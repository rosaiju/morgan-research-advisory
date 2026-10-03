"""Start/stop one llama-server process with the frozen configuration and parse its load log.

Offload is measured from the server's own buffer report: GPU fraction of weights =
CUDA0 model buffer / (all model buffers), plus the "offloaded X/Y layers" line and the KV-cache size.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "config_local.json").read_text(encoding="utf-8"))
PINS = json.loads((HERE / "gguf_pins.json").read_text(encoding="utf-8"))
MODEL_DIR = Path(os.environ.get("MORGAN_MODEL_DIR", r"C:\llm\models"))
BIN = Path(CONFIG["backend"]["install_dir"]) / "llama-server.exe"
PORT = int(os.environ.get("MORGAN_LLAMA_PORT", "8181"))

_MIB = r"([0-9]+(?:\.[0-9]+)?) MiB"


@dataclass
class LoadInfo:
    load_seconds: float | None = None
    gpu_model_mib: float = 0.0
    cpu_model_mib: float = 0.0
    kv_mib: float | None = None
    compute_gpu_mib: float | None = None
    layers_offloaded: str | None = None
    n_ctx: int | None = None
    fit_lines: list[str] = field(default_factory=list)

    @property
    def gpu_weight_fraction(self) -> float | None:
        total = self.gpu_model_mib + self.cpu_model_mib
        return round(self.gpu_model_mib / total, 4) if total else None


def parse_log(text: str) -> LoadInfo:
    info = LoadInfo()
    for line in text.splitlines():
        m = re.search(r"(CUDA\d+) model buffer size =\s*" + _MIB, line)
        if m:
            info.gpu_model_mib += float(m.group(2))
            continue
        m = re.search(r"(CPU(?:_Mapped|_REPACK)?|CUDA_Host) model buffer size =\s*" + _MIB, line)
        if m:
            info.cpu_model_mib += float(m.group(2))
            continue
        m = re.search(r"offloaded (\d+/\d+) layers to GPU", line)
        if m:
            info.layers_offloaded = m.group(1)
        m = re.search(r"(?:llama_kv_cache|llama_kv_cache_iswa|llama_memory_recurrent):\s+size =\s*" + _MIB, line)
        if m:
            info.kv_mib = (info.kv_mib or 0.0) + float(m.group(1))
        m = re.search(r"CUDA0 compute buffer size =\s*" + _MIB, line)
        if m:
            info.compute_gpu_mib = float(m.group(1))
        m = re.search(r"n_ctx\s*=\s*(\d+)", line)
        if m and info.n_ctx is None:
            info.n_ctx = int(m.group(1))
        if "common_params_fit_impl" in line or "common_fit_params" in line:
            info.fit_lines.append(line.split(" I ", 1)[-1].strip())
    return info


class Server:
    def __init__(self, model_key: str, n_ctx: int, log_path: Path, threads: int | None = None,
                 extra_args: list[str] | None = None, reasoning_budget: int | None = None,
                 budget_message: str | None = None):
        self.key = model_key
        self.n_ctx = n_ctx
        self.log_path = log_path
        self.threads = threads if threads is not None else CONFIG["backend"]["threads"]
        self.extra = extra_args or []
        self.reasoning_budget, self.budget_message = reasoning_budget, budget_message
        self.proc: subprocess.Popen | None = None
        self.info: LoadInfo | None = None

    @property
    def base(self) -> str:
        return f"http://127.0.0.1:{PORT}"

    def args(self) -> list[str]:
        m = CONFIG["models"][self.key]
        a = [str(BIN), "-m", str(MODEL_DIR / PINS[self.key]["file"]),
             "--chat-template-file", str(HERE / m["template_file"]),
             "-c", str(self.n_ctx), "--port", str(PORT), *CONFIG["backend"]["common_server_args"]]
        if self.threads:
            a += ["-t", str(self.threads)]
        if self.reasoning_budget is not None:
            i = a.index("--reasoning-budget")
            a[i + 1] = str(self.reasoning_budget)
            if self.budget_message:
                a += ["--reasoning-budget-message", self.budget_message]
        return a + self.extra

    def start(self, timeout_s: float = 900) -> LoadInfo:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        log = self.log_path.open("w", encoding="utf-8", errors="replace")
        t0 = time.perf_counter()
        self.proc = subprocess.Popen(self.args(), stdout=log, stderr=subprocess.STDOUT,
                                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        while True:
            if self.proc.poll() is not None:
                log.close()
                raise RuntimeError(f"llama-server exited with {self.proc.returncode} during load; see {self.log_path}")
            try:
                with urllib.request.urlopen(self.base + "/health", timeout=5) as r:
                    if r.status == 200 and json.load(r).get("status") == "ok":
                        break
            except (urllib.error.URLError, ConnectionError, TimeoutError, json.JSONDecodeError):
                pass
            if time.perf_counter() - t0 > timeout_s:
                self.stop()
                raise TimeoutError(f"llama-server not ready after {timeout_s}s")
            time.sleep(0.5)
        load_s = time.perf_counter() - t0
        log.flush()
        self.info = parse_log(self.log_path.read_text(encoding="utf-8", errors="replace"))
        self.info.load_seconds = round(load_s, 2)
        return self.info

    def pid(self) -> int | None:
        return self.proc.pid if self.proc else None

    def post(self, path: str, body: dict, timeout: float = 120) -> dict:
        req = urllib.request.Request(self.base + path, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)

    def get(self, path: str, timeout: float = 30) -> dict:
        with urllib.request.urlopen(self.base + path, timeout=timeout) as r:
            return json.load(r)

    def apply_template(self, messages: list[dict], kwargs: dict) -> str:
        return self.post("/apply-template", {"messages": messages, "chat_template_kwargs": kwargs})["prompt"]

    def tokenize(self, text: str) -> list[int]:
        return self.post("/tokenize", {"content": text, "add_special": False, "parse_special": True})["tokens"]

    def stop(self) -> None:
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=30)
        self.proc = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()

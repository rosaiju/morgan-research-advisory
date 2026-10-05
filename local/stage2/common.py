"""Stage 2 host setup shared by probe_stage2.py, run_stage2.py and preflight_stage2.py.

The Stage 1 harness modules (llm_server, client, telemetry, placement, run_local) are reused UNCHANGED. Host-specific
values are applied at runtime only:
  MORGAN_HOST        local-rtx4060 (default) | morgan-gpu        -> config_stage2.json hosts.<host>
  MORGAN_LLAMA_DIR   directory containing llama-server(.exe) and llama-fit-params(.exe)  (overrides the host entry)
  MORGAN_MODEL_DIR   directory containing the pinned GGUF files                            (overrides the host entry)
  MORGAN_GPU_INDEX   nvidia-smi index of the GPU used for telemetry (default: host entry, else 0); for a multi-GPU
                     server also set CUDA_VISIBLE_DEVICES to the same single GPU
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCAL = HERE.parent
CONFIG2 = json.loads((HERE / "config_stage2.json").read_text(encoding="utf-8"))
HOST = os.environ.get("MORGAN_HOST", "local-rtx4060")
if HOST not in CONFIG2["hosts"]:
    raise SystemExit(f"unknown MORGAN_HOST {HOST!r}; expected one of {sorted(CONFIG2['hosts'])}")
H = CONFIG2["hosts"][HOST]
LLAMA_DIR = Path(os.environ.get("MORGAN_LLAMA_DIR") or H["llama_dir"])
os.environ.setdefault("MORGAN_MODEL_DIR", H["model_dir"])          # read by llm_server at import
GPU_INDEX = int(os.environ.get("MORGAN_GPU_INDEX", H.get("gpu_index") or 0))
EXE = ".exe" if os.name == "nt" else ""
RUNS = LOCAL / "runs"
PROBE_DIR = RUNS / f"stage2-probe-{HOST}"
RUN_DIR = RUNS / f"stage2-{HOST}"
sys.path.insert(0, str(LOCAL))

import llm_server  # noqa: E402
import placement  # noqa: E402
import telemetry  # noqa: E402

llm_server.BIN = LLAMA_DIR / f"llama-server{EXE}"

RENDERED2 = json.loads((HERE / "items/stage2_rendered.json").read_text(encoding="utf-8"))
PANEL2 = json.loads((HERE / "items/stage2_panel.json").read_text(encoding="utf-8"))
PROBE_ITEMS = [p["item_id"] for p in json.loads((HERE / "items/stage2_probe_items.json").read_text(encoding="utf-8"))]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def server_threads() -> int | None:
    return H.get("threads") if H.get("threads") is not None else llm_server.CONFIG["backend"]["threads"]


def _projected(model_path: Path, n_ctx: int, k: int, ngl: int = 999) -> tuple[int, int]:
    """placement.projected with a host-specific llama-fit-params path (same arguments and parsing)."""
    exe = LLAMA_DIR / f"llama-fit-params{EXE}"
    args = [str(exe), "-m", str(model_path), "-c", str(n_ctx), "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0",
            "-ngl", str(ngl), "-fitt", str(placement.MARGIN_MIB), "-lv", "4"]
    if k:
        args += ["-ot", placement.ffn_override(k)]
    out = ""
    for _ in range(3):
        p = subprocess.run(args, capture_output=True, text=True, timeout=300)
        out = p.stdout + p.stderr
        m = re.search(r"projected to use (\d+) MiB of device memory vs\. (\d+) MiB of free device memory", out)
        if m:
            return int(m.group(1)), int(m.group(2))
        b = re.search(r"CUDA0 \([^)]*\)\s*\|\s*\d+\s*=\s*(\d+)\s*\+\s*\(\s*(\d+)\s*=", out)
        if b:
            return int(b.group(2)), int(b.group(1))
    raise RuntimeError(f"llama-fit-params gave no projection for k={k}, ngl={ngl}:\n{out[-2000:]}")


placement.projected = _projected
_QUERY = telemetry.QUERY


def _gpu_snapshot() -> dict:
    """telemetry.gpu_snapshot for one selected GPU (nvidia-smi -i), so multi-GPU servers report the GPU in use."""
    out = subprocess.run(["nvidia-smi", "-i", str(GPU_INDEX), f"--query-gpu={_QUERY}", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True, timeout=15).stdout.strip().splitlines()[0]
    f = [x.strip() for x in out.split(",")]

    def num(x):
        try:
            return float(x)
        except ValueError:
            return None
    return {"gpu_mem_used_mib": num(f[0]), "gpu_mem_total_mib": num(f[1]), "gpu_util_pct": num(f[2]),
            "gpu_temp_c": num(f[3]), "gpu_sm_clock_mhz": num(f[4]), "gpu_power_w": num(f[5]),
            "gpu_throttle_reasons": f[6]}


telemetry.gpu_snapshot = _gpu_snapshot


def host_info() -> dict:
    """Facts about the machine, recorded in every probe and run (needed to reproduce and to interpret speeds)."""
    import platform

    import psutil
    info = {"host": HOST, "platform": platform.platform(), "python": platform.python_version(),
            "cpu": platform.processor(), "cpu_logical": psutil.cpu_count(), "cpu_physical": psutil.cpu_count(False),
            "ram_gb": round(psutil.virtual_memory().total / 2**30, 1), "llama_dir": str(LLAMA_DIR),
            "model_dir": os.environ["MORGAN_MODEL_DIR"], "gpu_index": GPU_INDEX,
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES")}
    try:
        q = "name,memory.total,driver_version,vbios_version,pcie.link.gen.max"
        info["gpu"] = subprocess.run(["nvidia-smi", "-i", str(GPU_INDEX), f"--query-gpu={q}", "--format=csv,noheader"],
                                     capture_output=True, text=True, timeout=15).stdout.strip()
        smi = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=15).stdout
        m = re.search(r"CUDA Version: ([0-9.]+)", smi)
        info["driver_cuda"] = m.group(1) if m else None
    except Exception as e:  # noqa: BLE001
        info["gpu_error"] = repr(e)
    try:
        info["llama_server_version"] = subprocess.run([str(llm_server.BIN), "--version"], capture_output=True,
                                                      text=True, timeout=60).stderr.strip().splitlines()[-2:]
    except Exception as e:  # noqa: BLE001
        info["llama_server_version_error"] = repr(e)
    return info


def weights_ok(model: str, full_hash: bool = False) -> tuple[bool, str]:
    pin = llm_server.PINS[model]
    f = Path(os.environ["MORGAN_MODEL_DIR"]) / pin["file"]
    if not f.exists() or f.stat().st_size != pin["size"]:
        return False, f"missing or wrong size: {f}"
    side = f.with_suffix(".gguf.sha256")
    if not full_hash and side.exists() and side.read_text().strip() == pin["sha256"]:
        return True, "sidecar"
    h = hashlib.sha256()
    with f.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 24), b""):
            h.update(chunk)
    ok = h.hexdigest() == pin["sha256"]
    if ok and not side.exists():
        side.write_text(pin["sha256"] + "\n")
    return ok, "full re-hash"

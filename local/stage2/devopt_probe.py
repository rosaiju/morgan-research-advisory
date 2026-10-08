"""DEVELOPMENT-ONLY execution-speed probe for the dense finalists on THIS host (not Stage 2; no Stage 2 item is used).

    MORGAN_HOST=local-rtx4060 python local/stage2/devopt_probe.py bench <model> <config> [<config> ...]
    MORGAN_HOST=local-rtx4060 python local/stage2/devopt_probe.py server <model> <config> [<config> ...]
    MORGAN_HOST=local-rtx4060 python local/stage2/devopt_probe.py placement <model> <margin_mib>

Only execution settings vary (CPU threads / pinning / priority, GPU layer count, VRAM margin). Never varied: GGUF
(Q4_K_M), q8_0 K/V cache, flash attention on, no mmap, n_ctx, reasoning budget 16,384, answer allowance 2,048,
template, sampling, seeds, prompts.

bench  : llama-bench on synthetic tokens (no study item): tg64 at depth 0 and 16,384 (2 repetitions), with resource
         sampling (RAM, VRAM, CPU %, CPU performance %, GPU throttle reasons).
server : the real llama-server path at the Stage 2 n_ctx with the frozen common arguments: load, fresh pp512/tg128,
         tg128 after 8K and 16K tokens, and the development item ifeval/1012 (stage2_probe_items.json; excluded from
         the Stage 2 panel) at the Stage 2 budget, recording prompt hash, seed and payload hash.
Outputs: local/runs/stage2-devopt-<host>/ (results_<model>.jsonl, logs).
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

import psutil  # noqa: E402

import placement  # noqa: E402
import run_local as R  # noqa: E402
from llm_server import MODEL_DIR, PINS, Server  # noqa: E402
from probe_local import depth_probe, fresh_probe  # noqa: E402

OUT = C.RUNS / f"stage2-devopt-{C.HOST}"
DEV_ITEM = "ifeval/1012"
MARK = "Time is up. I must stop thinking now"
REASONING_MARKERS = ("<think>", "</think>", "[THINK]", "[/THINK]", "<|channel|>", "<|start|>", "<|message|>",
                     "<|channel>", "<channel|>")
P_CORE_ONE_THREAD_EACH = "0x5555"  # logical CPUs 0,2,..,14 = one hardware thread on each of the 8 P-cores


def frozen_probe(model: str) -> dict:
    return json.loads((C.PROBE_DIR / f"probe_{model}.json").read_text(encoding="utf-8"))


def ffn_all(model: str) -> str:
    return placement.ffn_override(placement.N_LAYERS[model])


def configs(model: str) -> dict[str, dict]:
    """name -> {'ngl', 'ffn_cpu' (bool), 'threads', 'extra' (server/bench flags)}; baseline = frozen probe placement."""
    p = frozen_probe(model)["placement"]
    ngl0 = p["ngl"]
    base = {"ngl": ngl0, "ffn_cpu": True, "threads": 8, "extra": []}
    c = {"baseline": base}
    for t in (6, 12, 16, 20):
        c[f"t{t}"] = base | {"threads": t}
    c["t8_pcore_strict"] = base | {"extra": ["-C", P_CORE_ONE_THREAD_EACH, "--cpu-strict", "1"]}
    c["t8_prio2"] = base | {"extra": ["--prio", "2"]}
    extra_ngl = json.loads((OUT / f"placement_{model}.json").read_text()) if (OUT / f"placement_{model}.json").exists() else {}
    for name, ngl in extra_ngl.items():
        c[f"ngl{ngl}_{name}"] = base | {"ngl": ngl}
        c[f"t16_ngl{ngl}_{name}"] = base | {"ngl": ngl, "threads": 16}
    return c


def sampler(stop: threading.Event, pid_name: str, out: dict) -> None:
    peaks = {"sys_used_mib": 0, "proc_rss_mib": 0, "gpu_mem_used_mib": 0, "gpu_temp_c": 0}
    cpu, perf, throttle = [], [], set()
    psutil.cpu_percent(None)
    k = 0
    while not stop.is_set():
        vm = psutil.virtual_memory()
        peaks["sys_used_mib"] = max(peaks["sys_used_mib"], (vm.total - vm.available) / 2**20)
        for pr in psutil.process_iter(["name", "memory_info"]):
            if pid_name in (pr.info["name"] or "") and pr.info["memory_info"]:
                peaks["proc_rss_mib"] = max(peaks["proc_rss_mib"], pr.info["memory_info"].rss / 2**20)
        try:
            g = C.telemetry.gpu_snapshot()
            peaks["gpu_mem_used_mib"] = max(peaks["gpu_mem_used_mib"], g["gpu_mem_used_mib"] or 0)
            peaks["gpu_temp_c"] = max(peaks["gpu_temp_c"], g["gpu_temp_c"] or 0)
            if g["gpu_throttle_reasons"] not in (None, "0x0000000000000000", "0x0000000000000001"):
                throttle.add(g["gpu_throttle_reasons"])  # 0x1 = GPU idle, not a throttle
        except Exception:  # noqa: BLE001
            pass
        c = psutil.cpu_percent(None)
        if c:
            cpu.append(c)
        if k % 5 == 0:  # Windows: % Processor Performance falls below base when the CPU is thermally/power limited
            try:
                t = subprocess.run(["typeperf", r"\Processor Information(_Total)\% Processor Performance", "-sc", "1"],
                                   capture_output=True, text=True, timeout=10).stdout.strip().splitlines()
                rows = [x for x in t if x.startswith('"')]
                perf.append(float(rows[1].split(",")[1].strip('"')))
            except Exception:  # noqa: BLE001
                pass
        k += 1
        stop.wait(1.0)
    out.update(peaks={k: round(v, 1) for k, v in peaks.items()}, gpu_throttle_reasons=sorted(throttle),
               cpu_pct_mean=round(sum(cpu) / len(cpu), 1) if cpu else None, cpu_pct_max=max(cpu) if cpu else None,
               cpu_perf_pct_min=min(perf) if perf else None, cpu_perf_pct_median=sorted(perf)[len(perf) // 2] if perf else None)


def with_sampling(fn, pid_name: str):
    stop, out = threading.Event(), {}
    th = threading.Thread(target=sampler, args=(stop, pid_name, out), daemon=True)
    th.start()
    try:
        res = fn()
    finally:
        stop.set()
        th.join(30)
    return res, out


def bench(model: str, names: list[str]) -> None:
    cfg = configs(model)
    exe = C.LLAMA_DIR / f"llama-bench{C.EXE}"
    for name in names:
        c = cfg[name]
        args = [str(exe), "-m", str(MODEL_DIR / PINS[model]["file"]), "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0",
                "-lm", "none", "-ngl", str(c["ngl"]), "-t", str(c["threads"]), "-p", "0", "-n", "64",
                "-d", "0,16384", "-r", "2", "-o", "jsonl", *c["extra"]]
        if c["ffn_cpu"]:
            args += ["-ot", ffn_all(model)]
        t0 = time.time()
        p, res = with_sampling(lambda: subprocess.run(args, capture_output=True, text=True, timeout=7200), "llama-bench")
        rows = [json.loads(l) for l in p.stdout.splitlines() if l.startswith("{")]
        rec = {"phase": "bench", "model": model, "config": name, "settings": c, "returncode": p.returncode,
               "wall_s": round(time.time() - t0, 1),
               "tg64": {str(r["n_depth"]): {"avg_ts": round(r["avg_ts"], 3), "stddev_ts": round(r["stddev_ts"], 3)}
                        for r in rows},
               "resources": res, "stderr_tail": p.stderr[-800:] if p.returncode else ""}
        (OUT / f"bench_{model}_{name}.log").write_text(p.stdout + "\n" + p.stderr, encoding="utf-8")
        with (OUT / f"results_{model}.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print(json.dumps({k: rec[k] for k in ("config", "returncode", "wall_s", "tg64")} | {"res": res}), flush=True)


def server(model: str, names: list[str]) -> None:
    cfg = configs(model)
    n_ctx = frozen_probe(model)["n_ctx"]
    s2 = C.CONFIG2
    text = C.RENDERED2[DEV_ITEM]["text"]
    for name in names:
        c = cfg[name]
        pargs = ["-ngl", str(c["ngl"])] + (["-ot", ffn_all(model)] if c["ffn_cpu"] else []) + c["extra"]
        srv = Server(model, n_ctx, OUT / f"server_{model}_{name}.log", threads=c["threads"], extra_args=pargs,
                     reasoning_budget=s2["thinking_budget"], budget_message=s2["budget_message"])
        rec = {"phase": "server", "model": model, "config": name, "settings": c, "n_ctx": n_ctx, "args": pargs}

        def go():
            li = srv.start()
            rec["load"] = {"load_seconds": li.load_seconds, "layers_offloaded": li.layers_offloaded,
                           "gpu_model_mib": li.gpu_model_mib, "cpu_model_mib": li.cpu_model_mib, "kv_mib": li.kv_mib,
                           "n_ctx_reported": li.n_ctx}
            rec["fresh"] = fresh_probe(srv)
            rec["deep_8k"] = depth_probe(srv, 8192)
            rec["deep_16k"] = depth_probe(srv, 16384)
            r = R.run_attempt(srv, model, DEV_ITEM, text, s2["max_tokens"], 12 * 3600, "stage2-devopt",
                              answer_cap=s2["answer_allowance"])
            fin = r["final_text"] or ""
            rec["dev_item"] = {k: r.get(k) for k in ("item_id", "seed", "prompt_sha256", "payload_sha256", "max_tokens",
                                                     "reasoning_budget", "finish_reason", "abort", "error",
                                                     "completion_tokens", "reasoning_tokens", "final_tokens", "wall_s",
                                                     "client_gen_tok_s", "server_gen_tok_s")}
            rec["dev_item"].update(final_nonempty=bool(fin.strip()), forced=MARK in (r["reasoning_text"] or ""),
                                   reasoning_markers_in_final=any(m in fin for m in REASONING_MARKERS))
            R.wait_idle(srv)

        try:
            _, res = with_sampling(go, "llama-server")
            rec["resources"] = res
        except Exception as e:  # noqa: BLE001  an unstable configuration is a result, not a crash of the probe
            rec["error"] = repr(e)[:500]
        finally:
            srv.stop()
        with (OUT / f"results_{model}.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print(json.dumps({k: rec.get(k) for k in ("config", "load", "fresh", "deep_8k", "deep_16k", "dev_item", "resources", "error")}),
              flush=True)
        time.sleep(10)


def placement_search(model: str, margin: int) -> None:
    """Step 2 of the approved rule (all FFN on CPU, largest ngl that leaves `margin` MiB free) at today's free VRAM."""
    n_ctx = frozen_probe(model)["n_ctx"]
    path = MODEL_DIR / PINS[model]["file"]
    n = placement.N_LAYERS[model]
    lo, hi, tr = 0, n, {}
    free = None
    while hi - lo > 1:
        mid = (lo + hi) // 2
        u, free = C._projected(path, n_ctx, n, ngl=mid)
        tr[mid] = u
        if u <= free - margin:
            lo = mid
        else:
            hi = mid
    f = OUT / f"placement_{model}.json"
    d = json.loads(f.read_text()) if f.exists() else {}
    d[f"margin{margin}"] = lo
    f.write_text(json.dumps(d, indent=1))
    print(json.dumps({"model": model, "margin": margin, "ngl": lo, "free_mib": free, "trace": dict(sorted(tr.items()))}), flush=True)


if __name__ == "__main__":
    mode, model, *rest = sys.argv[1:]
    if model not in ("qwen3.8-27b", "gemma-4-31b"):
        raise SystemExit("dense finalists only")
    OUT.mkdir(parents=True, exist_ok=True)
    lock = C.llm_server.acquire_runner_lock(f"stage2 devopt {C.HOST}")
    C.llm_server.keep_awake(True)
    try:
        if mode == "bench":
            bench(model, rest)
        elif mode == "server":
            server(model, rest)
        elif mode == "placement":
            placement_search(model, int(rest[0]))
    finally:
        C.llm_server.keep_awake(False)
        C.llm_server.release_runner_lock(lock)

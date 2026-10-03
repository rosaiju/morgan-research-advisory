"""Approved placement rule (2026-10-02): attention layers and the KV cache stay on the GPU; when VRAM runs out,
feed-forward (dense) or expert (MoE) weights move to the CPU first, with the same 1 GiB free-VRAM margin.

- MoE models (gpt-oss, GLM): llama.cpp --fit already implements exactly this (all layers on GPU, expert tensors of
  the first layers overflow to system memory), so no extra arguments are added.
- Dense models: -ngl 999 plus --override-tensor sending the feed-forward tensors (ffn_up/ffn_gate/ffn_down) of the
  first K layers to the CPU, with K the smallest value whose projected device use (llama-fit-params, no weight load)
  leaves >= 1024 MiB free. This mirrors --fit's front-to-back expert overflow for MoE models.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "config_local.json").read_text(encoding="utf-8"))
MOE = {"gpt-oss-20b", "glm-4.7-flash"}
N_LAYERS = {"r1-0528-qwen3-8b": 36, "ministral-3-14b-reasoning": 40, "muse-glimmer-30b": 52,
            "qwen3.8-27b": 64, "gemma-4-31b": 60}
MARGIN_MIB = 1024


def ffn_override(k: int) -> str:
    layers = "|".join(str(i) for i in range(k))
    return rf"blk\.({layers})\.ffn_(up|down|gate).*=CPU"


def projected(model_path: Path, n_ctx: int, k: int, ngl: int = 999) -> tuple[int, int]:
    """(projected device MiB, free device MiB) for K overflowing FFN layers and ngl GPU layers, from llama-fit-params
    (no weight load)."""
    exe = Path(CONFIG["backend"]["install_dir"]) / "llama-fit-params.exe"
    args = [str(exe), "-m", str(model_path), "-c", str(n_ctx), "-fa", "on", "-ctk", "q8_0", "-ctv", "q8_0",
            "-ngl", str(ngl), "-fitt", str(MARGIN_MIB), "-lv", "4"]
    if k:
        args += ["-ot", ffn_override(k)]
    out = ""
    for _ in range(3):  # the summary line is occasionally missing from the captured output; retry, then fall back
        p = subprocess.run(args, capture_output=True, text=True, timeout=300)
        out = p.stdout + p.stderr
        m = re.search(r"projected to use (\d+) MiB of device memory vs\. (\d+) MiB of free device memory", out)
        if m:
            return int(m.group(1)), int(m.group(2))
        # memory breakdown line: "CUDA0 (RTX 4060) | total = free + (self = model + context + compute) + unaccounted"
        b = re.search(r"CUDA0 \([^)]*\)\s*\|\s*\d+\s*=\s*(\d+)\s*\+\s*\(\s*(\d+)\s*=", out)
        if b:
            return int(b.group(2)), int(b.group(1))
    raise RuntimeError(f"llama-fit-params gave no projection for k={k}, ngl={ngl}:\n{out[-2000:]}")


def placement_args(model: str, model_path: Path, n_ctx: int) -> tuple[list[str], dict]:
    if model in MOE:
        return [], {"rule": "moe: --fit expert overflow (attention + KV on GPU)"}
    n = N_LAYERS[model]
    lo, hi, trace = 0, n, {}
    used, free = projected(model_path, n_ctx, 0)
    trace[0] = used
    if used <= free - MARGIN_MIB:
        return ["-ngl", "999"], {"rule": "dense: everything fits on GPU", "k_ffn_cpu": 0, "projected_mib": used, "free_mib": free}
    used_all, _ = projected(model_path, n_ctx, n)
    trace[n] = used_all
    if used_all > free - MARGIN_MIB:
        # Rule step 2: all FFN weights already on CPU and attention + KV still do not fit -> move whole layers too
        # (largest GPU layer count that fits; llama.cpp's --fit refuses to run when tensor overrides are set).
        # Recorded as a per-model deviation from "all attention on GPU".
        lo_n, hi_n, tr2 = 0, n, {}
        while hi_n - lo_n > 1:  # largest ngl with used <= free - margin
            mid = (lo_n + hi_n) // 2
            u, free = projected(model_path, n_ctx, n, ngl=mid)
            tr2[mid] = u
            if u <= free - MARGIN_MIB:
                lo_n = mid
            else:
                hi_n = mid
        return ["-ngl", str(lo_n), "-ot", ffn_override(n)], {
            "rule": "dense, step 2: ALL FFN on CPU and attention+KV still too large -> whole layers moved to CPU",
            "k_ffn_cpu": n, "n_layers": n, "ngl": lo_n, "attention_all_on_gpu": False,
            "projected_mib_all_ffn_cpu": used_all, "projected_mib": tr2.get(lo_n), "free_mib": free,
            "search_trace_ngl": dict(sorted(tr2.items()))}
    while hi - lo > 1:  # smallest k with used <= free - margin
        mid = (lo + hi) // 2
        u, free = projected(model_path, n_ctx, mid)
        trace[mid] = u
        if u <= free - MARGIN_MIB:
            hi = mid
        else:
            lo = mid
    return ["-ngl", "999", "-ot", ffn_override(hi)], {
        "rule": "dense: all layers on GPU, FFN of first K layers on CPU", "k_ffn_cpu": hi, "n_layers": n,
        "projected_mib": trace[hi], "free_mib": free, "search_trace": dict(sorted(trace.items()))}

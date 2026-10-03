"""Offline what-if analysis on completed calibration data (no inference).

For each calibrated model and a common thinking budget B (with forced conclusion and an answer allowance), estimate
the tokens and seconds each development attempt would have used, from the model's own measured decode-vs-depth curve
(llama-server 3 s timings) and measured prompt rate. Also reports the measured slowdown components.

    python local/budget_scenarios.py local/runs/calibration-20261002
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analyze_calibration as A  # noqa: E402

MODELS = ["r1-0528-qwen3-8b", "gpt-oss-20b", "glm-4.7-flash", "ministral-3-14b-reasoning"]
BUDGETS = [4096, 6144, 8192, 12288, 24576]


def main(run_dir: Path) -> None:
    out = {}
    for m in MODELS:
        if not (run_dir / f"model_{m}.json").exists():
            continue
        s = json.loads((run_dir / f"model_{m}.json").read_text(encoding="utf-8"))
        rs = A.final_attempts(run_dir, m)
        curve = A.speed_curve(run_dir, m)
        finals = [r["final_tokens"] for r in rs if r["finish_reason"] == "stop" and r.get("final_tokens")]
        answer = min(statistics.median(finals) if finals else 400, 2048)
        prompt_rates = [r["server_prompt_tok_s"] for r in rs if r.get("server_prompt_tok_s")]
        prefill = statistics.median(prompt_rates) if prompt_rates else s["speed_probe"]["pp512_tok_s_median"]

        def at(depth):
            return round(curve[min(depth // A.BUCKET, len(curve) - 1)], 2) if curve else None

        row = {"layers_offloaded": s["loads"][-1]["layers_offloaded"], "gpu_weight_fraction": s["loads"][-1]["gpu_weight_fraction"],
               "kv_mib": s["loads"][-1]["kv_mib"], "tok_s_at_depth": {d: at(d) for d in (0, 4096, 8192, 12288, 16384, 20480)},
               "natural_tokens": [r["completion_tokens"] for r in rs], "finish": [r["finish_reason"] for r in rs],
               "median_answer_tokens": answer, "scenarios": {}}
        for B in BUDGETS:
            per = []
            for r in rs:
                n = r["completion_tokens"] or 0
                forced = n > B or r["finish_reason"] != "stop"
                tok = (B + answer) if forced else n
                sec = A.gen_seconds(tok, curve, 10.0) + (r["prompt_tokens"] or 0) / prefill
                per.append({"item": r["item_id"], "benchmark": r["benchmark"], "tokens": tok, "forced": forced, "seconds": round(sec)})
            row["scenarios"][B] = {"per_item": per, "forced_share": round(sum(p["forced"] for p in per) / len(per), 2),
                                   "mean_seconds_capability": round(statistics.mean(p["seconds"] for p in per if p["benchmark"] != "ifeval")),
                                   "ifeval_seconds": next((p["seconds"] for p in per if p["benchmark"] == "ifeval"), None)}
        out[m] = row
    (run_dir / "budget_scenarios.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for m, r in out.items():
        print(m, r["layers_offloaded"], r["gpu_weight_fraction"], "tok/s by depth", r["tok_s_at_depth"])
        for B, sc in r["scenarios"].items():
            print(f"   B={B:6d} forced {sc['forced_share']:.2f}  mean capability item {sc['mean_seconds_capability']/60:6.1f} min  "
                  f"ifeval {sc['ifeval_seconds']} s")


if __name__ == "__main__":
    main(Path(sys.argv[1]))

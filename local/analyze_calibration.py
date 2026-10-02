"""Apply the pre-registered C1 rule to calibration attempts and project the Stage 1 runtime.

    python local/analyze_calibration.py local/runs/<calibration run>

C1 rule (config_local.json calibration.rule): C1 = smallest L in the ladder such that
  (a) no model has more than 1 development attempt that ended naturally (finish_reason == "stop")
      with completion_tokens > L, and
  (b) at most 2 such attempts across all models.
Loop-terminated and C_dev-truncated attempts are censored at every L and do not count.
Accuracy, runtime and model identity are NOT inputs to the rule.

Projection (per model, from that model's own calibration measurements):
  tokens per Stage 1 item  = measured mean completion tokens for the same benchmark, each attempt capped at C1
                             (MATH dev items are L3-L5 and the panel spans L1-L5, so MATH is conservative;
                              the student suite has no development items and uses the model's MMLU-Pro mean)
  generation time          = tokens / measured decode rate (completion tokens / generation seconds, at depth)
  prompt time              = Stage 1 prompt tokens / measured median prompt rate
  + 3 s per item overhead + one model load
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "config_local.json").read_text(encoding="utf-8"))
PANEL = json.loads((HERE / "items/stage1_panel.json").read_text(encoding="utf-8"))
ORDER = ["r1-0528-qwen3-8b", "gpt-oss-20b", "glm-4.7-flash", "ministral-3-14b-reasoning",
         "muse-glimmer-30b", "qwen3.8-27b", "gemma-4-31b"]


def final_attempts(run_dir: Path, model: str) -> list[dict]:
    """Last attempt per item (an infrastructure rerun supersedes the failed attempt)."""
    by_item = {}
    p = run_dir / f"attempts_{model}.jsonl"
    for line in p.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("kind") == "item" and r.get("stage") == "calibration":
            by_item[r["item_id"]] = r
    return list(by_item.values())


def choose_c1(attempts: dict[str, list[dict]]) -> tuple[int, dict]:
    ladder = CONFIG["calibration"]["ladder"]
    table = {}
    for L in ladder:
        per_model = {m: sum(1 for r in rs if r["finish_reason"] == "stop" and not r["abort"]
                            and (r["completion_tokens"] or 0) > L) for m, rs in attempts.items()}
        table[L] = {"per_model": per_model, "total": sum(per_model.values()),
                    "passes": max(per_model.values()) <= 1 and sum(per_model.values()) <= 2}
    chosen = next((L for L in ladder if table[L]["passes"]), ladder[-1])
    return chosen, table


def project(run_dir: Path, model: str, rs: list[dict], c1: int, summary: dict) -> dict:
    natural = [r for r in rs if not r["error"]]
    gen_tok = sum(r["completion_tokens"] or 0 for r in natural)
    gen_s = sum((r["wall_s"] - r["ttft_s"]) for r in natural if r["ttft_s"] is not None)
    decode = gen_tok / gen_s if gen_s else None
    prompt_rates = [r["server_prompt_tok_s"] for r in natural if r.get("server_prompt_tok_s")]
    prefill = statistics.median(prompt_rates) if prompt_rates else summary["speed_probe"]["pp512_tok_s_median"]
    per_bench = defaultdict(list)
    for r in natural:
        per_bench[r["benchmark"]].append(min(r["completion_tokens"] or 0, c1))
    mean = {b: statistics.mean(v) for b, v in per_bench.items()}
    mean["student"] = mean.get("mmlu_pro")
    plen = summary["prompt_tokens"]["per_item"]
    out = {}
    for block in ("core", "reserve"):
        items = [p for p in PANEL if p["block"] == block]
        toks = sum(mean[p["benchmark"]] for p in items)
        ptoks = sum(plen[p["item_id"]] for p in items)
        hours = (toks / decode + ptoks / prefill + 3 * len(items)) / 3600
        out[block] = {"items": len(items), "gen_tokens": round(toks), "prompt_tokens": ptoks, "hours": round(hours, 2)}
    load_h = statistics.median(l["load_seconds"] for l in summary["loads"]) / 3600
    out["load_hours"] = round(load_h, 3)
    out["decode_tok_s_at_depth"] = round(decode, 2) if decode else None
    out["prefill_tok_s"] = round(prefill, 1)
    out["mean_tokens_by_benchmark_capped_at_C1"] = {b: round(v) for b, v in mean.items() if v is not None}
    return out


def main(run_dir: Path) -> None:
    models = [m for m in ORDER if (run_dir / f"model_{m}.json").exists()]
    attempts = {m: final_attempts(run_dir, m) for m in models}
    summaries = {m: json.loads((run_dir / f"model_{m}.json").read_text(encoding="utf-8")) for m in models}
    c1, table = choose_c1(attempts)
    report = {"run": run_dir.name, "models": models, "complete": len(models) == 7,
              "C1": c1, "c1_table": table, "per_model": {}}
    total_core = total_full = 0.0
    for m in models:
        rs, s = attempts[m], summaries[m]
        proj = project(run_dir, m, rs, c1, s)
        load3 = s["loads"][-1]
        report["per_model"][m] = {
            "integration_passed": s["integration"]["passed"],
            "template_fidelity": s["integration"]["template_fidelity"],
            "speed_probe": s["speed_probe"],
            "n_ctx_calibration": s["n_ctx_calibration"],
            "load_seconds": [l["load_seconds"] for l in s["loads"]],
            "layers_offloaded": load3["layers_offloaded"], "gpu_weight_fraction": load3["gpu_weight_fraction"],
            "gpu_model_mib": load3["gpu_model_mib"], "cpu_model_mib": load3["cpu_model_mib"], "kv_mib": load3["kv_mib"],
            "gpu_baseline_mib": s["gpu_baseline_mib"], "telemetry": s["telemetry"],
            "attempts": [{"item": r["item_id"], "finish": r["finish_reason"], "abort": r["abort"], "tokens": r["completion_tokens"],
                          "reasoning_tokens": r["reasoning_tokens"], "final_tokens": r["final_tokens"],
                          "gen_tok_s": r["client_gen_tok_s"], "wall_s": r["wall_s"], "attempt": r.get("attempt")} for r in rs],
            "projection": proj,
        }
        total_core += proj["core"]["hours"] + proj["load_hours"]
        total_full += proj["core"]["hours"] + proj["reserve"]["hours"] + 2 * proj["load_hours"]
    report["projection_total_hours"] = {"core": round(total_core, 1), "core_plus_reserve": round(total_full, 1)}
    (run_dir / "calibration_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "per_model"}, indent=1))
    for m in models:
        p = report["per_model"][m]
        print(f"{m:28s} decode {p['projection']['decode_tok_s_at_depth']} tok/s | probe tg {p['speed_probe']['tg256_tok_s_median']} | "
              f"GPU {p['gpu_weight_fraction']} ({p['layers_offloaded']}) | core {p['projection']['core']['hours']} h "
              f"+ reserve {p['projection']['reserve']['hours']} h")


if __name__ == "__main__":
    main(Path(sys.argv[1]))

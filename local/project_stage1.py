"""Project the Stage 1 v2 runtime from MEASURED probe speeds (approved placement + 6,144 + 1,536 budget).

    python local/project_stage1.py [probe run dir] [calibration run dir]

Per model:
  decode speed vs depth : linear between the probe's fresh tg and its tg after an ~8K-token context
                          (held flat beyond 8K; Stage 1 never exceeds ~9K generated + prompt)
  tokens per item       : from calibration development attempts, re-capped under the new budget
                          (reasoning > 6,144 -> 6,144 + message + the model's measured forced-answer length, else
                          natural reasoning + answer capped at 1,536). Models without calibration (dense) use the
                          pooled per-benchmark mean of the four calibrated models (assumption, flagged).
                          Student items use the MMLU-Pro value; MATH dev items are level 5 while the panel uses L2-L4
                          (both conservative).
  prompt time           : this model's v2 prompt token counts / measured prefill speed
  overhead              : 3 s per item + one measured model load
Writes <probe dir>/stage1_projection.json.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / "config_local.json").read_text(encoding="utf-8"))
S1 = CONFIG["stage1_v2"]
PANEL = json.loads((HERE / "items/stage1_panel_v2.json").read_text(encoding="utf-8"))
ORDER = ["r1-0528-qwen3-8b", "gpt-oss-20b", "glm-4.7-flash", "ministral-3-14b-reasoning",
         "muse-glimmer-30b", "qwen3.8-27b", "gemma-4-31b"]
MSG_TOK = 24


def gen_seconds(tokens: float, fresh: float, deep: float, depth_ref: int = 8192) -> float:
    t, step, done = 0.0, 256, 0
    while done < tokens:
        n = min(step, tokens - done)
        x = min((done + n / 2) / depth_ref, 1.0)
        t += n / (fresh + (deep - fresh) * x)
        done += n
    return t


def capped_tokens(att: dict, forced_answer: float) -> float:
    r = att.get("reasoning_tokens") or 0
    f = att.get("final_tokens") or 0
    if att.get("finish_reason") != "stop" or r > S1["thinking_budget"]:
        return S1["thinking_budget"] + MSG_TOK + forced_answer
    return r + min(f, S1["answer_allowance"])


def main(probe_dir: Path, cal_dir: Path, student_as: str = "mmlu_pro") -> None:
    per_bench_all = {}
    cal = {}
    for m in ORDER:
        p = cal_dir / f"attempts_{m}.jsonl"
        if p.exists():
            items = {}
            for line in p.read_text(encoding="utf-8").splitlines():
                r = json.loads(line)
                if r.get("kind") == "item" and r.get("stage") == "calibration":
                    items[r["item_id"]] = r
            cal[m] = list(items.values())
    out, total = {}, 0.0
    for m in ORDER:
        pf = probe_dir / f"probe_{m}.json"
        if not pf.exists():
            out[m] = {"status": "no probe result"}
            continue
        pr = json.loads(pf.read_text(encoding="utf-8"))
        if "speed_fresh" not in pr or "speed_deep" not in pr:
            out[m] = {"status": "probe incomplete", "error": pr.get("error")}
            continue
        fresh, deep = pr["speed_fresh"]["tg_fresh_tok_s"], pr["speed_deep"]["tg_tok_s_at_depth"]
        prefill = min(pr["speed_fresh"]["pp512_tok_s"], pr["speed_deep"]["prefill_tok_s"])
        fa = pr.get("forced_conclusion", {}).get("math500/test/geometry/880.json", {}).get("final_tokens") or 600
        fa = min(fa, S1["answer_allowance"])
        if m in cal:
            src = "own calibration attempts"
            per = {}
            for a in cal[m]:
                per.setdefault(a["benchmark"], []).append(capped_tokens(a, fa))
            per_bench = {b: statistics.mean(v) for b, v in per.items()}
            for b, v in per.items():
                per_bench_all.setdefault(b, []).extend(v)
        else:
            src = "ASSUMED: pooled calibrated-model token use (no long calibration for this model)"
            per_bench = None
        out[m] = {"fresh": fresh, "deep": deep, "prefill": prefill, "forced_answer_tokens": fa, "token_source": src,
                  "per_bench": per_bench, "pr": pr}
    pooled = {b: statistics.mean(v) for b, v in per_bench_all.items()}
    for m in ORDER:
        o = out[m]
        if "pr" not in o:
            continue
        pb = dict(o["per_bench"] or pooled)
        pb["student"] = pb.get(student_as)
        lens = o["pr"]["prompt_tokens_v2"]
        gen = sum(gen_seconds(pb[p["benchmark"]], o["fresh"], o["deep"]) for p in PANEL)
        pre = sum(lens[p["item_id"]] / o["prefill"] for p in PANEL)
        load = statistics.median(l["load_seconds"] for l in o["pr"]["loads"])
        hours = (gen + pre + 3 * len(PANEL) + load) / 3600
        o.update(tokens_per_bench={b: round(v) for b, v in pb.items()}, gen_tokens=round(sum(pb[p["benchmark"]] for p in PANEL)),
                 hours=round(hours, 2))
        del o["pr"], o["per_bench"]
        total += hours
    res = {"panel": "stage1_panel_v2 (22 items)", "budget": f"{S1['thinking_budget']} + {S1['answer_allowance']}",
           "student_items_costed_as": student_as,
           "per_model": out, "total_hours": round(total, 1)}
    name = "stage1_projection.json" if student_as == "mmlu_pro" else f"stage1_projection_student_as_{student_as}.json"
    (probe_dir / name).write_text(json.dumps(res, indent=1), encoding="utf-8")
    for m in ORDER:
        o = out[m]
        print(f"{m:28s} " + (f"fresh {o['fresh']:6.2f} deep {o['deep']:6.2f} tok/s | {o['gen_tokens']:6d} tok | {o['hours']:5.2f} h"
                             if "hours" in o else o.get("status", "")))
    print(f"TOTAL {total:.1f} h")


if __name__ == "__main__":
    flags = [x for x in sys.argv[1:] if x.startswith("--student-as=")]
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    main(Path(a[0]) if a else HERE / "runs/probe-20261003", Path(a[1]) if len(a) > 1 else HERE / "runs/calibration-20261002",
         flags[0].split("=", 1)[1] if flags else "mmlu_pro")

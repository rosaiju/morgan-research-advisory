"""Stage 2 runtime projection for the frozen finalists, from the actual Stage 1 v2 logs (read-only; runs nothing).

    local\\.venv\\Scripts\\python.exe local\\project_stage2.py      # writes local/STAGE2_PROJECTION.md

Stage 2 plan (REVISED_PROPOSAL_2026-10-02 section 7): fresh Compact panel of 186 capability + 80 IFEval + 18 student
items, 16,384 reasoning + 2,048 answer tokens. The capability split follows the frozen final-set mix
(MMLU-Pro 420 : MATH-500 400 : BBEH 460 -> 61 : 58 : 67). Every assumption is a named constant below.
"""
from __future__ import annotations

import json
import statistics as st
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "runs" / "stage1-v2"
FORCE_MARK = "Time is up. I must stop thinking now"
ORDER = ["r1-0528-qwen3-8b", "gpt-oss-20b", "glm-4.7-flash", "ministral-3-14b-reasoning", "muse-glimmer-30b",
         "qwen3.8-27b", "gemma-4-31b"]
FINALISTS = ["qwen3.8-27b", "gemma-4-31b", "gpt-oss-20b"]
PANEL = {"mmlu_pro": 61, "math500": 58, "bbeh_mini": 67, "ifeval": 80, "student": 18}
B_THINK, B_ANSWER = 16_384, 2_048
# probe-measured decode tok/s fresh and at 8K depth, and prompt-processing tok/s (runs/probe-20261003)
PROBE = {"qwen3.8-27b": (3.40, 3.29, 223), "gemma-4-31b": (2.61, 2.50, 189), "gpt-oss-20b": (42.2, 40.5, 925)}
# mean prompt tokens per benchmark (source lengths; BBEH mini mean ~3.8K chars, max ~16K chars)
PROMPT_MEAN = {"bbeh_mini": 1000, "mmlu_pro": 250, "math500": 150, "ifeval": 120, "student": 80}
PER_ITEM_OVERHEAD_S = 3
# Scenario assumptions.
#   cap      fraction of items whose natural reasoning exceeds 6,144 (Stage 1: BBEH 9/14 pooled, 5/6 finalists;
#            MMLU 3/35; MATH 0/21 on 3 easy items, but level-5 development items mostly ran past 24K; IFEval:
#            per-model rate smoothed from Stage 1)
#   capcost  reasoning tokens such an item uses at the 16,384 budget (calibration: 3 of 4 unforced BBEH attempts and
#            7 of 8 level-5 MATH attempts ran past 16K)
#   ans      answer tokens after a forced conclusion
#   hard     multiplier on Stage 1 natural lengths for capability items (the Stage 2 panel is broader and harder
#            than the 10 Stage 1 capability items)
#   slow     speed factor for deeper contexts (up to ~20K vs the 8K probe) and the larger n_ctx moving 1-2 layers
SCENARIOS = {
    "optimistic":   dict(cap={"bbeh_mini": .50, "math500": .05, "mmlu_pro": .05, "student": .00},
                         capcost=11_000, ans=300, hard=1.0, slow=1.00),
    "realistic":    dict(cap={"bbeh_mini": .64, "math500": .15, "mmlu_pro": .10, "student": .02},
                         capcost=B_THINK, ans=500, hard=1.5, slow=0.97),
    "conservative": dict(cap={"bbeh_mini": .83, "math500": .27, "mmlu_pro": .25, "student": .05},
                         capcost=B_THINK, ans=B_ANSWER, hard=2.0, slow=0.92),
}


def load() -> dict[str, list[dict]]:
    out = {}
    for m in ORDER:
        rows = [json.loads(l) for l in (RUN / f"attempts_{m}.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        out[m] = [r for r in rows if r.get("kind") == "item" and r.get("final_attempt")]
    return out


def capped(r: dict) -> bool:
    return FORCE_MARK in (r.get("reasoning_text") or "")


def tokens(r: dict) -> int:
    return (r.get("reasoning_tokens") or 0) + (r.get("final_tokens") or 0)


def stage1_stats(recs: list[dict]) -> dict:
    R = [r.get("reasoning_tokens") or 0 for r in recs]
    A = [r.get("final_tokens") or 0 for r in recs]
    wall = sum(r["wall_s"] for r in recs)
    comp = sum(r.get("completion_tokens") or 0 for r in recs)
    return {"items": len(recs), "reasoning_mean": round(st.mean(R)), "reasoning_median": round(st.median(R)),
            "answer_mean": round(st.mean(A)), "answer_median": round(st.median(A)), "cap_hits": sum(map(capped, recs)),
            "gen_tok_s_median": round(st.median(r["client_gen_tok_s"] for r in recs if r.get("client_gen_tok_s")), 2),
            "effective_tok_s": round(comp / wall, 2), "runtime_h": round(wall / 3600, 2)}


def project(recs: dict, m: str, scen: str) -> tuple[float, int]:
    a = SCENARIOS[scen]
    fresh, deep, pp = PROBE[m]
    eff = sum(r.get("completion_tokens") or 0 for r in recs[m]) / sum(r["wall_s"] for r in recs[m])
    hours = gen = 0.0
    for b, n in PANEL.items():
        if b == "ifeval":
            k = sum(capped(r) for r in recs[m] if r["benchmark"] == b)
            p = {"optimistic": k / 6, "realistic": (k + .5) / 7, "conservative": (k + 1) / 7}[scen]
        else:
            p = a["cap"][b]
        own = [tokens(r) for r in recs[m] if r["benchmark"] == b and not capped(r)]
        u = st.mean(own or [tokens(r) for mm in ORDER for r in recs[mm] if r["benchmark"] == b and not capped(r)])
        u *= a["hard"] if b in ("math500", "mmlu_pro", "bbeh_mini") else 1.0
        long_tok = a["capcost"] + a["ans"]
        t = n * ((1 - p) * u / (eff * a["slow"]) + p * long_tok / (deep * a["slow"]) + PROMPT_MEAN[b] / pp
                 + PER_ITEM_OVERHEAD_S)
        hours += t / 3600
        gen += n * ((1 - p) * u + p * long_tok)
    return round(hours, 1), round(gen / sum(PANEL.values()))


def main() -> None:
    recs = load()
    lines = [f"# Stage 2 runtime projection (generated {datetime.now(timezone.utc).isoformat(timespec='seconds')})", "",
             "Generated by `local/project_stage2.py` from the Stage 1 v2 logs. Projection only; no Stage 2 item has "
             "been selected or run.", "",
             f"Planned panel per finalist: {PANEL} = {sum(PANEL.values())} items; budget {B_THINK:,} + {B_ANSWER:,}.", "",
             "## Stage 1 behaviour of the finalists (22 items each, budget 6,144 + 1,536)", "",
             "| Model | reasoning mean | reasoning median | answer mean | answer median | reasoning-cap hits | "
             "decode tok/s (median) | effective tok/s | Stage 1 runtime h |", "|---|---|---|---|---|---|---|---|---|"]
    for m in FINALISTS:
        s = stage1_stats(recs[m])
        lines.append(f"| {m} | {s['reasoning_mean']:,} | {s['reasoning_median']:,} | {s['answer_mean']} | "
                     f"{s['answer_median']} | {s['cap_hits']}/22 | {s['gen_tok_s_median']} | {s['effective_tok_s']} | "
                     f"{s['runtime_h']} |")
    lines += ["", "## Projected Stage 2 generation time", "",
              "| Model | optimistic | realistic | conservative |", "|---|---|---|---|"]
    tot = {k: 0.0 for k in SCENARIOS}
    for m in FINALISTS:
        cells = []
        for scen in SCENARIOS:
            h, t = project(recs, m, scen)
            tot[scen] += h
            cells.append(f"{h} h (~{h / 24:.1f} d; {t:,} tok/item)")
        lines.append(f"| {m} | " + " | ".join(cells) + " |")
    lines.append("| **all three, sequential** | " + " | ".join(f"**{tot[s]:.0f} h (~{tot[s] / 24:.1f} d)**"
                                                          for s in SCENARIOS) + " |")
    lines += ["", "## Assumptions", "", "```", json.dumps(SCENARIOS, indent=1), "```", "",
              "- IFEval cap rate per model: optimistic k/6, realistic (k+0.5)/7, conservative (k+1)/7 (k = Stage 1 cap hits).",
              "- Natural-length items run at the model's Stage 1 effective throughput; capped items at the probe's "
              "8K-deep decode speed; both times the scenario's `slow` factor.",
              "- Not included: model loads (~15 s each), the optional 24,576-token rerun, reruns after infrastructure "
              "failures, scoring.", ""]
    (HERE / "STAGE2_PROJECTION.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

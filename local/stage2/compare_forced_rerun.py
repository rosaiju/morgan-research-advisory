"""Compare the Policy B forced-item rerun (24,576 reasoning tokens) with the official Stage 2 result (16,384) for the
same items. SENSITIVITY ONLY: reads both scored.jsonl files; the official result is not changed.

    python local/stage2/compare_forced_rerun.py <host> <model>

Writes local/stage2/sensitivity/forced_rerun_comparison_<host>_<model>.json and .md.
"""
from __future__ import annotations

import collections
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent / "runs"
MARK = "Time is up. I must stop thinking now"  # score_local.py FORCE_MARK


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def finals(d: Path) -> tuple[dict, dict]:
    scored = {r["item_id"]: r for r in map(json.loads, (d / "scored.jsonl").read_text(encoding="utf-8").splitlines())
              if r.get("final_attempt")}
    att = {}
    for p in d.glob("attempts_*.jsonl"):
        for line in p.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r.get("kind") == "item" and r.get("final_attempt"):
                att[r["item_id"]] = r
    return scored, att


def main(host: str, model: str) -> None:
    sel_path = HERE / "sensitivity" / f"forced_rerun_selection_{host}_{model}.json"
    sel = json.loads(sel_path.read_text(encoding="utf-8"))
    off_dir, re_dir = RUNS / f"stage2-{host}", RUNS / f"stage2-forced-rerun-{host}"
    os_, oa = finals(off_dir)
    rs, ra = finals(re_dir)
    ids = sel["selected_item_ids"]
    missing = [i for i in ids if i not in rs]
    if missing or set(rs) != set(ids):
        raise SystemExit(f"rerun incomplete or extra items: missing {missing}, extra {sorted(set(rs) - set(ids))}")
    rows = []
    for i in ids:
        o, r = os_[i], rs[i]
        rows.append({"item_id": i, "benchmark": o["benchmark"],
                     "official": {"status": o["status"], "correct": o["correct"], "flags": o["flags"],
                                  "completion_tokens": oa[i]["completion_tokens"],
                                  "reasoning_tokens": oa[i].get("reasoning_tokens"),
                                  "forced": MARK in (oa[i].get("reasoning_text") or "")},
                     "rerun": {"status": r["status"], "correct": r["correct"], "flags": r["flags"],
                               "completion_tokens": ra[i]["completion_tokens"],
                               "reasoning_tokens": ra[i].get("reasoning_tokens"),
                               "hit_24576_cap": MARK in (ra[i].get("reasoning_text") or ""), "wall_s": ra[i].get("wall_s")},
                     "same_seed": oa[i]["seed"] == ra[i]["seed"], "same_prompt": oa[i]["prompt_sha256"] == ra[i]["prompt_sha256"]})

    def tally(rr):
        c = collections.Counter()
        for x in rr:
            o, n = x["official"]["correct"], x["rerun"]["correct"]
            c["stayed_correct" if o and n else "stayed_incorrect" if not o and not n
              else "incorrect_to_correct" if n else "correct_to_incorrect"] += 1
            c["status_changed"] += x["official"]["status"] != x["rerun"]["status"]
            ext = {"EXTRACTION_FAILURE", "BUDGET_TRUNCATED"}
            c["extraction_or_truncation_outcome_changed"] += ((x["official"]["status"] in ext) != (x["rerun"]["status"] in ext)
                                                             or (x["official"]["status"] in ext and x["official"]["status"] != x["rerun"]["status"]))
            c["still_hit_24576_cap"] += x["rerun"]["hit_24576_cap"]
            c["official_correct"] += o
            c["rerun_correct"] += n
            c["n"] += 1
        return dict(c)

    by = {b: tally([x for x in rows if x["benchmark"] == b]) for b in sorted({x["benchmark"] for x in rows})}
    rep = {"purpose": "Policy B sensitivity analysis only; the official Stage 2 score is unchanged",
           "host": host, "model": model, "selection_record": str(sel_path.relative_to(HERE.parent.parent)).replace("\\", "/"),
           "selection_sha256": sha(sel_path),
           "official_scored_sha256": sha(off_dir / "scored.jsonl"), "rerun_scored_sha256": sha(re_dir / "scored.jsonl"),
           "rerun_attempts_sha256": sha(next(re_dir.glob("attempts_*.jsonl"))),
           "all_same_seed": all(x["same_seed"] for x in rows), "all_same_prompt": all(x["same_prompt"] for x in rows),
           "rerun_infrastructure_failures": sum(x["rerun"]["status"] == "INFRASTRUCTURE_FAILURE" for x in rows),
           "rerun_attempts_over_1": sum(1 for p in re_dir.glob("attempts_*.jsonl") for l in p.read_text(encoding="utf-8").splitlines()
                                        if json.loads(l).get("kind") == "item" and json.loads(l).get("attempt", 1) > 1),
           "total": tally(rows), "by_benchmark": by, "items": rows}
    out = HERE / "sensitivity" / f"forced_rerun_comparison_{host}_{model}"
    out.with_suffix(".json").write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    t = rep["total"]
    md = [f"# Policy B forced-item rerun: {model} on {host} (sensitivity only)", "",
          "The official Stage 2 score is unchanged. Same items, prompts, seeds and settings; only the reasoning budget "
          "changed from 16,384 to 24,576 tokens.", "",
          f"Official correct on these {t['n']} items: {t['official_correct']}; rerun correct: {t['rerun_correct']}.", "",
          "| Benchmark | n | stayed correct | stayed incorrect | incorrect→correct | correct→incorrect | "
          "extraction/truncation changed | still hit 24,576 |", "|---|---|---|---|---|---|---|---|"]
    for b, c in list(by.items()) + [("**total**", t)]:
        md.append(f"| {b} | {c['n']} | {c.get('stayed_correct', 0)} | {c.get('stayed_incorrect', 0)} | "
                  f"{c.get('incorrect_to_correct', 0)} | {c.get('correct_to_incorrect', 0)} | "
                  f"{c.get('extraction_or_truncation_outcome_changed', 0)} | {c.get('still_hit_24576_cap', 0)} |")
    md += ["", "| Item | official (16,384) | rerun (24,576) | rerun tokens | hit 24,576 |", "|---|---|---|---|---|"]
    for x in rows:
        md.append(f"| `{x['item_id']}` | {x['official']['status']} | {x['rerun']['status']} | "
                  f"{x['rerun']['completion_tokens']} | {'yes' if x['rerun']['hit_24576_cap'] else 'no'} |")
    out.with_suffix(".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("all_same_seed", "all_same_prompt", "rerun_infrastructure_failures",
                                          "rerun_attempts_over_1", "total", "by_benchmark")}, indent=1))
    for x in rows:
        print(x["item_id"], x["official"]["status"], "->", x["rerun"]["status"], x["rerun"]["completion_tokens"],
              "cap" if x["rerun"]["hit_24576_cap"] else "", x["rerun"]["flags"])
    for s in (".json", ".md"):
        print(out.with_suffix(s).name, sha(out.with_suffix(s)))


if __name__ == "__main__":
    main(*sys.argv[1:3])

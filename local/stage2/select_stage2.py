"""Deterministically select the fresh Stage 2 panel and the Stage 2 development probe items. No inference.

Stage 2 (approved 2026-10-05; REVISED_PROPOSAL_2026-10-02 section 7): 284 items per finalist
  capability 186, split as the frozen final-set mix (MMLU-Pro 420 : MATH-500 400 : BBEH 460):
    MMLU-Pro 61   14 subjects: 4 each + 5 subjects drawn for a 5th
    MATH-500 58   35 subject|level strata, proportional to the final set (largest remainder, seeded ties)
    BBEH     67   23 tasks: 2 each + 21 tasks drawn for a 3rd
  IFEval   80   simple random sample of the 541 official prompts
  Student  18   every suite prompt not used before (3 per category)
Sources: capability items from manifest/items/items_final.json (frozen final manifest); IFEval from the locked
official file; student items from the app suite v1.3.
Excluded: every item ever selected in this study (Stage 1 v1 core + reserve, Stage 1 v2, calibration, the Stage 1
probe items) and every item id found in any local/runs/*/attempts file.
Probe items (Stage 2 development probe) come from the development set only, so they can never be Stage 2 items.

    local\\.venv\\Scripts\\python.exe local\\stage2\\select_stage2.py
Writes local/stage2/items/stage2_panel.json, stage2_probe_items.json, stage2_items_lock.json, SELECTION_AUDIT.md.
"""
from __future__ import annotations

import collections
import glob
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCAL = HERE.parent
ROOT = LOCAL.parent
APP = Path(r"C:\Users\rohan\open-source-ai-model")
OUT = HERE / "items"
SEED = "morgan-local-stage2-2026-10-05"
TARGET = {"mmlu_pro": 61, "math500": 58, "bbeh_mini": 67, "ifeval": 80, "student": 18}
PROBE_ITEMS = ["math500/test/geometry/880.json", "ifeval/1012"]   # development items (Stage 1 calibration/probe)


def rng(label: str) -> random.Random:
    return random.Random(f"{SEED}|{label}")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def used_ids() -> tuple[set[str], dict[str, int]]:
    ids, src = set(), {}
    for n in ("stage1_panel.json", "stage1_panel_v2.json", "calibration_items.json"):
        s = {p["item_id"] for p in load(LOCAL / "items" / n)}
        src[f"local/items/{n}"] = len(s)
        ids |= s
    ids |= set(PROBE_ITEMS)
    seen = set()
    for f in glob.glob(str(LOCAL / "runs" / "**" / "attempts_*.jsonl"), recursive=True):
        for line in Path(f).read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(r, dict) and r.get("item_id") and not r["item_id"].startswith(("integration/", "synthetic/")):
                seen.add(r["item_id"])
    src["item ids in local/runs/**/attempts_*.jsonl"] = len(seen)
    return ids | seen, src


def largest_remainder(sizes: dict[str, int], n: int, label: str) -> dict[str, int]:
    total = sum(sizes.values())
    quota = {k: n * v / total for k, v in sizes.items()}
    alloc = {k: int(q) for k, q in quota.items()}
    keys = sorted(sizes)
    rng(label).shuffle(keys)                        # seeded tie-break
    keys.sort(key=lambda k: -(quota[k] - alloc[k]))  # stable: largest remainder first
    for k in keys[: n - sum(alloc.values())]:
        alloc[k] += 1
    return alloc


def main() -> None:
    final = load(ROOT / "manifest/items/items_final.json")
    dev_ids = {i["item_id"] for i in load(ROOT / "manifest/items/items_dev.json")}
    used, used_src = used_ids()
    panel, audit = [], {}

    def add(iid, bench, stratum, content_sha):
        assert iid not in used, iid
        panel.append({"benchmark": bench, "item_id": iid, "stratum": stratum, "content_sha256": content_sha})

    by = collections.defaultdict(lambda: collections.defaultdict(list))
    for it in sorted(final, key=lambda x: x["item_id"]):
        by[it["benchmark"]][it["stratum"]].append(it)

    # MMLU-Pro: equal strata (30 each) -> 4 per subject + 5 extra subjects
    subj = sorted(by["mmlu_pro"])
    extra = set(rng("mmlu|extra").sample(subj, TARGET["mmlu_pro"] - 4 * len(subj)))
    alloc_mmlu = {s: 4 + (s in extra) for s in subj}
    # MATH-500: proportional to the final set's subject|level strata
    alloc_math = largest_remainder({s: len(v) for s, v in by["math500"].items()}, TARGET["math500"], "math|alloc")
    # BBEH: equal strata (20 per task) -> 2 per task + 21 tasks with a 3rd
    tasks = sorted(by["bbeh_mini"])
    extra = set(rng("bbeh|extra").sample(tasks, TARGET["bbeh_mini"] - 2 * len(tasks)))
    alloc_bbeh = {t: 2 + (t in extra) for t in tasks}

    for bench, alloc in (("mmlu_pro", alloc_mmlu), ("math500", alloc_math), ("bbeh_mini", alloc_bbeh)):
        for s in sorted(alloc):
            pool = [it for it in by[bench][s] if it["item_id"] not in used]
            if len(pool) < alloc[s]:
                raise SystemExit(f"{bench}/{s}: need {alloc[s]}, only {len(pool)} unused")
            for it in rng(f"{bench}|{s}").sample(pool, alloc[s]):
                add(it["item_id"], bench, s, it["content_sha256"])
        audit[bench] = {s: alloc[s] for s in sorted(alloc) if alloc[s]}

    # IFEval
    ifeval = [json.loads(l) for l in (ROOT / "manifest/evaluation-sources/ifeval__data__input_data.jsonl")
              .read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(ifeval) == 541
    pool = sorted((r for r in ifeval if f"ifeval/{r['key']}" not in used), key=lambda r: r["key"])
    for r in rng("ifeval").sample(pool, TARGET["ifeval"]):
        add(f"ifeval/{r['key']}", "ifeval", "ifeval", sha(r["prompt"].encode("utf-8")))
    inst = collections.Counter(i.split(":")[0] for r in ifeval if f"ifeval/{r['key']}" in {p["item_id"] for p in panel}
                               for i in r["instruction_id_list"])
    audit["ifeval"] = {"pool_after_exclusion": len(pool), "instruction_groups": dict(sorted(inst.items()))}

    # Student suite: every unused prompt
    sys.path.insert(0, str(APP))
    from app.evaluation import suite
    fresh = [p for p in suite.SUITE if f"student/{p.id}" not in used]
    if len(fresh) != TARGET["student"]:
        raise SystemExit(f"student: expected {TARGET['student']} unused prompts, found {len(fresh)}")
    for p in fresh:
        add(f"student/{p.id}", "student", p.category, suite.prompt_hash(p))
    audit["student"] = dict(collections.Counter(p.category for p in fresh))

    # integrity
    ids = [p["item_id"] for p in panel]
    counts = collections.Counter(p["benchmark"] for p in panel)
    assert len(ids) == len(set(ids)) == sum(TARGET.values()), (len(ids), len(set(ids)))
    assert dict(counts) == TARGET, counts
    assert not set(ids) & used and not set(ids) & dev_ids and not set(ids) & set(PROBE_ITEMS)
    keys = load(ROOT / "manifest/items/answer_key_final.json")
    missing = [i for i in ids if i.split("/")[0] in ("mmlu_pro", "math500", "bbeh") and i not in keys]
    assert not missing, missing   # every capability item is scoreable (key exists); keys are NOT copied anywhere

    probe = [{"item_id": i, "purpose": p, "source": "development set (used in Stage 1 calibration/probe)"}
             for i, p in zip(PROBE_ITEMS, ["forced conclusion at 16,384 (ran past 24K unforced in calibration)",
                                           "natural-length item"])]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "stage2_panel.json").write_text(json.dumps(panel, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT / "stage2_probe_items.json").write_text(json.dumps(probe, indent=1), encoding="utf-8")
    lock = {"seed": SEED, "stage2_panel.json": sha((OUT / "stage2_panel.json").read_bytes()),
            "stage2_probe_items.json": sha((OUT / "stage2_probe_items.json").read_bytes()),
            "sources": {n: sha((ROOT / n).read_bytes()) for n in
                        ("manifest/items/items_final.json", "manifest/items/items_dev.json",
                         "manifest/evaluation-sources/ifeval__data__input_data.jsonl")},
            "app_suite_version": suite.SUITE_VERSION, "counts": dict(counts), "excluded_ids": len(used)}
    (OUT / "stage2_items_lock.json").write_text(json.dumps(lock, indent=1), encoding="utf-8")

    lines = ["# Stage 2 panel selection audit", "",
             f"Seed `{SEED}`; script `local/stage2/select_stage2.py` (deterministic: rerunning reproduces the same files).",
             "", f"Panel: {dict(counts)} = {len(ids)} items, identical for every finalist.", "",
             f"`stage2_panel.json` SHA-256 `{lock['stage2_panel.json']}`", "",
             "## Exclusions", "", f"{len(used)} item ids excluded (every item ever selected or run in this study):", ""]
    lines += [f"- {k}: {v}" for k, v in used_src.items()] + [f"- Stage 1 probe items: {PROBE_ITEMS}", "",
              "Checks: no Stage 2 item is in the exclusion set, the development set, or the probe items; every "
              "capability item has a key in the frozen final answer key.", "",
              "## Composition", ""]
    for b in ("mmlu_pro", "math500", "bbeh_mini"):
        lines += [f"**{b}** ({TARGET[b]}): " + ", ".join(f"{k} {v}" for k, v in audit[b].items()), ""]
    lines += [f"**ifeval** (80): pool after exclusion {audit['ifeval']['pool_after_exclusion']}; instruction groups "
              + ", ".join(f"{k} {v}" for k, v in audit["ifeval"]["instruction_groups"].items()), "",
              f"**student** (18): {audit['student']} (all unused suite prompts; the suite has 30, Stage 1 v1 selected "
              "12). Includes 3 programming items graded in the Docker sandbox.", "",
              "## Development probe items (never Stage 2 items)", ""]
    lines += [f"- `{p['item_id']}`: {p['purpose']}" for p in probe]
    (HERE / "SELECTION_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

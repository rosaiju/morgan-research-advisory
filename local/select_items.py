"""Deterministically select the Stage 1 panel and the calibration (development) items. No inference.

Sources (all already locked):
  manifest/items/items_final.json        frozen final manifest  -> Stage 1 MMLU-Pro / MATH-500 / BBEH
  manifest/items/items_dev.json          frozen development set -> calibration MMLU-Pro / MATH-500 / BBEH
  manifest/evaluation-sources/ifeval__data__input_data.jsonl (541 prompts) -> Stage 1 + calibration IFEval
  open-source-ai-model app/evaluation/suite.py v1.3 (30 prompts)          -> Stage 1 student suite

Stage 1 (approved plan): core 44 + reserve 12 = 56 items per model
  MMLU-Pro 14 core (1 per subject)
  MATH-500 10 core (2 per level L1..L5) + 2 reserve (1 at L4, 1 at L5)
  BBEH     6 distinct tasks: 4 core + 2 reserve, 1 item per task (official Mini items)
  IFEval   10 core + 2 reserve
  Student  6 core (1 per category) + 6 reserve (2nd per category)
Calibration: 6 per model, never scored for selection
  MMLU-Pro 2 (validation split, 2 different subjects), MATH-500 2 (dev set, L3-L5),
  BBEH 1 (dev set), IFEval 1 (not in the Stage 1 panel)

Every draw uses random.Random(f"{SEED}|<label>") over a sorted candidate list. Output:
  local/items/stage1_panel.json, local/items/calibration_items.json, local/items/items_lock.json

    python local/select_items.py
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
APP = Path(r"C:\Users\rohan\open-source-ai-model")
OUT = HERE / "items"
SEED = "morgan-local-stage1-2026-10-02"


def rng(label: str) -> random.Random:
    return random.Random(f"{SEED}|{label}")


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def student_suite():
    sys.path.insert(0, str(APP))
    from app.evaluation import suite  # noqa: E402
    return suite


def main() -> None:
    final = load_json(ROOT / "manifest/items/items_final.json")
    dev = load_json(ROOT / "manifest/items/items_dev.json")
    ifeval_path = ROOT / "manifest/evaluation-sources/ifeval__data__input_data.jsonl"
    ifeval = [json.loads(l) for l in ifeval_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(ifeval) == 541, len(ifeval)
    suite = student_suite()
    assert suite.SUITE_VERSION == "1.3", suite.SUITE_VERSION

    def by(items, bench):
        return sorted((i for i in items if i["benchmark"] == bench), key=lambda i: i["item_id"])

    panel: list[dict] = []

    def add(item: dict, block: str, bench: str, stratum: str, content_sha: str):
        panel.append({"block": block, "benchmark": bench, "item_id": item, "stratum": stratum,
                      "content_sha256": content_sha})

    # MMLU-Pro: one per subject
    mm = defaultdict(list)
    for i in by(final, "mmlu_pro"):
        mm[i["stratum"]].append(i)
    assert len(mm) == 14
    for subj in sorted(mm):
        pick = rng(f"mmlu_pro|{subj}").choice(mm[subj])
        add(pick["item_id"], "core", "mmlu_pro", subj, pick["content_sha256"])

    # MATH-500: by level (subject mixed within level)
    lv = defaultdict(list)
    for i in by(final, "math500"):
        lv[i["stratum"].split("|")[1]].append(i)
    reserve_levels = {"L4": 1, "L5": 1}
    for level in ["L1", "L2", "L3", "L4", "L5"]:
        order = lv[level][:]
        rng(f"math500|{level}").shuffle(order)
        for k, it in enumerate(order[: 2 + reserve_levels.get(level, 0)]):
            add(it["item_id"], "core" if k < 2 else "reserve", "math500", it["stratum"], it["content_sha256"])

    # BBEH: six distinct tasks from the official Mini; one item per task
    bt = defaultdict(list)
    for i in by(final, "bbeh_mini"):
        bt[i["stratum"]].append(i)
    assert len(bt) == 23
    tasks = rng("bbeh|tasks").sample(sorted(bt), 6)
    for k, task in enumerate(tasks):
        it = rng(f"bbeh|{task}").choice(bt[task])
        add(it["item_id"], "core" if k < 4 else "reserve", "bbeh_mini", task, it["content_sha256"])

    # IFEval: 12 of 541 (first 10 core)
    keys = sorted(r["key"] for r in ifeval)
    ifeval_by_key = {r["key"]: r for r in ifeval}
    if_pick = rng("ifeval|stage1").sample(keys, 12)
    for k, key in enumerate(if_pick):
        add(f"ifeval/{key}", "core" if k < 10 else "reserve", "ifeval", "ifeval",
            sha_bytes(ifeval_by_key[key]["prompt"].encode("utf-8")))

    # Student suite v1.3: per category, first -> core, second -> reserve
    for cat in suite.CATEGORIES:
        prompts = sorted(suite.by_categories([cat]), key=lambda p: p.id)
        order = prompts[:]
        rng(f"student|{cat}").shuffle(order)
        for k, p in enumerate(order[:2]):
            add(f"student/{p.id}", "core" if k == 0 else "reserve", "student", cat, suite.prompt_hash(p))

    # Calibration (development / non-panel only)
    cal: list[dict] = []
    mmd = by(dev, "mmlu_pro")
    subjects = rng("cal|mmlu|subjects").sample(sorted({i["stratum"] for i in mmd}), 2)
    for s in subjects:
        it = rng(f"cal|mmlu|{s}").choice([i for i in mmd if i["stratum"] == s])
        cal.append({"benchmark": "mmlu_pro", "item_id": it["item_id"], "stratum": s, "content_sha256": it["content_sha256"]})
    mdev = [i for i in by(dev, "math500") if i["stratum"].split("|")[1] in ("L3", "L4", "L5")]
    for it in rng("cal|math").sample(mdev, 2):
        cal.append({"benchmark": "math500", "item_id": it["item_id"], "stratum": it["stratum"], "content_sha256": it["content_sha256"]})
    bdev = by(dev, "bbeh_mini")
    it = rng("cal|bbeh").choice(bdev)
    cal.append({"benchmark": "bbeh_mini", "item_id": it["item_id"], "stratum": it["stratum"], "content_sha256": it["content_sha256"]})
    remaining = [k for k in keys if k not in set(if_pick)]
    key = rng("cal|ifeval").choice(remaining)
    cal.append({"benchmark": "ifeval", "item_id": f"ifeval/{key}", "stratum": "ifeval",
                "content_sha256": sha_bytes(ifeval_by_key[key]["prompt"].encode("utf-8"))})

    # Integrity checks
    final_ids = {i["item_id"] for i in final}
    dev_ids = {i["item_id"] for i in dev}
    pid = [p["item_id"] for p in panel]
    cid = [c["item_id"] for c in cal]
    assert len(pid) == len(set(pid)) == 56, len(pid)
    assert len(cid) == len(set(cid)) == 6
    assert not set(pid) & set(cid), "panel/calibration overlap"
    assert all(p["item_id"] in final_ids for p in panel if p["benchmark"] in ("mmlu_pro", "math500", "bbeh_mini"))
    assert all(c["item_id"] in dev_ids for c in cal if c["benchmark"] in ("mmlu_pro", "math500", "bbeh_mini"))
    assert not {p["content_sha256"] for p in panel} & {c["content_sha256"] for c in cal}
    counts = defaultdict(lambda: defaultdict(int))
    for p in panel:
        counts[p["block"]][p["benchmark"]] += 1
    expect = {"core": {"mmlu_pro": 14, "math500": 10, "bbeh_mini": 4, "ifeval": 10, "student": 6},
              "reserve": {"math500": 2, "bbeh_mini": 2, "ifeval": 2, "student": 6}}
    assert {b: dict(v) for b, v in counts.items()} == expect, dict(counts)

    OUT.mkdir(exist_ok=True)
    files = {"stage1_panel.json": panel, "calibration_items.json": cal}
    for name, obj in files.items():
        (OUT / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")
    lock = {name: sha_bytes((OUT / name).read_bytes()) for name in files}
    lock["inputs"] = {
        "items_final.json": sha_bytes((ROOT / "manifest/items/items_final.json").read_bytes()),
        "items_dev.json": sha_bytes((ROOT / "manifest/items/items_dev.json").read_bytes()),
        "ifeval__data__input_data.jsonl": sha_bytes(ifeval_path.read_bytes()),
        "student_suite.py": sha_bytes((APP / "app/evaluation/suite.py").read_bytes()),
        "student_suite_version": suite.SUITE_VERSION,
    }
    lock["seed"] = SEED
    lock["counts"] = {"stage1": {b: dict(v) for b, v in counts.items()}, "calibration": len(cal)}
    (OUT / "items_lock.json").write_text(json.dumps(lock, indent=1), encoding="utf-8")
    print(json.dumps(lock, indent=1))


if __name__ == "__main__":
    main()

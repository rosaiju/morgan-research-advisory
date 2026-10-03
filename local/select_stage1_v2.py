"""Stage 1 panel v2 (approved ~24 h variant, 2026-10-02): a deterministic subset of the LOCKED v1 core panel.

    MMLU-Pro 5 (of the 14 core) · MATH-500 3 (one each at L2, L3, L4) · BBEH 2 (of the 4 core tasks)
    IFEval 6 (of the 10 core) · Student 6 (the 6 core items, one per category)  = 22 items per model

No new item is introduced: every v2 item is a v1 core item, drawn with random.Random("stage1-v2|<label>") over the
v1 order. Writes local/items/stage1_panel_v2.json and local/items/stage1_v2_lock.json; v1 files are not modified.

    python local/select_stage1_v2.py
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
ITEMS = HERE / "items"
SEED = "stage1-v2"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    v1 = json.loads((ITEMS / "stage1_panel.json").read_text(encoding="utf-8"))
    cal = json.loads((ITEMS / "calibration_items.json").read_text(encoding="utf-8"))
    core = [p for p in v1 if p["block"] == "core"]

    def pick(bench, k, label, pool=None):
        pool = pool if pool is not None else [p for p in core if p["benchmark"] == bench]
        return random.Random(f"{SEED}|{label}").sample(pool, k)

    panel = []
    panel += pick("mmlu_pro", 5, "mmlu_pro")
    for level in ("L2", "L3", "L4"):
        pool = [p for p in core if p["benchmark"] == "math500" and p["stratum"].endswith("|" + level)]
        panel += pick("math500", 1, f"math500|{level}", pool)
    panel += pick("bbeh_mini", 2, "bbeh")
    panel += pick("ifeval", 6, "ifeval")
    panel += [p for p in core if p["benchmark"] == "student"]
    panel = [{k: v for k, v in p.items() if k != "block"} | {"v1_block": p["block"]} for p in panel]

    ids = [p["item_id"] for p in panel]
    assert len(ids) == len(set(ids)) == 22
    assert set(ids) <= {p["item_id"] for p in core}
    assert not set(ids) & {c["item_id"] for c in cal}, "Stage 1 / calibration overlap"
    assert not {p["content_sha256"] for p in panel} & {c["content_sha256"] for c in cal}
    out = ITEMS / "stage1_panel_v2.json"
    out.write_text(json.dumps(panel, indent=1, ensure_ascii=False), encoding="utf-8")
    counts = {}
    for p in panel:
        counts[p["benchmark"]] = counts.get(p["benchmark"], 0) + 1
    lock = {"stage1_panel_v2.json": sha(out), "derived_from": {"stage1_panel.json": sha(ITEMS / "stage1_panel.json"),
            "items_lock.json": sha(ITEMS / "items_lock.json")}, "seed": SEED, "counts": counts,
            "calibration_overlap": "none (checked by id and content hash)"}
    (ITEMS / "stage1_v2_lock.json").write_text(json.dumps(lock, indent=1), encoding="utf-8")
    print(json.dumps(lock, indent=1))
    for p in panel:
        print(" ", p["benchmark"], p["item_id"], p["stratum"])


if __name__ == "__main__":
    main()

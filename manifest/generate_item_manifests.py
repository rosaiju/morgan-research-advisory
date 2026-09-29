"""Deterministically generate development and final ITEM manifests (no model outputs, no inference).

Input: pinned files in manifest/evaluation-sources/ (see fetch_evaluation_sources.py and
evaluation-files-lock.json). Output (manifest/items/):
    items_final.json, items_dev.json            item ids, benchmark, stratum, prompt-source hash
    answer_key_final.json, answer_key_dev.json  gold answers ONLY here (isolated from item files)
    item_manifest_lock.json                     sha256 of every output + input file hashes used
Rules (from evaluation.json / dev-calibration-spec.json, seed 20260929):
    MMLU-Pro  final: 30 per subject from TEST (14 subjects); dev: all 70 VALIDATION items
    MATH-500  dev: 100 by proportional (subject, level) largest-remainder allocation, ties by stratum
              name; final: the other 400
    BBEH      v2: final = official BBEH Mini (460 = 20 per task); dev = 2 per task, seeded, excluding Mini
              (v1 drew its own 20 per task; archived in manifest/history/2026-09-29_v1_pre-MiMo/)
Refuses to run if an input's sha256 differs from evaluation-files-lock.json.

    python manifest/generate_item_manifests.py
"""

import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "evaluation-sources"
OUT = ROOT / "items"
SEED = 20260929


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def locked_bytes(name: str) -> bytes:
    lock = {r["file"]: r for r in json.loads((ROOT / "evaluation-files-lock.json").read_text(encoding="utf-8"))}
    data = (SRC / name).read_bytes()
    if lock.get(name, {}).get("sha256") != sha(data):
        raise SystemExit(f"{name}: hash does not match evaluation-files-lock.json")
    return data


def rng_for(label: str) -> random.Random:
    return random.Random(f"{SEED}|{label}")


def item(bench: str, iid: str, stratum: str, content: str) -> dict:
    return {"benchmark": bench, "item_id": iid, "stratum": stratum, "content_sha256": sha(content.encode("utf-8"))}


def mmlu_pro(final, dev, key_final, key_dev):
    import io
    import pyarrow.parquet as pq
    for split, target, keys in (("test", final, key_final), ("validation", dev, key_dev)):
        table = pq.read_table(io.BytesIO(locked_bytes(f"TIGER-Lab--MMLU-Pro__{split}.parquet"))).to_pylist()
        by_cat = defaultdict(list)
        for r in sorted(table, key=lambda r: int(r["question_id"])):
            by_cat[r["category"]].append(r)
        if len(by_cat) != 14:
            raise SystemExit(f"MMLU-Pro {split}: expected 14 subjects, found {len(by_cat)}")
        for cat in sorted(by_cat):
            rows = by_cat[cat]
            chosen = rows if split == "validation" else rng_for(f"mmlu_pro|{cat}").sample(rows, 30)
            for r in sorted(chosen, key=lambda r: int(r["question_id"])):
                iid = f"mmlu_pro/{r['question_id']}"
                target.append(item("mmlu_pro", iid, cat, json.dumps([r["question"], r["options"]], ensure_ascii=False)))
                keys[iid] = {"answer": r["answer"], "answer_index": r["answer_index"]}


def largest_remainder(sizes: dict[str, int], total: int) -> dict[str, int]:
    n = sum(sizes.values())
    quotas = {k: total * v / n for k, v in sizes.items()}
    alloc = {k: int(q) for k, q in quotas.items()}
    order = sorted(sizes, key=lambda k: (-(quotas[k] - alloc[k]), k))
    for k in order[: total - sum(alloc.values())]:
        alloc[k] += 1
    return alloc


def math500(final, dev, key_final, key_dev):
    rows = [json.loads(l) for l in locked_bytes("HuggingFaceH4--MATH-500__test.jsonl").decode("utf-8").splitlines() if l.strip()]
    if len(rows) != 500:
        raise SystemExit(f"MATH-500: expected 500 rows, found {len(rows)}")
    strata = defaultdict(list)
    for r in sorted(rows, key=lambda r: r["unique_id"]):
        strata[f"{r['subject']}|L{r['level']}"].append(r)
    dev_alloc = largest_remainder({k: len(v) for k, v in strata.items()}, 100)
    for s in sorted(strata):
        shuffled = strata[s][:]
        rng_for(f"math500|{s}").shuffle(shuffled)
        for i, r in enumerate(shuffled):
            iid = f"math500/{r['unique_id']}"
            target, keys = (dev, key_dev) if i < dev_alloc[s] else (final, key_final)
            target.append(item("math500", iid, s, r["problem"]))
            keys[iid] = {"answer": r["answer"]}


def bbeh(final, dev, key_final, key_dev):
    """v2: final = the OFFICIAL BBEH Mini (bbeh/mini/data.json, 460 = 20 per task, paper section 4);
    dev = 2 per task drawn with the seeded shuffle from items NOT in Mini (by id and by content)."""
    names = sorted(p.name for p in SRC.glob("bbeh__bbeh__benchmark_tasks__*__task.json"))
    if not names:
        raise SystemExit("BBEH task files not fetched")
    tasks = {}
    for name in names:
        task = name.split("__benchmark_tasks__")[1].split("__task.json")[0]
        tasks[task] = json.loads(locked_bytes(name))["examples"]
    first_index = {}
    for task in sorted(tasks):
        for idx, ex in enumerate(tasks[task]):
            first_index.setdefault((ex["input"], ex["target"]), (task, idx))
    mini = json.loads(locked_bytes("bbeh__bbeh__mini__data.json"))["examples"]
    mini_ids, mini_content = set(), set()
    for ex in mini:
        key = (ex["input"], ex["target"])
        if key not in first_index:
            raise SystemExit("BBEH Mini example not found in the pinned task files")
        task, idx = first_index[key]
        iid = f"bbeh/{task}/{idx}"
        mini_ids.add(iid)
        mini_content.add(sha(ex["input"].encode("utf-8")))
        final.append(item("bbeh_mini", iid, task, ex["input"]))
        key_final[iid] = {"answer": ex["target"]}
    per_task = {t: sum(1 for i in final if i["benchmark"] == "bbeh_mini" and i["stratum"] == t) for t in tasks}
    if len(mini_ids) != 460 or set(per_task.values()) != {20}:
        raise SystemExit(f"BBEH Mini: expected 460 unique items, 20 per task; got {len(mini_ids)} / {per_task}")
    for task in sorted(tasks):
        order = list(range(len(tasks[task])))
        rng_for(f"bbeh-dev-v2|{task}").shuffle(order)
        taken = 0
        for idx in order:
            ex = tasks[task][idx]
            iid = f"bbeh/{task}/{idx}"
            if iid in mini_ids or sha(ex["input"].encode("utf-8")) in mini_content:
                continue
            dev.append(item("bbeh_mini", iid, task, ex["input"]))
            key_dev[iid] = {"answer": ex["target"]}
            taken += 1
            if taken == 2:
                break
    return len(names)


def main():
    OUT.mkdir(exist_ok=True)
    final, dev, key_final, key_dev = [], [], {}, {}
    mmlu_pro(final, dev, key_final, key_dev)
    math500(final, dev, key_final, key_dev)
    n_tasks = bbeh(final, dev, key_final, key_dev)
    final_ids, dev_ids = {i["item_id"] for i in final}, {i["item_id"] for i in dev}
    assert not final_ids & dev_ids, "dev/final overlap by id"
    assert not {i["content_sha256"] for i in final} & {i["content_sha256"] for i in dev}, "dev/final overlap by content"
    for name, obj in (("items_final.json", final), ("items_dev.json", dev),
                      ("answer_key_final.json", key_final), ("answer_key_dev.json", key_dev)):
        (OUT / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    outputs = ("answer_key_dev.json", "answer_key_final.json", "items_dev.json", "items_final.json")
    lock = {name: sha((OUT / name).read_bytes()) for name in outputs}  # never hash the lock file itself
    lock["bbeh_task_count"] = n_tasks
    lock["counts"] = {"final": len(final), "dev": len(dev)}
    (OUT / "item_manifest_lock.json").write_text(json.dumps(lock, indent=1), encoding="utf-8")
    print(json.dumps(lock, indent=1))


if __name__ == "__main__":
    main()

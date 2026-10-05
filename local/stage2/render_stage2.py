"""Render the exact user-message text for the Stage 2 panel and probe items (no answers, no inference).

Same locked templates and rendering code as Stage 1 (local/render_prompts.py: manifest/prompts/ + prompts-lock.json,
pinned MMLU-Pro choice format, IFEval and student prompts verbatim). Every source file is checked against its lock,
and every item's content hash against the selection.

    .venv-scoring\\Scripts\\python.exe local\\stage2\\render_stage2.py
Writes local/stage2/items/stage2_rendered.json and stage2_rendered_lock.json.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCAL = HERE.parent
sys.path.insert(0, str(LOCAL))

import render_prompts as RP  # noqa: E402  (Stage 1 renderer: locked(), template(), render_mmlu())


def main() -> None:
    import pyarrow.parquet as pq

    panel = json.loads((HERE / "items/stage2_panel.json").read_text(encoding="utf-8"))
    stage1_rendered = json.loads((LOCAL / "items/rendered_prompts.json").read_text(encoding="utf-8"))
    probe = json.loads((HERE / "items/stage2_probe_items.json").read_text(encoding="utf-8"))
    mmlu = {}
    for split in ("test", "validation"):
        for r in pq.read_table(io.BytesIO(RP.locked(f"TIGER-Lab--MMLU-Pro__{split}.parquet"))).to_pylist():
            mmlu[f"mmlu_pro/{r['question_id']}"] = r
    math = {f"math500/{r['unique_id']}": r for r in
            (json.loads(l) for l in RP.locked("HuggingFaceH4--MATH-500__test.jsonl").decode("utf-8").splitlines() if l.strip())}
    bbeh = {}
    for p in sorted(RP.SRC.glob("bbeh__bbeh__benchmark_tasks__*__task.json")):
        task = p.name.split("__benchmark_tasks__")[1].split("__task.json")[0]
        for idx, ex in enumerate(json.loads(RP.locked(p.name))["examples"]):
            bbeh[f"bbeh/{task}/{idx}"] = ex
    ifeval = {f"ifeval/{r['key']}": r for r in
              (json.loads(l) for l in RP.locked("ifeval__data__input_data.jsonl").decode("utf-8").splitlines() if l.strip())}
    sys.path.insert(0, str(RP.APP))
    from app.evaluation import suite

    out = {}
    for it in panel:
        iid, bench = it["item_id"], it["benchmark"]
        if bench == "mmlu_pro":
            r = mmlu[iid]
            text = RP.render_mmlu(r["question"], list(r["options"]))
            check = RP.sha(json.dumps([r["question"], r["options"]], ensure_ascii=False).encode("utf-8"))
        elif bench == "math500":
            text = RP.template("math500_user_template.txt").format(prompt=math[iid]["problem"])
            check = RP.sha(math[iid]["problem"].encode("utf-8"))
        elif bench == "bbeh_mini":
            text = RP.template("bbeh_user_template.txt").format(input=bbeh[iid]["input"])
            check = RP.sha(bbeh[iid]["input"].encode("utf-8"))
        elif bench == "ifeval":
            text = ifeval[iid]["prompt"]
            check = RP.sha(text.encode("utf-8"))
        elif bench == "student":
            p = suite.get(iid.split("/", 1)[1])
            text, check = p.text, suite.prompt_hash(p)
        else:
            raise SystemExit(f"unknown benchmark {bench}")
        if check != it["content_sha256"]:
            raise SystemExit(f"{iid}: content hash mismatch with the Stage 2 selection")
        out[iid] = {"benchmark": bench, "text": text, "sha256": RP.sha(text.encode("utf-8"))}
    # probe items: development items, rendered identically for Stage 1 (copied, hash-checked against its lock)
    for p in probe:
        v = stage1_rendered[p["item_id"]]
        assert RP.sha(v["text"].encode("utf-8")) == v["sha256"]
        out[p["item_id"]] = {**v, "probe_only": True}

    path = HERE / "items/stage2_rendered.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    lock = {"stage2_rendered.json": RP.sha(path.read_bytes()),
            "from_stage2_items_lock": RP.sha((HERE / "items/stage2_items_lock.json").read_bytes()),
            "templates_lock": RP.sha((RP.ROOT / "manifest/prompts-lock.json").read_bytes()),
            "n_panel": len(panel), "n_probe": len(probe)}
    (HERE / "items/stage2_rendered_lock.json").write_text(json.dumps(lock, indent=1), encoding="utf-8")
    longest = sorted(((len(v["text"]), k) for k, v in out.items()), reverse=True)[:3]
    print(f"rendered {len(out)} prompts ({len(panel)} panel + {len(probe)} probe); longest chars: {longest}")


if __name__ == "__main__":
    main()

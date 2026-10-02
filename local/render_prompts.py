"""Render the exact user-message text for every selected item (no answers, no inference).

Templates are the locked files in manifest/prompts/ (prompts-lock.json); MMLU-Pro choices follow the pinned
inspect_ai 0.3.x multiple_choice renderer (letters joined by ",", options "A) text" joined by "\n",
no shuffling); IFEval and the student suite are used verbatim. Writes local/items/rendered_prompts.json
({item_id: {"text", "sha256"}}) and records its hash in local/items/rendered_lock.json.

Needs pyarrow (run with .venv-scoring\\Scripts\\python.exe):
    .venv-scoring\\Scripts\\python.exe local/render_prompts.py
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "manifest/evaluation-sources"
APP = Path(r"C:\Users\rohan\open-source-ai-model")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def locked(name: str) -> bytes:
    lock = {r["file"]: r["sha256"] for r in json.loads((ROOT / "manifest/evaluation-files-lock.json").read_text(encoding="utf-8")) if r.get("sha256")}
    data = (SRC / name).read_bytes()
    if lock.get(name) != sha(data):
        raise SystemExit(f"{name} does not match evaluation-files-lock.json")
    return data


def template(name: str) -> str:
    plock = json.loads((ROOT / "manifest/prompts-lock.json").read_text(encoding="utf-8"))
    data = (ROOT / "manifest/prompts" / name).read_bytes()
    if plock.get(name) != sha(data):
        raise SystemExit(f"{name} does not match prompts-lock.json")
    return data.decode("utf-8")


def answer_character(i: int) -> str:
    return chr(ord("A") + i) if i < 26 else str(i - 25)


def render_mmlu(question: str, options: list[str]) -> str:
    letters = ",".join(answer_character(i) for i in range(len(options)))
    choices = "\n".join(f"{answer_character(i)}) {o}" for i, o in enumerate(options))
    return template("mmlu_pro_user_template.txt").format(letters=letters, question=question, choices=choices)


def main() -> None:
    import pyarrow.parquet as pq

    items = json.loads((HERE / "items/stage1_panel.json").read_text(encoding="utf-8")) + \
        json.loads((HERE / "items/calibration_items.json").read_text(encoding="utf-8"))
    mmlu = {}
    for split in ("test", "validation"):
        for r in pq.read_table(io.BytesIO(locked(f"TIGER-Lab--MMLU-Pro__{split}.parquet"))).to_pylist():
            mmlu[f"mmlu_pro/{r['question_id']}"] = r
    math = {f"math500/{r['unique_id']}": r for r in
            (json.loads(l) for l in locked("HuggingFaceH4--MATH-500__test.jsonl").decode("utf-8").splitlines() if l.strip())}
    bbeh = {}
    for p in sorted(SRC.glob("bbeh__bbeh__benchmark_tasks__*__task.json")):
        task = p.name.split("__benchmark_tasks__")[1].split("__task.json")[0]
        for idx, ex in enumerate(json.loads(locked(p.name))["examples"]):
            bbeh[f"bbeh/{task}/{idx}"] = ex
    ifeval = {f"ifeval/{r['key']}": r for r in
              (json.loads(l) for l in locked("ifeval__data__input_data.jsonl").decode("utf-8").splitlines() if l.strip())}
    sys.path.insert(0, str(APP))
    from app.evaluation import suite

    out = {}
    for it in items:
        iid, bench = it["item_id"], it["benchmark"]
        if bench == "mmlu_pro":
            r = mmlu[iid]
            text = render_mmlu(r["question"], list(r["options"]))
            check = sha(json.dumps([r["question"], r["options"]], ensure_ascii=False).encode("utf-8"))
        elif bench == "math500":
            text = template("math500_user_template.txt").format(prompt=math[iid]["problem"])
            check = sha(math[iid]["problem"].encode("utf-8"))
        elif bench == "bbeh_mini":
            text = template("bbeh_user_template.txt").format(input=bbeh[iid]["input"])
            check = sha(bbeh[iid]["input"].encode("utf-8"))
        elif bench == "ifeval":
            text = ifeval[iid]["prompt"]
            check = sha(text.encode("utf-8"))
        elif bench == "student":
            p = suite.get(iid.split("/", 1)[1])
            text = p.text
            check = suite.prompt_hash(p)
        else:
            raise SystemExit(f"unknown benchmark {bench}")
        if check != it["content_sha256"]:
            raise SystemExit(f"{iid}: content hash mismatch with the selected item manifest")
        out[iid] = {"benchmark": bench, "text": text, "sha256": sha(text.encode("utf-8"))}

    path = HERE / "items/rendered_prompts.json"
    path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    lock = {"rendered_prompts.json": sha(path.read_bytes()),
            "from_items_lock": sha((HERE / "items/items_lock.json").read_bytes())}
    (HERE / "items/rendered_lock.json").write_text(json.dumps(lock, indent=1), encoding="utf-8")
    lengths = sorted(((len(v["text"]), k) for k, v in out.items()), reverse=True)[:5]
    print(f"rendered {len(out)} prompts; longest (chars): {lengths}")


if __name__ == "__main__":
    main()

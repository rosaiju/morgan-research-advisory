"""Fetch small, revision-pinned evaluation SOURCE and DATA files (no model weights, no inference).

Replaces the unvalidated fetch_evaluation_sources.ps1 (kept for history). Every URL uses an
immutable commit/revision from evaluation-source-lock.json or source-lock.json. Writes
manifest/evaluation-sources/ and manifest/evaluation-files-lock.json (sha256 per file).
Refuses any path that looks like model weights or tokenizer vocabularies.

    python manifest/fetch_evaluation_sources.py
"""

import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "evaluation-sources"
FORBIDDEN = re.compile(r"\.(safetensors|bin|pt|pth|gguf|ckpt|model|tiktoken)$|tokenizer\.json$", re.I)
lock = {row["id"]: row for row in json.loads((ROOT / "evaluation-source-lock.json").read_text(encoding="utf-8-sig"))}


def hf(repo: str, path: str) -> str:
    return f"https://huggingface.co/datasets/{repo}/resolve/{lock[repo]['revision']}/{path}"


def gh(repo: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{repo}/{lock[repo]['revision']}/{path}"


def gh_tree(repo: str) -> list[str]:
    url = f"https://api.github.com/repos/{repo}/git/trees/{lock[repo]['revision']}?recursive=1"
    req = urllib.request.Request(url, headers={"User-Agent": "morgan-research-prep"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return [e["path"] for e in json.load(r)["tree"] if e["type"] == "blob"]


REQUESTS: list[tuple[str, str]] = [
    (hf("TIGER-Lab/MMLU-Pro", "README.md"), "TIGER-Lab--MMLU-Pro__README.md"),
    (hf("TIGER-Lab/MMLU-Pro", "data/test-00000-of-00001.parquet"), "TIGER-Lab--MMLU-Pro__test.parquet"),
    (hf("TIGER-Lab/MMLU-Pro", "data/validation-00000-of-00001.parquet"), "TIGER-Lab--MMLU-Pro__validation.parquet"),
    (hf("HuggingFaceH4/MATH-500", "README.md"), "HuggingFaceH4--MATH-500__README.md"),
    (hf("HuggingFaceH4/MATH-500", "test.jsonl"), "HuggingFaceH4--MATH-500__test.jsonl"),
    (gh("google-deepmind/bbeh", "README.md"), "bbeh__README.md"),
    (gh("google-deepmind/bbeh", "bbeh/evaluate.py"), "bbeh__evaluate.py"),
    (gh("google-deepmind/bbeh", "bbeh/mini/data.json"), "bbeh__bbeh__mini__data.json"),  # added 2026-09-29 (official BBEH Mini)
    (gh("google-deepmind/bbeh", "leaderboard.md"), "bbeh__leaderboard.md"),
    *[(gh("google-research/google-research", f"instruction_following_eval/{p}"), f"ifeval__{p.replace('/', '__')}")
      for p in ("data/input_data.jsonl", "evaluation_lib.py", "instructions.py", "instructions_registry.py",
                "instructions_util.py", "requirements.txt")],
    *[(gh("UKGovernmentBEIS/inspect_evals", f"src/inspect_evals/{p}"), f"inspect_evals__{p.replace('/', '__')}")
      for p in ("mmlu_pro/mmlu_pro.py", "bbeh/bbeh.py", "ifeval/ifeval.py", "math/math.py", "math/utils.py")],
    *[(gh("huggingface/Math-Verify", p), f"math_verify__{p.replace('/', '__')}")
      for p in ("src/math_verify/parser.py", "src/math_verify/grader.py", "src/math_verify/__init__.py", "pyproject.toml")],
    ("https://huggingface.co/moonshotai/Kimi-K3/resolve/f831ab66814297da540d832a5235f8e904f29d06/encoding_k3.py",
     "kimi_k3__encoding_k3.py"),
]


def main() -> int:
    OUT.mkdir(exist_ok=True)
    try:  # BBEH task data: every benchmark_tasks/*/task.json at the pinned revision
        tree = gh_tree("google-deepmind/bbeh")
        tasks = sorted(p for p in tree if re.fullmatch(r"bbeh/benchmark_tasks/[^/]+/task\.json", p))
        REQUESTS.extend((gh("google-deepmind/bbeh", p), "bbeh__" + p.replace("/", "__")) for p in tasks)
        (OUT / "bbeh__tree.json").write_text(json.dumps(tree, indent=1), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        print("BBEH tree listing failed:", exc)
    records = []
    for url, name in REQUESTS:
        if FORBIDDEN.search(url):
            raise SystemExit(f"refusing weight/vocabulary-like path: {url}")
        target = OUT / name
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "morgan-research-prep"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            target.write_bytes(data)
            records.append({"url": url, "file": name, "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest(), "status": "fetched"})
        except Exception as exc:  # noqa: BLE001
            records.append({"url": url, "file": name, "status": "failed", "error": str(exc)})
    (ROOT / "evaluation-files-lock.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    for r in records:
        print(f"{r['status']:8} {r.get('bytes', ''):>10} {r['file']}")
    return 0 if all(r["status"] == "fetched" for r in records) else 1


if __name__ == "__main__":
    sys.exit(main())

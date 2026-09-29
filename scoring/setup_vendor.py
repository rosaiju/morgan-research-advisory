"""Assemble vendored, hash-checked scorer sources under scoring/vendor/ (no model, no inference).

- IFEval: the four pinned evaluator modules (already hashed in manifest/evaluation-files-lock.json) are
  copied into a package `instruction_following_eval`, plus the official instructions_test.py fetched at
  the same pinned commit (hash recorded in scoring/vendor/vendor-lock.json).
- BBEH: the pinned bbeh/evaluate.py functions (module-level example prints removed) -> bbeh_eval.py.
- Math-Verify: installed from the pinned commit archive (scoring/vendor/Math-Verify-<sha>/), see 20-*.md.

    python scoring/setup_vendor.py
"""
import hashlib
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "manifest" / "evaluation-sources"
LOCK = {r["file"]: r["sha256"] for r in json.loads((ROOT / "manifest" / "evaluation-files-lock.json").read_text(encoding="utf-8")) if r.get("sha256")}
VENDOR = ROOT / "scoring" / "vendor"
GR = "d36068b845da4c2b24927fee2cea1e6ef98dadda"
sha = lambda b: hashlib.sha256(b).hexdigest()


def locked(name: str) -> bytes:
    data = (SRC / name).read_bytes()
    if LOCK.get(name) != sha(data):
        raise SystemExit(f"{name} does not match evaluation-files-lock.json")
    return data


def main():
    record = {}
    pkg = VENDOR / "instruction_following_eval"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    for mod in ("evaluation_lib", "instructions", "instructions_registry", "instructions_util"):
        data = locked(f"ifeval__{mod}.py")
        (pkg / f"{mod}.py").write_bytes(data)
        record[f"instruction_following_eval/{mod}.py"] = {"sha256": sha(data), "source": f"google-research@{GR}"}
    url = f"https://raw.githubusercontent.com/google-research/google-research/{GR}/instruction_following_eval/instructions_test.py"
    data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "morgan-research-prep"}), timeout=120).read()
    (pkg / "instructions_test.py").write_bytes(data)
    record["instruction_following_eval/instructions_test.py"] = {"sha256": sha(data), "source": url}

    bbeh = locked("bbeh__evaluate.py").decode("utf-8")
    body = bbeh.split("# Examples")[0].rstrip() + "\n"
    header = ('# Vendored from google-deepmind/bbeh@80d12ca916b7158f22293fcf3144f4d3d854d4be bbeh/evaluate.py\n'
              '# (Apache-2.0). Functions unchanged; only the module-level example print() calls are removed.\n')
    (VENDOR / "bbeh_eval.py").write_text(header + body, encoding="utf-8")
    record["bbeh_eval.py"] = {"sha256": sha((VENDOR / "bbeh_eval.py").read_bytes()),
                              "derived_from_sha256": LOCK["bbeh__evaluate.py"], "change": "example prints removed"}
    (VENDOR / "vendor-lock.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    print(json.dumps(record, indent=1))


if __name__ == "__main__":
    main()

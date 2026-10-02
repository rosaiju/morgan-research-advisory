"""Re-run every local (no-network, no-inference) check in the package.   python verify_all.py

Requires .venv-scoring (see 21-local-validation-report.md). Exit code 0 only if every check passes.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VPY = str(ROOT / ".venv-scoring" / "Scripts" / "python.exe") if os.name == "nt" else str(ROOT / ".venv-scoring" / "bin" / "python")
MV = ROOT / "scoring" / "vendor" / "Math-Verify-ba3d3aaff23b3f4cac7a14672b4f6e293d97c98b"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def run(name, cmd, cwd=ROOT, env_extra=None, expect_tail=None, allow_codes=(0,)):
    env = {**os.environ, **(env_extra or {})}
    p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    tail = (p.stdout + p.stderr).strip().splitlines()[-1] if (p.stdout + p.stderr).strip() else ""
    ok = p.returncode in allow_codes and (expect_tail is None or expect_tail in tail)
    check(name, ok, f"-> {tail}")


# hashes
lock = json.loads((ROOT / "manifest/source-lock.json").read_text(encoding="utf-8-sig"))
files = [f for e in lock for f in e["files"] if f.get("status") == "fetched"]


def local(f):  # the lock records absolute paths from the original checkout folder; resolve inside this clone
    p = Path(f["local_file"])
    return p if p.exists() else ROOT.joinpath(*p.parts[p.parts.index("manifest"):])


bad = [f["path"] for f in files if not local(f).exists() or sha(local(f)) != f["sha256"]]
check("model source files vs source-lock.json", not bad, f"{len(files) - len(bad)}/{len(files)} match")
ev = [r for r in json.loads((ROOT / "manifest/evaluation-files-lock.json").read_text(encoding="utf-8")) if r.get("sha256")]
bad = [r["file"] for r in ev if sha(ROOT / "manifest/evaluation-sources" / r["file"]) != r["sha256"]]
check("evaluation sources vs evaluation-files-lock.json", not bad, f"{len(ev) - len(bad)}/{len(ev)} match")
il = json.loads((ROOT / "manifest/items/item_manifest_lock.json").read_text(encoding="utf-8"))
bad = [n for n, h in il.items() if n.endswith(".json") and sha(ROOT / "manifest/items" / n) != h]
check("item manifests vs item_manifest_lock.json", not bad, str(il.get("counts")))
pl = json.loads((ROOT / "manifest/prompts-lock.json").read_text(encoding="utf-8"))
bad = [n for n, h in pl.items() if sha(ROOT / "manifest/prompts" / n) != h]
check("prompt templates vs prompts-lock.json", not bad, f"{len(pl)} templates")
vl = json.loads((ROOT / "scoring/vendor/vendor-lock.json").read_text(encoding="utf-8"))
bad = [n for n, r in vl.items() if sha(ROOT / "scoring/vendor" / n) != r["sha256"]]
check("vendored scorer files vs vendor-lock.json", not bad, f"{len(vl)} files")

# JSON validity
js = [p for p in list((ROOT / "manifest").glob("*.json")) + list((ROOT / "runner").glob("*.json"))]
bad = []
for p in js:
    try:
        json.loads(p.read_text(encoding="utf-8-sig"))
    except ValueError:
        bad.append(p.name)
check("JSON manifests parse", not bad, f"{len(js)} files")

# test suites
run("runner offline tests", [sys.executable, "runner/test_offline.py"], expect_tail="OK")
nltk = {"NLTK_DATA": str(ROOT / "scoring/vendor/nltk_data")}
run("scorer fixtures", [VPY, "-m", "pytest", "scoring/test_scorers.py", "-q", "-p", "no:cacheprovider"], env_extra=nltk, expect_tail="passed")
run("IFEval official unit tests (seeded)", [VPY, "-m", "pytest", "instruction_following_eval/instructions_test.py", "-q", "-p", "no:cacheprovider", "-p", "ifeval_seed"],
    cwd=ROOT / "scoring/vendor", env_extra={**nltk, "PYTHONPATH": f"{ROOT / 'scoring/vendor'}{os.pathsep}{ROOT / 'scoring'}"}, expect_tail="41 passed")
run("Math-Verify upstream tests (inner timeout disabled; 3 timeout tests expected to fail)",
    [VPY, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider", "-p", "mv_no_inner_timeout"], cwd=MV,
    env_extra={"PYTHONPATH": str(ROOT / "scoring")}, expect_tail="3 failed, 288 passed", allow_codes=(1,))
run("BBEH suffix equals paper", [sys.executable, "scoring/verify_bbeh_suffix.py", "manifest/evaluation-sources/bbeh_paper/arxiv-2502.19187v2-main.tex"], expect_tail="MATCH")
run("secret scan", [sys.executable, "runner/secret_scan.py"], expect_tail="no credential-like strings found")
check("no stage authorised (runner/AUTHORIZATION.json absent)", not (ROOT / "runner/AUTHORIZATION.json").exists())
check("network opt-in not set in this environment", os.environ.get("MORGAN_ALLOW_NETWORK") != "1")

failed = [r for r in results if not r[1]]
print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
sys.exit(1 if failed else 0)

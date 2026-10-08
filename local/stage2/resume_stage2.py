"""Resume an interrupted official Stage 2 run on THIS host (added 2026-10-08 for the Morgan handoff; changes no
frozen file, no item, prompt, budget, setting or scoring rule).

    MORGAN_HOST=<host> python local/stage2/resume_stage2.py [--dry-run] [<model> ...]

Why: preflight_stage2's freshness check ("no overlap ... any previous run") and test_disjoint_from_everything_used
read every local/runs/**/attempts_*.jsonl, so once the official run has written its own attempts they fail by
construction and run_stage2.py refuses to resume (or to start the second model separately). This wrapper applies the
same post-run equivalents already used and committed for the Policy B rerun (run_forced_rerun.post_run_equivalents):
the two checks are re-run with only this host's own Stage 2 outputs excluded. Every other preflight check, the
approval gate, the freeze, the plan and the generation loop are run_stage2.py's own, unchanged.

The FIRST launch on a host always uses run_stage2.py itself; this script refuses when there is nothing to resume.
Before a real resume the existing RUN_INFO.json (rewritten by run_stage2.main) is copied to RUN_INFO.<UTC time>.json.
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

import preflight_stage2  # noqa: E402
import run_local as R  # noqa: E402
import run_stage2  # noqa: E402
from run_forced_rerun import FRESHNESS, TESTS, post_run_equivalents  # noqa: E402

_preflight = preflight_stage2.run


def _post_run_preflight(models=None, full_hash=False):
    # post_run_equivalents excludes stage2-<host>, its .raw-backup and stage2-forced-rerun-<host>; the forced
    # rerun's own .raw-backup (made after that runner was written) is this host's output too
    import glob
    extra, real_glob = str(C.RUNS / f"stage2-forced-rerun-{C.HOST}.raw-backup"), glob.glob
    glob.glob = lambda p, recursive=False: [f for f in real_glob(p, recursive=recursive) if str(Path(f).parent) != extra]
    try:
        post = post_run_equivalents()
    finally:
        glob.glob = real_glob
    return [c for c in _preflight(models, full_hash) if c[0] not in (FRESHNESS, TESTS)] + post


def main(args: list[str]) -> None:
    dry = "--dry-run" in args
    models = [a for a in args if not a.startswith("--")] or C.H["models"]
    attempts = sorted(C.RUN_DIR.glob("attempts_*.jsonl")) if C.RUN_DIR.exists() else []
    if not attempts:
        raise SystemExit(f"REFUSED: no official Stage 2 attempts in {C.RUN_DIR}; the first launch uses run_stage2.py")
    panel = {p["item_id"] for p in C.PANEL2}
    left = {m: len(panel - R.completed_items(C.RUN_DIR / f"attempts_{m}.jsonl")) for m in models}
    print(f"items still to generate on {C.HOST}: {left}")
    if not dry and not any(left.values()):
        raise SystemExit(f"REFUSED: nothing left to generate for {models} on {C.HOST}")
    info = C.RUN_DIR / "RUN_INFO.json"
    if not dry and info.exists():
        shutil.copy2(info, C.RUN_DIR / f"RUN_INFO.{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json")
    preflight_stage2.run = _post_run_preflight
    run_stage2.main(args)


if __name__ == "__main__":
    main(sys.argv[1:])

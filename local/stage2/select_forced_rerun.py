"""Policy B forced-rerun selection (local/stage2/FORCED_RERUN_POLICY.json, committed 6a0602e before generation).

    python local/stage2/select_forced_rerun.py <host> <model>

Reads ONLY kind, item_id, final_attempt and the forcing marker in reasoning_text from
local/runs/stage2-<host>/attempts_<model>.jsonl. No answer, key, status or score is read. Writes
local/stage2/sensitivity/forced_rerun_selection_<host>_<model>.json; refuses to overwrite an existing record.
"""
from __future__ import annotations

import hashlib
import json
import platform
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCAL = HERE.parent
POLICY = HERE / "FORCED_RERUN_POLICY.json"
MARK = "Time is up. I must stop thinking now"  # score_local.py FORCE_MARK


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(host: str, model: str) -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    attempts = LOCAL / "runs" / f"stage2-{host}" / f"attempts_{model}.jsonl"
    out = HERE / "sensitivity" / f"forced_rerun_selection_{host}_{model}.json"
    if out.exists():
        raise SystemExit(f"REFUSED: {out.name} already exists (the selection is fixed once recorded)")
    forced, n_final = set(), 0
    for line in attempts.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("kind") != "item" or not r.get("final_attempt"):
            continue
        n_final += 1
        if MARK in (r.get("reasoning_text") or ""):
            forced.add(r["item_id"])
    ids = sorted(forced)
    cap = policy["sample_cap"]
    seed = policy["seed"].replace("<model>", model)
    selected = ids if len(ids) <= cap else sorted(random.Random(seed).sample(ids, cap))
    rec = {"policy": "B", "policy_file": "local/stage2/FORCED_RERUN_POLICY.json", "policy_sha256": sha(POLICY),
           "policy_commit": "6a0602e", "host": host, "model": model,
           "selected_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "selected_before_scoring": True,
           "fields_read": ["kind", "item_id", "final_attempt", "reasoning_text (forcing marker presence only)"],
           "source": str(attempts.relative_to(LOCAL.parent)).replace("\\", "/"), "source_sha256": sha(attempts),
           "final_records": n_final, "forced_definition": policy["forced_item_definition"],
           "forced_count": len(ids), "forced_item_ids_sorted": ids,
           "sample_cap": cap, "seed": seed, "algorithm": policy["selection_algorithm"],
           "python": platform.python_version(), "selected_count": len(selected), "selected_item_ids": selected,
           "rerun_settings": policy["rerun_settings"], "reruns_started": False}
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{out.relative_to(LOCAL.parent)}: forced {len(ids)}, selected {len(selected)}, sha256 {sha(out)}")


if __name__ == "__main__":
    main(*sys.argv[1:3])

"""Freeze the Stage 1 v2 configuration (preparation only; does NOT run Stage 1 and does NOT create the approval file).

Sets config_local.json stage1_v2.frozen = true and writes local/items/stage1_v2_freeze.json with the SHA-256 of every
input Stage 1 depends on. Any later change to these files makes preflight fail until re-frozen.

    python local/freeze_stage1.py
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE_ID = os.environ.get("MORGAN_PROBE_ID", "probe-20261003")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    cfg_path = HERE / "config_local.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["stage1_v2"]["frozen"] = True
    cfg["stage1_v2"]["frozen_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cfg_path.write_text(json.dumps(cfg, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    files = ["config_local.json", "gguf_pins.json", "items/stage1_panel_v2.json", "items/stage1_v2_lock.json",
             "items/rendered_prompts.json", "items/rendered_lock.json", "official/official-lock.json",
             "client.py", "llm_server.py", "placement.py", "run_local.py", "score_local.py", "preflight.py"]
    files += sorted({m["template_file"] for m in cfg["models"].values()})
    probes = sorted(str(p.relative_to(HERE)).replace("\\", "/") for p in (HERE / "runs" / PROBE_ID).glob("probe_*.json"))
    rec = {"frozen_at": cfg["stage1_v2"]["frozen_at"], "config_sha256": sha(cfg_path),
           "files": {f: sha(HERE / f) for f in files},
           "probe_results": {p: sha(HERE / p) for p in probes},
           "gguf_sha256": {k: v["sha256"] for k, v in json.loads((HERE / "gguf_pins.json").read_text()).items()},
           "note": "Stage 1 execution still requires local/STAGE1_APPROVED.json written by the user."}
    (HERE / "items/stage1_v2_freeze.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in rec.items() if k != "files"}, indent=1))


if __name__ == "__main__":
    main()

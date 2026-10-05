"""Freeze the Stage 2 configuration for THIS host (preparation only; runs nothing, writes no approval).

    MORGAN_HOST=<host> python local/stage2/freeze_stage2.py

Requires a complete (not --skip-long) Stage 2 probe for every model assigned to the host. Writes
local/stage2/items/stage2_freeze_<host>.json with the SHA-256 of every Stage 2 input (paths relative to local/);
an existing record is archived to local/stage2/items/history/ first.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

FILES = ["stage2/config_stage2.json", "config_local.json", "gguf_pins.json", "official/official-lock.json",
         "stage2/items/stage2_panel.json", "stage2/items/stage2_items_lock.json", "stage2/items/stage2_probe_items.json",
         "stage2/items/stage2_rendered.json", "stage2/items/stage2_rendered_lock.json",
         "stage2/common.py", "stage2/probe_stage2.py", "stage2/run_stage2.py", "stage2/preflight_stage2.py",
         "stage2/select_stage2.py", "stage2/test_stage2.py", "stage2/freeze_stage2.py",
         "run_local.py", "client.py", "llm_server.py", "placement.py", "telemetry.py", "probe_local.py"]
# rendering and scoring happen on the local machine only (answer keys never leave it); hashed where present
LOCAL_ONLY = ["stage2/render_stage2.py", "score_local.py", "../scoring/docker_code.py", "../scoring/scorers.py"]


def main() -> None:
    stage1 = json.loads((C.LOCAL / "config_local.json").read_text(encoding="utf-8"))
    probes = {}
    for m in C.H["models"]:
        p = C.PROBE_DIR / f"probe_{m}.json"
        if not p.exists():
            raise SystemExit(f"REFUSED: no Stage 2 probe for {m} on {C.HOST}")
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("skip_long") or d.get("error") or not d.get("forced_conclusion_ok") or not d["integration"]["passed"]:
            raise SystemExit(f"REFUSED: the Stage 2 probe for {m} on {C.HOST} is incomplete or failed")
        probes[str(p.relative_to(C.LOCAL)).replace("\\", "/")] = C.sha(p)
    out = C.HERE / "items" / f"stage2_freeze_{C.HOST}.json"
    previous = None
    if out.exists():
        old = json.loads(out.read_text(encoding="utf-8"))
        hist = C.HERE / "items" / "history"
        hist.mkdir(exist_ok=True)
        dest = hist / f"stage2_freeze_{C.HOST}_{old['frozen_at'].replace(':', '').replace('+0000', 'Z')}.json"
        if not dest.exists():
            shutil.copy2(out, dest)
        previous = {"record": str(dest.relative_to(C.LOCAL)).replace("\\", "/"), "sha256": C.sha(dest)}
    files = (FILES + sorted({stage1["models"][m]["template_file"] for m in C.H["models"]})
             + [f for f in LOCAL_ONLY if (C.LOCAL / f).exists()])
    rec = {"frozen_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "host": C.HOST,
           "models": C.H["models"], "files": {f: C.sha(C.LOCAL / f) for f in files},
           "probe_results": probes, "host_info": C.host_info(),
           "gguf_sha256": {m: C.llm_server.PINS[m]["sha256"] for m in C.H["models"]},
           "forced_rerun_policy": C.CONFIG2["forced_rerun_policy"], "previous_freeze": previous,
           "note": f"Stage 2 on {C.HOST} still requires local/stage2/STAGE2_APPROVED_{C.HOST}.json written by the user."}
    rec["files"].update(probes)
    out.write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"frozen {out.name}: sha256 {C.sha(out)}")


if __name__ == "__main__":
    main()

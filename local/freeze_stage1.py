"""Freeze the Stage 1 v2 configuration (preparation only; does NOT run Stage 1 and does NOT create the approval file).

Sets config_local.json stage1_v2.frozen = true and writes local/items/stage1_v2_freeze.json with the SHA-256 of every
input Stage 1 depends on. Any later change to these files makes preflight fail until re-frozen.
An existing freeze record is first archived to local/items/history/ (never overwritten); the new record names it.

    python local/freeze_stage1.py
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROBE_ID = os.environ.get("MORGAN_PROBE_ID", "probe-20261003")
APP = Path(r"C:\Users\rohan\open-source-ai-model")
# outside local/: the Docker code sandbox, its tests, and the reference scorers
EXTRA_FILES = ["../scoring/docker_code.py", "../scoring/test_docker_code.py", "../scoring/scorers.py"]
# the app grader whose non-code checks score the student items (separate repository)
APP_FILES = ["app/evaluation/graders.py", "app/evaluation/suite.py"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sandbox_record() -> dict:
    sys.path.insert(0, str(HERE.parent / "scoring"))
    import docker_code
    return {"image": docker_code.IMAGE, "image_tag": docker_code.IMAGE_TAG, "image_local": docker_code.check_ready(),
            "run_args": docker_code.SANDBOX, "code_timeout_s": docker_code.CODE_TIMEOUT_S,
            "stdout_cap": docker_code.STDOUT_CAP, "stderr_cap": docker_code.STDERR_CAP}


def archive_previous() -> dict | None:
    old_path = HERE / "items/stage1_v2_freeze.json"
    if not old_path.exists():
        return None
    old = json.loads(old_path.read_text(encoding="utf-8"))
    hist = HERE / "items/history"
    hist.mkdir(exist_ok=True)
    stamp = old["frozen_at"].replace(":", "").replace("+0000", "Z")
    dest = hist / f"stage1_v2_freeze_{stamp}.json"
    if not dest.exists():
        shutil.copy2(old_path, dest)
    return {"record": str(dest.relative_to(HERE)).replace("\\", "/"), "record_sha256": sha(dest),
            "config_sha256": old["config_sha256"], "frozen_at": old["frozen_at"]}


def main() -> None:
    cfg_path = HERE / "config_local.json"
    previous = archive_previous()
    sandbox = sandbox_record()  # fails (no freeze written) unless Docker and the pinned image are ready
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    cfg["stage1_v2"]["frozen"] = True
    cfg["stage1_v2"]["frozen_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cfg_path.write_text(json.dumps(cfg, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    files = ["config_local.json", "gguf_pins.json", "items/stage1_panel_v2.json", "items/stage1_v2_lock.json",
             "items/rendered_prompts.json", "items/rendered_lock.json", "official/official-lock.json",
             "client.py", "llm_server.py", "placement.py", "run_local.py", "score_local.py", "preflight.py"]
    files += sorted({m["template_file"] for m in cfg["models"].values()}) + EXTRA_FILES
    probes = sorted(str(p.relative_to(HERE)).replace("\\", "/") for p in (HERE / "runs" / PROBE_ID).glob("probe_*.json"))
    app_commit = subprocess.run(["git", "-C", str(APP), "rev-parse", "HEAD"], capture_output=True, text=True).stdout
    rec = {"frozen_at": cfg["stage1_v2"]["frozen_at"], "config_sha256": sha(cfg_path),
           "files": {f: sha(HERE / f) for f in files},
           "probe_results": {p: sha(HERE / p) for p in probes},
           "gguf_sha256": {k: v["sha256"] for k, v in json.loads((HERE / "gguf_pins.json").read_text()).items()},
           "app_grader": {"repo": str(APP), "commit": app_commit.strip(),
                          "files": {f: sha(APP / f) for f in APP_FILES}},
           "code_sandbox": sandbox,
           "previous_freeze": previous,
           "note": "Stage 1 execution still requires local/STAGE1_APPROVED.json written by the user."}
    (HERE / "items/stage1_v2_freeze.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in rec.items() if k != "files"}, indent=1))


if __name__ == "__main__":
    main()

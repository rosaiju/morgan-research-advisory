"""Build the Morgan GPU bundle for Stage 2 (Qwen3.8-27B, Gemma 4 31B): only what generation needs, NO answer keys.

    local\\.venv\\Scripts\\python.exe local\\stage2\\make_morgan_bundle.py
Writes local/runs/morgan-bundle-<VERSION>/morgan-stage2-bundle.tar.gz (git-ignored) with SHA256SUMS.txt inside, and prints
the archive's SHA-256 (earlier versions stay in their own directories; the 2026-10-05 one is local/runs/morgan-bundle/). The archive unpacks to morgan-stage2/ with the repository layout the scripts expect.
"""
from __future__ import annotations

import hashlib
import io
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCAL = HERE.parent
ROOT = LOCAL.parent
VERSION = "20261008"   # 20261008: + Policy B files and resume_stage2.py; SHA256SUMS.txt written with LF line endings
OUT = LOCAL / "runs" / f"morgan-bundle-{VERSION}"
FILES = (
    [f"local/{n}" for n in ("run_local.py", "client.py", "llm_server.py", "placement.py", "telemetry.py", "probe_local.py",
                            "config_local.json", "gguf_pins.json", "requirements-local-lock.txt")]
    + [f"local/items/{n}" for n in ("rendered_prompts.json", "calibration_items.json", "stage1_panel.json",
                                    "stage1_panel_v2.json")]
    + [str(p.relative_to(ROOT)).replace("\\", "/") for p in sorted((LOCAL / "official").iterdir()) if p.is_file()]
    + [f"local/stage2/{n}" for n in ("common.py", "probe_stage2.py", "run_stage2.py", "preflight_stage2.py",
                                     "freeze_stage2.py", "test_stage2.py", "select_stage2.py", "config_stage2.json",
                                     "MORGAN_HANDOFF.md", "SELECTION_AUDIT.md", "MODELS.sha256",
                                     "README.md", "FORCED_RERUN_POLICY.json", "select_forced_rerun.py",
                                     "run_forced_rerun.py", "resume_stage2.py")]
    + [f"local/stage2/items/{n}" for n in ("stage2_panel.json", "stage2_items_lock.json", "stage2_probe_items.json",
                                           "stage2_rendered.json", "stage2_rendered_lock.json")]
    + ["manifest/items/items_dev.json"]
)


def main() -> None:
    for f in FILES:
        assert "answer_key" not in f and (ROOT / f).is_file(), f
    sums = "".join(f"{hashlib.sha256((ROOT / f).read_bytes()).hexdigest()}  {f}\n" for f in FILES)
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / "morgan-stage2-bundle.tar.gz"
    with tarfile.open(out, "w:gz") as tar:
        for f in FILES:
            tar.add(ROOT / f, arcname=f"morgan-stage2/{f}")
        data = sums.encode("utf-8")
        ti = tarfile.TarInfo("morgan-stage2/SHA256SUMS.txt")
        ti.size = len(data)
        tar.addfile(ti, io.BytesIO(data))
        for d in ("local/runs",):            # empty output directory in the expected place
            ti = tarfile.TarInfo(f"morgan-stage2/{d}")
            ti.type, ti.mode = tarfile.DIRTYPE, 0o755
            tar.addfile(ti)
    (OUT / "SHA256SUMS.txt").write_bytes(sums.encode("utf-8"))
    print(f"{len(FILES)} files, {out.stat().st_size / 2**20:.1f} MiB -> {out}")
    print(f"archive sha256 {hashlib.sha256(out.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()

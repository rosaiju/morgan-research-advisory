"""Download pinned GGUF weights (local/gguf_pins.json) with resume, then verify size and SHA-256.

Only the exact file named in the pin is fetched, from the immutable /resolve/<revision>/ URL.
Verified files get a sidecar <file>.sha256 so later runs (and preflight) skip re-hashing.

    python local/fetch_models.py r1-0528-qwen3-8b [more keys...]
    python local/fetch_models.py --all
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PINS = json.loads((HERE / "gguf_pins.json").read_text(encoding="utf-8"))
MODEL_DIR = Path(os.environ.get("MORGAN_MODEL_DIR", r"C:\llm\models"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def local_path(key: str) -> Path:
    return MODEL_DIR / PINS[key]["file"]


def verified(key: str) -> bool:
    p, side = local_path(key), local_path(key).with_suffix(".gguf.sha256")
    return p.exists() and side.exists() and side.read_text().strip() == PINS[key]["sha256"] \
        and p.stat().st_size == PINS[key]["size"]


def fetch(key: str) -> None:
    pin = PINS[key]
    dest = local_path(key)
    if verified(key):
        print(f"{key}: already verified")
        return
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    url = f"https://huggingface.co/{pin['repo']}/resolve/{pin['revision']}/{pin['file']}"
    print(f"{key}: downloading {pin['size'] / 1e9:.2f} GB", flush=True)
    # curl: follow redirects, resume partial files, retry transient failures
    subprocess.run(["curl", "-L", "--fail", "--retry", "10", "--retry-delay", "15", "-C", "-",
                    "-sS", "-o", str(dest), url], check=True)
    size = dest.stat().st_size
    if size != pin["size"]:
        raise SystemExit(f"{key}: size {size} != pinned {pin['size']}")
    digest = sha256_file(dest)
    if digest != pin["sha256"]:
        bad = dest.with_name(dest.name + f".sha-mismatch-{int(__import__('time').time())}")
        dest.rename(bad)  # kept for inspection; a retry downloads a fresh copy
        raise SystemExit(f"{key}: sha256 {digest} != pinned {pin['sha256']} (moved to {bad.name})")
    dest.with_suffix(".gguf.sha256").write_text(digest + "\n")
    print(f"{key}: verified {digest}", flush=True)


if __name__ == "__main__":
    keys = list(PINS) if sys.argv[1:] == ["--all"] else sys.argv[1:]
    unknown = [k for k in keys if k not in PINS]
    if not keys or unknown:
        raise SystemExit(f"usage: fetch_models.py KEY... | --all   (unknown: {unknown}; known: {list(PINS)})")
    for k in keys:
        fetch(k)

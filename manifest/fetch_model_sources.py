"""Fetch small, revision-pinned MODEL documentation/config/template files (no weights, no vocabularies).

Added 2026-09-29 for the MiMo-V2.6-Pro candidate audit (P35) and the dedicated Qwen FP8 route.
Appends/replaces entries in manifest/source-lock.json (same record format as the original six) and
writes files to manifest/<org>--<repo>/. Refuses weight and tokenizer-vocabulary paths.

    python manifest/fetch_model_sources.py
"""

import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FORBIDDEN = re.compile(r"\.(safetensors|bin|pt|pth|gguf|ckpt|model|tiktoken)$|tokenizer\.json$|vocab\.json$|merges\.txt$", re.I)
REPOS = {
    "XiaomiMiMo/MiMo-V2.6-Pro-RL": ("73875d00b30a89ef8cc353a0b60b0e9f9561952d",
        ["README.md", "config.json", "generation_config.json", "chat_template.jinja", "tokenizer_config.json",
         "configuration_mimo_v2.py"]),
    "XiaomiMiMo/MiMo-V2.6-Pro-MOPD": ("adea8e2c5373181e5a973fa1ecb343cb31af214b",
        ["README.md", "config.json", "generation_config.json", "chat_template.jinja", "tokenizer_config.json",
         "configuration_mimo_v2.py"]),
    "Qwen/Qwen3.8-2.4T-A95B-FP8": ("d2dc35658bcf77e66643428cb52e774cc3b5bd29",
        ["README.md", "config.json", "generation_config.json", "chat_template.jinja", "tokenizer_config.json"]),
}


def get(url: str) -> bytes:
    if FORBIDDEN.search(url):
        raise SystemExit(f"refusing weight/vocabulary-like path: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "morgan-research-prep"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def main() -> int:
    lock_path = ROOT / "source-lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8-sig"))
    ok = True
    for repo, (rev, files) in REPOS.items():
        folder = ROOT / repo.replace("/", "--")
        folder.mkdir(exist_ok=True)
        meta = json.loads(get(f"https://huggingface.co/api/models/{repo}/revision/{rev}"))
        (folder / "metadata.json").write_bytes(json.dumps(meta, indent=2).encode("utf-8"))
        rows = []
        for path in files:
            url = f"https://huggingface.co/{repo}/resolve/{rev}/{path}"
            local = folder / path.replace("/", "__")
            try:
                data = get(url)
                local.write_bytes(data)
                rows.append({"path": path, "url": url, "sha256": hashlib.sha256(data).hexdigest(),
                             "local_file": str(local), "status": "fetched"})
            except Exception as exc:  # noqa: BLE001
                ok = False
                rows.append({"path": path, "url": url, "status": "failed", "error": str(exc)})
        entry = {"id": repo, "revision": rev, "lastModified": meta.get("lastModified"), "files": rows,
                 "added": "2026-09-29 (fetch_model_sources.py)"}
        lock = [e for e in lock if e.get("id") != repo] + [entry]
        for r in rows:
            print(f"{r['status']:8} {repo}/{r['path']}")
    lock_path.write_text(json.dumps(lock, indent=4, ensure_ascii=False), encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

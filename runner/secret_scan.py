"""Fail if anything in the package looks like a real credential (run before every commit/share)."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATTERNS = [re.compile(p) for p in (
    r"sk-[A-Za-z0-9]{20,}",                      # OpenAI-style keys (DeepSeek, Moonshot, ...)
    r"Bearer\s+[A-Za-z0-9_\-\.]{20,}",
    r"(?i)(api[_-]?key|secret|token)\s*[=:]\s*['\"]?[A-Za-z0-9_\-\.]{24,}",
)]
SKIP_DIRS = {"evaluation-sources", "__pycache__", ".git"}
SKIP_SUFFIX = {".parquet", ".jsonl"}


def main() -> int:
    hits = []
    for p in ROOT.rglob("*"):
        third_party = any(part.startswith(".venv") for part in p.parts) or "vendor" in p.parts
        if not p.is_file() or third_party or SKIP_DIRS & set(p.parts) or p.suffix in SKIP_SUFFIX or p.name == ".env":
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pat in PATTERNS:
            for m in pat.finditer(text):
                hits.append(f"{p.relative_to(ROOT)}: {m.group(0)[:12]}...")
    print("\n".join(hits) if hits else "secret scan: no credential-like strings found")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())

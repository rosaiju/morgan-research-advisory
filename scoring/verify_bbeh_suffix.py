"""Verify prompts/bbeh_user_template.txt against the BBEH paper's Suffix box (arXiv 2502.19187v2 LaTeX source).

    python scoring/verify_bbeh_suffix.py <path-to-extracted-main.tex>

LaTeX collapses runs of spaces, so the paper's rendered text is compared after collapsing whitespace.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
tex = Path(sys.argv[1]).read_text(encoding="utf-8")
box = tex.split("title=Suffix]", 1)[1].split(r"\end{tcolorbox}", 1)[0].strip()
paper = re.sub(r"\s+", " ", box)
template = (ROOT / "manifest" / "prompts" / "bbeh_user_template.txt").read_text(encoding="utf-8")
prefix, suffix = template.split("\n\n", 1)
assert prefix == "{input}", prefix
print("paper suffix:", paper)
print("MATCH" if suffix == paper else "MISMATCH")
sys.exit(0 if suffix == paper else 1)

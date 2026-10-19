"""Paired analysis of Stage 2 scored results. Reads two scored.jsonl files, writes one new markdown report."""
import hashlib
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

MORGAN, GPTOSS, OUT = map(Path, sys.argv[1:4])
SEED = 20261019
B = 10_000
Z = 1.959963984540054
MODELS = ["qwen3.8-27b", "gemma-4-31b", "gpt-oss-20b"]
PAIRS = [("qwen3.8-27b", "gemma-4-31b"), ("qwen3.8-27b", "gpt-oss-20b"), ("gemma-4-31b", "gpt-oss-20b")]

if OUT.exists():
    sys.exit(f"refusing to overwrite {OUT}")


def load(p):
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


rows = load(MORGAN) + load(GPTOSS)
data = {}
for r in rows:
    if not r["final_attempt"]:
        continue
    key = (r["model"], r["item_id"])
    assert key not in data, key
    data[key] = r
items = sorted({i for (m, i) in data if m == "gpt-oss-20b"})
for m in MODELS:
    assert sorted(i for (mm, i) in data if mm == m) == items, f"item set differs for {m}"
bench = {i: data[("gpt-oss-20b", i)]["benchmark"] for i in items}
for m in MODELS:
    assert all(data[(m, i)]["benchmark"] == bench[i] for i in items)
    assert all(data[(m, i)]["correct"] == (data[(m, i)]["status"] == "CORRECT") for i in items)
benches = sorted(set(bench.values()))


def ok(m, i):
    return bool(data[(m, i)]["correct"])


def trunc(m, i):
    return data[(m, i)]["status"] == "BUDGET_TRUNCATED"


def wilson(k, n):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return c - h, c + h


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, j) for j in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def bootstrap(diffs, seed):
    rng = random.Random(seed)
    n = len(diffs)
    stats = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(B))
    return stats[int(0.025 * B)], stats[int(0.975 * B) - 1]


def pct(x):
    return f"{100 * x:.1f}%"


def acc_cell(k, n):
    lo, hi = wilson(k, n)
    return f"{k}/{n} = {pct(k / n)} [{pct(lo)}, {pct(hi)}]" if n else "n/a"


def pair_row(a, b, sel, seed):
    both = neither = a_only = b_only = 0
    diffs = []
    for i in sel:
        x, y = ok(a, i), ok(b, i)
        both += x and y
        neither += (not x) and (not y)
        a_only += x and not y
        b_only += y and not x
        diffs.append(int(x) - int(y))
    n = len(sel)
    d = sum(diffs) / n
    lo, hi = bootstrap(diffs, seed)
    p = mcnemar_exact(a_only, b_only)
    return (f"| {a} vs {b} | {n} | {both} | {neither} | {a_only} | {b_only} | {p:.4g} | "
            f"{100 * d:+.1f} pp [{100 * lo:+.1f}, {100 * hi:+.1f}] |")


PAIR_HDR = ("| Pair (A vs B) | n | Both right | Both wrong | A only right | B only right | McNemar exact p | "
            "Acc. diff A−B, 95% bootstrap CI |\n|---|---|---|---|---|---|---|---|")

out = []
w = out.append
w("# Stage 2 paired analysis: Qwen3.8-27B, Gemma 4 31B, gpt-oss-20b")
w("")
w("Generated 2026-10-19 on the laptop by a read-only script; no scored or attempt file was modified.")
w("")
w("## Inputs")
w("")
w("| File | SHA-256 | Rows used |")
w("|---|---|---|")
for p, ms in ((MORGAN, "qwen3.8-27b, gemma-4-31b"), (GPTOSS, "gpt-oss-20b")):
    w(f"| `{p.as_posix().split('morgan-research-advisory/')[-1]}` | `{hashlib.sha256(p.read_bytes()).hexdigest()}` | 284 per model ({ms}) |")
w("")
w(f"All three models have the same {len(items)} items, every row is `final_attempt: true` on attempt 1, and the "
  "benchmark label of each item agrees across files. `correct` is true exactly when status is CORRECT.")
w("")
w("## Methods")
w("")
w("- **Primary analysis:** the scorer's `correct` field. BUDGET_TRUNCATED, EXTRACTION_FAILURE and INCORRECT all "
  "count as incorrect.")
w("- **Sensitivity analysis (truncated excluded):** per-model accuracy drops that model's BUDGET_TRUNCATED items; "
  "each paired comparison drops items truncated by *either* model in the pair, so both models are compared on the "
  "same items. EXTRACTION_FAILURE stays incorrect.")
w("- **Wilson score interval**, 95% (z = 1.96), for each accuracy.")
w("- **Exact McNemar test:** two-sided exact binomial test on the discordant pairs (A-only vs B-only right), "
  "p = min(1, 2·P[X ≤ min(b, c)]) with X ~ Bin(b + c, 0.5).")
w(f"- **Paired bootstrap:** {B:,} resamples of items with replacement, percentile 95% CI for accuracy(A) − "
  f"accuracy(B). Python `random.Random`, seed {SEED} for the first pair and seed + k for the k-th pair, in the "
  "order listed (primary, then sensitivity: seeds 20261019 to 20261024).")
w("- No correction for multiple comparisons (3 pairs); a Bonferroni threshold would be p < 0.0167.")
w("")

w("## Status counts")
w("")
statuses = sorted({data[(m, i)]["status"] for m in MODELS for i in items})
w("| Model | " + " | ".join(statuses) + " |")
w("|---|" + "---|" * len(statuses))
for m in MODELS:
    c = Counter(data[(m, i)]["status"] for i in items)
    w(f"| {m} | " + " | ".join(str(c[s]) for s in statuses) + " |")
w("")

for title, excl in (("Primary: truncated counted as incorrect", False),
                    ("Sensitivity: truncated items excluded", True)):
    w(f"## {title}")
    w("")
    w("### Accuracy with Wilson 95% CI")
    w("")
    w("| Model | Overall | " + " | ".join(benches) + " |")
    w("|---|---|" + "---|" * len(benches))
    for m in MODELS:
        cells = []
        for subset in [items] + [[i for i in items if bench[i] == b] for b in benches]:
            sel = [i for i in subset if not (excl and trunc(m, i))]
            cells.append(acc_cell(sum(ok(m, i) for i in sel), len(sel)))
        w(f"| {m} | " + " | ".join(cells) + " |")
    w("")
    w("### Paired comparisons")
    w("")
    w(PAIR_HDR)
    for k, (a, b) in enumerate(PAIRS):
        sel = [i for i in items if not (excl and (trunc(a, i) or trunc(b, i)))]
        w(pair_row(a, b, sel, SEED + k + (3 if excl else 0)))
    w("")

w("## Per-benchmark discordant counts (primary, descriptive only)")
w("")
w("Counts are A-only right / B-only right. Per-benchmark samples are small, so no tests are reported here.")
w("")
w("| Pair | " + " | ".join(benches) + " |")
w("|---|" + "---|" * len(benches))
for a, b in PAIRS:
    cells = []
    for bn in benches:
        sel = [i for i in items if bench[i] == bn]
        cells.append(f"{sum(ok(a, i) and not ok(b, i) for i in sel)} / {sum(ok(b, i) and not ok(a, i) for i in sel)}")
    w(f"| {a} vs {b} | " + " | ".join(cells) + " |")
w("")

OUT.write_text("\n".join(out), encoding="utf-8")
print(f"wrote {OUT}")

# Stage 2 paired analysis: Qwen3.8-27B, Gemma 4 31B, gpt-oss-20b

## Reproduce

From the project root (`C:\Users\rohan\morgan-research-advisory`), with `.venv-scoring` (Python 3.14.4):

```powershell
.venv-scoring\Scripts\python.exe -I local\analysis\paired_analysis.py local\runs\stage2-morgan-gpu\scored.jsonl local\runs\stage2-local-rtx4060\scored.jsonl $env:TEMP\paired_analysis_rerun.md
```

- Script: `local/analysis/paired_analysis.py` (standard library only; Docker not needed).
- Arguments: Qwen/Gemma scored file, gpt-oss scored file, output path. The script refuses to overwrite an existing output, so write the rerun to a new path.
- Seeds: `random.Random`, 10,000 resamples per comparison. Primary: 20261019 (Qwen vs Gemma), 20261020 (Qwen vs gpt-oss), 20261021 (Gemma vs gpt-oss). Truncated-excluded: 20261022, 20261023, 20261024, same order.
- Check: the rerun output equals this file without this "Reproduce" section. Its SHA-256 is `70cb8f9bf7cffe93f4061545f293f55f57295e557adc40f0f78f813c775ee0d2` (verified 2026-10-19 by rerunning the repo copy of the script).

Generated 2026-10-19 on the laptop by a read-only script; no scored or attempt file was modified.

## Inputs

| File | SHA-256 | Rows used |
|---|---|---|
| `local/runs/stage2-morgan-gpu/scored.jsonl` | `fa44302541a87ac1a9e5f339b3bf28501884d472abd86042022b3daa99c03b41` | 284 per model (qwen3.8-27b, gemma-4-31b) |
| `local/runs/stage2-local-rtx4060/scored.jsonl` | `401982a592e4532a1d8ed5b49b22f4733a1660d612f43efbf8f6fa2980ed75ba` | 284 per model (gpt-oss-20b) |

All three models have the same 284 items, every row is `final_attempt: true` on attempt 1, and the benchmark label of each item agrees across files. `correct` is true exactly when status is CORRECT.

## Methods

- **Primary analysis:** the scorer's `correct` field. BUDGET_TRUNCATED, EXTRACTION_FAILURE and INCORRECT all count as incorrect.
- **Sensitivity analysis (truncated excluded):** per-model accuracy drops that model's BUDGET_TRUNCATED items; each paired comparison drops items truncated by *either* model in the pair, so both models are compared on the same items. EXTRACTION_FAILURE stays incorrect.
- **Wilson score interval**, 95% (z = 1.96), for each accuracy.
- **Exact McNemar test:** two-sided exact binomial test on the discordant pairs (A-only vs B-only right), p = min(1, 2·P[X ≤ min(b, c)]) with X ~ Bin(b + c, 0.5).
- **Paired bootstrap:** 10,000 resamples of items with replacement, percentile 95% CI for accuracy(A) − accuracy(B). Python `random.Random`, seed 20261019 for the first pair and seed + k for the k-th pair, in the order listed (primary, then sensitivity: seeds 20261019 to 20261024).
- No correction for multiple comparisons (3 pairs); a Bonferroni threshold would be p < 0.0167.

## Status counts

| Model | BUDGET_TRUNCATED | CORRECT | EXTRACTION_FAILURE | INCORRECT |
|---|---|---|---|---|
| qwen3.8-27b | 6 | 235 | 0 | 43 |
| gemma-4-31b | 12 | 233 | 0 | 39 |
| gpt-oss-20b | 8 | 198 | 8 | 70 |

## Primary: truncated counted as incorrect

### Accuracy with Wilson 95% CI

| Model | Overall | bbeh_mini | ifeval | math500 | mmlu_pro | student |
|---|---|---|---|---|---|---|
| qwen3.8-27b | 235/284 = 82.7% [77.9%, 86.7%] | 42/67 = 62.7% [50.7%, 73.3%] | 74/80 = 92.5% [84.6%, 96.5%] | 56/58 = 96.6% [88.3%, 99.0%] | 46/61 = 75.4% [63.3%, 84.5%] | 17/18 = 94.4% [74.2%, 99.0%] |
| gemma-4-31b | 233/284 = 82.0% [77.2%, 86.1%] | 38/67 = 56.7% [44.8%, 67.9%] | 75/80 = 93.8% [86.2%, 97.3%] | 56/58 = 96.6% [88.3%, 99.0%] | 49/61 = 80.3% [68.7%, 88.4%] | 15/18 = 83.3% [60.8%, 94.2%] |
| gpt-oss-20b | 198/284 = 69.7% [64.1%, 74.8%] | 22/67 = 32.8% [22.8%, 44.7%] | 68/80 = 85.0% [75.6%, 91.2%] | 51/58 = 87.9% [77.1%, 94.0%] | 41/61 = 67.2% [54.7%, 77.7%] | 16/18 = 88.9% [67.2%, 96.9%] |

### Paired comparisons

| Pair (A vs B) | n | Both right | Both wrong | A only right | B only right | McNemar exact p | Acc. diff A−B, 95% bootstrap CI |
|---|---|---|---|---|---|---|---|
| qwen3.8-27b vs gemma-4-31b | 284 | 218 | 34 | 17 | 15 | 0.8601 | +0.7 pp [-3.2, +4.6] |
| qwen3.8-27b vs gpt-oss-20b | 284 | 191 | 42 | 44 | 7 | 1.212e-07 | +13.0 pp [+8.5, +17.6] |
| gemma-4-31b vs gpt-oss-20b | 284 | 184 | 37 | 49 | 14 | 1.112e-05 | +12.3 pp [+7.0, +17.6] |

## Sensitivity: truncated items excluded

### Accuracy with Wilson 95% CI

| Model | Overall | bbeh_mini | ifeval | math500 | mmlu_pro | student |
|---|---|---|---|---|---|---|
| qwen3.8-27b | 235/278 = 84.5% [79.8%, 88.3%] | 42/61 = 68.9% [56.4%, 79.1%] | 74/80 = 92.5% [84.6%, 96.5%] | 56/58 = 96.6% [88.3%, 99.0%] | 46/61 = 75.4% [63.3%, 84.5%] | 17/18 = 94.4% [74.2%, 99.0%] |
| gemma-4-31b | 233/272 = 85.7% [81.0%, 89.3%] | 38/55 = 69.1% [56.0%, 79.7%] | 75/80 = 93.8% [86.2%, 97.3%] | 56/58 = 96.6% [88.3%, 99.0%] | 49/61 = 80.3% [68.7%, 88.4%] | 15/18 = 83.3% [60.8%, 94.2%] |
| gpt-oss-20b | 198/276 = 71.7% [66.2%, 76.7%] | 22/61 = 36.1% [25.2%, 48.6%] | 68/78 = 87.2% [78.0%, 92.9%] | 51/58 = 87.9% [77.1%, 94.0%] | 41/61 = 67.2% [54.7%, 77.7%] | 16/18 = 88.9% [67.2%, 96.9%] |

### Paired comparisons

| Pair (A vs B) | n | Both right | Both wrong | A only right | B only right | McNemar exact p | Acc. diff A−B, 95% bootstrap CI |
|---|---|---|---|---|---|---|---|
| qwen3.8-27b vs gemma-4-31b | 269 | 218 | 28 | 10 | 13 | 0.6776 | -1.1 pp [-4.8, +2.2] |
| qwen3.8-27b vs gpt-oss-20b | 273 | 191 | 36 | 39 | 7 | 1.832e-06 | +11.7 pp [+7.0, +16.5] |
| gemma-4-31b vs gpt-oss-20b | 266 | 184 | 26 | 44 | 12 | 2.088e-05 | +12.0 pp [+6.8, +17.3] |

## Per-benchmark discordant counts (primary, descriptive only)

Counts are A-only right / B-only right. Per-benchmark samples are small, so no tests are reported here.

| Pair | bbeh_mini | ifeval | math500 | mmlu_pro | student |
|---|---|---|---|---|---|
| qwen3.8-27b vs gemma-4-31b | 10 / 6 | 3 / 4 | 0 / 0 | 2 / 5 | 2 / 0 |
| qwen3.8-27b vs gpt-oss-20b | 23 / 3 | 8 / 2 | 5 / 0 | 6 / 1 | 2 / 1 |
| gemma-4-31b vs gpt-oss-20b | 23 / 7 | 9 / 2 | 5 / 0 | 10 / 2 | 2 / 3 |

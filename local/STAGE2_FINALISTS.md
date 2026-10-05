# Stage 2 finalist selection record (frozen before any Stage 2 result exists)

**Recorded:** 2026-10-05T03:30Z. **Decided by:** the user (Rohan Sainju), explicit instruction in the Claude Code
session. **State at recording:** Stage 1 v2 generation and scoring complete; no Stage 2 panel, prompt, probe, run
directory or result exists. This record must not be edited after Stage 2 begins; corrections go in a dated addendum.

## Finalists

1. **Qwen3.8-27B**
2. **Gemma 4 31B**
3. **gpt-oss-20b**

## Rule

The three highest-performing models under the frozen official Stage 1 scoring rules. Qwen3.8 and Gemma 4 tied
first (21/22); gpt-oss was next (20/22). The formatting-only sensitivity result (gpt-oss 21/22) is supporting
context only and did not decide the selection.

Stage 1 is a 22-item screening run. The selection does **not** claim that the finalists are statistically better
than R1-0528-Qwen3-8B, GLM-4.7-Flash or Muse Glimmer 30B: the top six are within two items of each other, and even
the largest pairwise gap (Qwen3.8 vs Ministral, 5 discordant items to 0) gives an exact two-sided p of about 0.06.

## Stage 1 evidence this decision is based on

Results: `local/runs/stage1-v2/scored.jsonl` SHA-256 `b9786f1bc19155bdaa50c505f3e0315fefc64a3d9bb3a0789163b15b1f38927f`
(raw attempts: `attempts_<model>.jsonl`, hashes below). Stage 1 freeze: `local/items/stage1_v2_freeze.json`
SHA-256 `eecb95d32e5dde9e2351f900befb27a190c6b5c769b007fc268df82e91321895`.

### OFFICIAL (frozen pre-registered rules)

| Rank | Model | Score | % |
|---|---|---|---|
| 1= | Qwen3.8-27B | 21/22 | 95.5 |
| 1= | Gemma 4 31B | 21/22 | 95.5 |
| 3 | gpt-oss-20b | 20/22 | 90.9 |
| 4= | R1-0528-Qwen3-8B | 19/22 | 86.4 |
| 4= | GLM-4.7-Flash | 19/22 | 86.4 |
| 4= | Muse Glimmer 30B | 19/22 | 86.4 |
| 7 | Ministral 3 14B | 16/22 | 72.7 |

### SENSITIVITY ONLY (formatting-only EXTRACTION_FAILUREs counted as correct; not an official result)

Four extraction failures had the keyed answer in a non-compliant format: gpt-oss `mmlu_pro/9323` (`**Answer:** A`),
Muse `mmlu_pro/3259` (`ANSWER: $B`), Ministral `math500 number_theory/1287` and `algebra/425` (`\boxed{}`, no ANSWER line).

| Rank | Model | Score | % |
|---|---|---|---|
| 1= | Qwen3.8-27B | 21/22 | 95.5 |
| 1= | Gemma 4 31B | 21/22 | 95.5 |
| 1= | gpt-oss-20b | 21/22 | 95.5 |
| 4 | Muse Glimmer 30B | 20/22 | 90.9 |
| 5= | R1-0528-Qwen3-8B | 19/22 | 86.4 |
| 5= | GLM-4.7-Flash | 19/22 | 86.4 |
| 7 | Ministral 3 14B | 18/22 | 81.8 |

### Raw attempt hashes (Stage 1 v2)

| File | SHA-256 |
|---|---|
| attempts_r1-0528-qwen3-8b.jsonl | 81c477917eb954d890c04e089a16144cb345a9d0762caa48fce89c595272bde0 |
| attempts_gpt-oss-20b.jsonl | 9d698028208f53c16c461da26855f5628232e07a5c3a1f64a2f7970393cb892d |
| attempts_glm-4.7-flash.jsonl | 33f2b550a73c285deb1f223192f8064cb99f97c49841b0f0c0d24da1ddd5b7d6 |
| attempts_ministral-3-14b-reasoning.jsonl | 5c934d2c2a2c65f717c1c3b6a9084db99799a24457e8c37f772bb5df4eceafe1 |
| attempts_muse-glimmer-30b.jsonl | f280ec03b94d3e9e6b074d5e07ac9610689b5620b6e27fec5d3d1c31a66f6f75 |
| attempts_qwen3.8-27b.jsonl | a7403bd0250aa09b14761dc2a9fd63d55ebcaf2256d0d03d230ddbe59d5e7e47 |
| attempts_gemma-4-31b.jsonl | 19a48b0d7b2b19f3fbd26fd6c8db9cbaf06a2f95ad15a042d98b6f48af5d13c5 |

## Stage 2 runtime projection

See `local/STAGE2_PROJECTION.md` (from `local/project_stage2.py`, based on the Stage 1 logs). Projection only; Stage 2
design items still open (panel selection and lock, probe at Stage 2 context, hardware/budget decision for the dense
finalists, optional 24,576 rerun scope) are decided and recorded before any Stage 2 generation.

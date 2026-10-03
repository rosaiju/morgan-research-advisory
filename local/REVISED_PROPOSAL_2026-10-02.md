# Revised local screening proposal (2026-10-02, after calibrating 4 of 7 models)

Status: PROPOSAL awaiting approval. Calibration queue stopped after Ministral; Muse Glimmer, Qwen3.8-27B and Gemma 4
31B have NOT been run. Stage 1 has NOT been started. All data is preserved in `local/runs/calibration-20261002/`
(analysis of all four models: `calibration_report_4models.json`, `scored_4models.jsonl`, `budget_scenarios.json`).

## 1. Why maximum reasoning with a 24,576-token ceiling is impractical on this machine

- The pre-registered rule set C1 = 24,576 (8K/12K/16K all failed). Natural completions observed (16 of 24 attempts):
  495 · 991 · 1,445 · 1,650 · 1,726 · 3,030 · 3,837 · 10,121 · 10,172 · 10,563 · 10,809 · 14,756 · 18,654 · 18,898 ·
  20,104 · 23,624; the other 8 attempts ran to 24,576 without finishing. Even MMLU-Pro items took a median ~10K tokens.
- Calibrating 4 models x 6 items took 7 h 50 min; Ministral alone 4 h 28 min (one item = 97 min).
- Stage 1 projection at 24,576 (core + reserve): R1 10.7 h, gpt-oss 4.8 h, GLM 7.7 h, Ministral ~34 h. The three dense
  ~30B models start ~3x slower than Ministral, so roughly 80-110 h each. Total ~300+ h versus a 24-48 h budget.

## 2. How much comes from long context versus CPU offload (measured)

| Model | Placement at 29.4K ctx | tok/s fresh | tok/s at 20K generated | Depth loss |
|---|---|---|---|---|
| R1-8B (dense) | 32/37 layers on GPU (81% of weights) | 32 (47 with all layers on GPU at 8K ctx) | 9 | -72% |
| Ministral 14B (dense) | 23/41 layers (55%) | 9.7 | 2.8 | -71% |
| gpt-oss-20b (MoE) | all layers/attention on GPU, experts split (47%) | 40 | 36 | -10% |
| GLM-4.7-Flash (MoE) | all layers/attention on GPU, experts on CPU (28%) | 31 | 23 | -24% |

- CPU offload sets the starting speed: R1 loses ~32% fresh when 5 layers move to CPU; Ministral starts at 9.7 tok/s
  because ~3.4 GB of weights stream from DDR5 per token. Dense ~30B models will start near 3-4 tok/s.
- Long context causes most of the remaining loss, but only when attention layers and their KV cache sit on the CPU:
  dense models lose ~70% by 20K; MoE models, whose attention is entirely on the GPU, lose only 10-24%.
- Over a 24K answer, depth roughly triples wall time for the dense models.

## 3. Realistic local screening methodology keeping all seven models

Unchanged: same seven models, llama.cpp b11349, bartowski Q4_K_M (gpt-oss MXFP4), official templates, publisher
sampling, highest documented reasoning level, paired items and seeds, locked scorers, status precedence, no composite
headline, Stage 1 approval gate. Two changes:

A. Placement rule (uniform, deployment-realistic): attention weights and the KV cache always on the GPU; when VRAM
   runs out, move feed-forward (dense) or expert (MoE) weights to the CPU first, chosen by the same 1 GiB fit margin.
   MoE models already behave this way (flat curves). Expected for dense models: similar fresh speed, much flatter
   with depth. Must be verified in the probe (section 6).
B. Common thinking budget with forced conclusion (replaces the C1 censoring rule as the Stage 1 budget): reasoning
   is capped at B_think; at the cap the reasoning block is closed with a fixed message ("Time is up. Give your final
   answer now in the required format.") and the model gets an answer allowance. No answer is ever lost to
   truncation, which was the 4K pilot's unfairness. Natural finish within budget is recorded per item.
   Prefer llama.cpp's `--reasoning-budget` + `--reasoning-budget-message` where it validates for a model's reasoning
   format; otherwise the harness performs the same two-phase forcing through the raw completion endpoint.

## 4. Proposed common budget

B_think = 6,144 reasoning tokens + up to 1,536 answer tokens (at most 7,680 generated). That is 1.5x the old 4,096 cap
for reasoning alone, plus a guaranteed answer step.
- No 20K+ runs, and the deepest context (~8-9K) stays where speed is still 60-80% of fresh even for dense models.
- The measured natural lengths are bimodal (all at or under 3.8K, or at least 10K). Any budget between 4K and 10K
  forces the same items, so a larger budget mainly adds cost. Per-item cost (development-set mix, measured):
  R1 3.7 min, gpt-oss 2.5, GLM 3.6, Ministral 10.8 (versus 5.0 / 3.2 / 4.8 / 14.9 at 8,192).
- Alternative if preferred: B_think = 8,192 (about 30% more time per item).

## 5. Smaller Stage 1 panel (12-24 h total)

Estimated cost per paired item across all seven, at B_think 6,144 with the placement rule (dense models estimated at
~3 tok/s pending the probe): capability item ~1.8 h (dense models ~30 min each = ~85% of it); IFEval or student item
~0.45 h.

| Variant | MMLU-Pro | MATH-500 | BBEH | IFEval | Student | Estimated total |
|---|---|---|---|---|---|---|
| ~24 h (recommended) | 5 | 3 (L2, L3, L4) | 2 | 6 | 6 (1 per category) | ~22-25 h |
| ~12 h | 3 | 1 (L3) | 1 | 4 | 4 | ~11-13 h |

Items are the first k of each benchmark in a seeded order of the ALREADY-LOCKED Stage 1 core panel, so no new item
selection is introduced. Honest limitation: with 10 capability items Stage 1 can only flag gross weakness (roughly
1-2/10 versus 8/10) plus compatibility, instruction-following and deployment behaviour. Small differences are not
interpretable. The final panel size is fixed by a pre-registered rule from probe-measured speeds (largest variant
projecting at or under 24 h).

## 6. Short compatibility and speed probe for Muse, Qwen3.8, Gemma (no long questions)

About 45 min per dense model, plus about 15 min each re-validating the four calibrated models (~3-3.5 h total):
1. Load at the Stage 1 context (~14K) under both placements (current `--fit` layer split, and attention-on-GPU).
   Record load time x3, offload by bytes and layers, KV size, VRAM, and RAM added by the load.
2. Template fidelity and effort-control render checks (no generation).
3. Budget-forcing check: one short prompt with B_think = 1,024. Confirm the reasoning closes, the forcing message is
   accepted, and an extractable final answer appears in this model's native format.
4. Truncation and token-accounting check (32 tokens).
5. Speed: pp512/tg256 fresh, and tg128 after a ~8K-token prefilled context, for each placement. This measures the
   depth penalty without any long generation.
Output: compatibility table, chosen placement rule, and a recomputed Stage 1 projection.

## 7. Larger reasoning budget for finalists (Stage 2)

Finalists (2-3) run the Compact panel on fresh items (186 capability + 80 IFEval + 18 student) with B_think = 16,384
(forced, + 2,048 answer). Optionally, a completeness check reruns the forced items unforced at the already-calibrated
24,576. Rough local runtime per finalist (development-set token profile; mixed items should be somewhat lower):
gpt-oss ~19 h, GLM ~30 h, R1 ~38 h, Ministral ~110 h, dense ~30B ~200-300 h. Dense finalists are realistic for
Stage 2 only on larger hardware (Morgan GPUs) or with a smaller Stage 2 budget; that is a decision for after Stage 1.

## Calibration findings worth keeping

- All 4 calibrated models passed integration (templates exact; Ministral differs only by the BOS token, which
  llama.cpp adds itself; GLM gating = sigmoid).
- No loops terminated, no infrastructure failures, no reruns.
- Development statuses: 8 CORRECT, 5 INCORRECT, 8 BUDGET_TRUNCATED (at 24,576), 2 EXTRACTION_FAILURE (Ministral used
  \boxed{} instead of the required ANSWER line), 1 MALFORMED (GLM wrote a second `</think>` inside its answer).
  These are pipeline checks only and influence no setting.
- No thermal throttling (max 69 C; flags idle / software power cap only).

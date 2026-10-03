# 22. Local evaluation plan (llama.cpp on RTX 4060 8 GB + 32 GB RAM)

October 2-3, 2026. Supersedes the hosted-API execution plan in 18-20 for execution purposes; those documents and the
`runner/` API adapters are kept unchanged as history. The capability methodology in 16 (scorers, status precedence,
statistics, no composite headline) is reused. Harness and evidence: [local/](local/README.md),
handoff: [local/HANDOFF.md](local/HANDOFF.md).

## Scope and models

Seven open-weight models, run locally through one backend (llama.cpp b11349, CUDA 12.4), one quantizer
(bartowski imatrix Q4_K_M; gpt-oss in its native MXFP4), official publisher chat templates, publisher sampling,
highest documented reasoning level: Qwen3.8-27B, Gemma 4 31B, Muse Glimmer 30B, GLM-4.7-Flash, gpt-oss-20b,
Ministral 3 14B Reasoning, DeepSeek-R1-0528-Qwen3-8B. Exact GGUF revisions and SHA-256: `local/gguf_pins.json`.

## History of decisions

1. **Calibration under the first plan** (2026-10-02, `local/runs/calibration-20261002/`): 6 development items per
   model at a 24,576-token development ceiling. The pre-registered rule selected C1 = 24,576. Four models were
   calibrated (R1, gpt-oss, GLM, Ministral) before the queue was stopped at the user's request. Findings: median
   MMLU-Pro reasoning about 10K tokens; one third of attempts did not finish within 24,576; decode on partially
   offloaded dense models fell about 70% with context depth because attention layers and their KV cache sat on the
   CPU. Stage 1 at C1 = 24,576 projected to about 300+ h. Kept as evidence; no longer the Stage 1 budget.
2. **Revised design approved 2026-10-02** (`local/REVISED_PROPOSAL_2026-10-02.md`):
   - placement rule: attention layers + KV cache on the GPU; feed-forward (dense) or expert (MoE) weights move to
     the CPU first, with a 1 GiB free-VRAM margin (`local/placement.py`). If all feed-forward weights on the CPU
     still do not fit, whole layers are moved too, recorded per model;
   - common reasoning budget 6,144 thinking tokens with forced conclusion + 1,536 answer tokens
     (`--reasoning-budget` with a fixed message; the harness enforces the answer allowance);
   - Stage 1 panel v2, about 24 h: 22 items per model (MMLU-Pro 5, MATH-500 3, BBEH 2, IFEval 6, student suite 6),
     a deterministic subset of the locked v1 core panel (`local/items/stage1_panel_v2.json`);
   - short compatibility and speed probes instead of long calibration for the three dense ~30B models.
3. **Stage 1 execution is NOT approved.** It requires `local/STAGE1_APPROVED.json` written by the user; the runner
   refuses otherwise.

## Fairness protections kept

Paired items and per-item seeds across models; final channel only scored; locked scorers (Math-Verify pinned,
official BBEH / IFEval); status precedence from 16 plus `forced_conclusion` and `answer_allowance_exceeded` flags;
no semantic retries; up to 2 infrastructure reruns; equal budget for every model; explicit sampler parameters (no
llama.cpp defaults); no speculative decoding; text only.

## Measured results (probes, 2026-10-03)

All seven: integration passed, maximum reasoning mode confirmed, forced conclusion validated end-to-end (six via
llama-server `--reasoning-budget`, Muse via the harness two-phase mechanism), full SHA-256 re-hash matched.

| Model | tok/s fresh / after 8K | GPU weight share | VRAM / RAM added | forced answer tokens |
|---|---|---|---|---|
| R1-0528-Qwen3-8B | 47.3 / 39.6 | 93% | 5.5 / 0.8 GB | 180 |
| gpt-oss-20b | 42.2 / 40.5 | 49% | 6.2 / 6.4 GB | 771 |
| GLM-4.7-Flash | 34.4 / 30.4 | 32% | 6.2 / 12.6 GB | 1,302 |
| Ministral 3 14B Reasoning | 13.4 / 12.9 | 62% | 6.0 / 3.4 GB | 540 |
| Muse Glimmer 30B | 3.63 / 3.61 | 34% | 6.0 / 11.6 GB | 347 (harness) |
| Qwen3.8-27B | 3.40 / 3.29 | 30% | 5.8 / 12.3 GB | 530 |
| Gemma 4 31B | 2.61 / 2.50 | 24% | 5.9 / 15.9 GB | 926 |

Projected Stage 1 v2 runtime from measured speeds: central 23.5 h, conservative 31.4 h. Dense vs MoE on this
hardware: MoE models keep all attention on the GPU and run 34-42 tok/s with little depth loss; dense ~30B models are
bound by streaming ~11-14 GB of CPU-resident weights per token (2.6-3.6 tok/s) and take 86% of Stage 1 time. Details:
`local/runs/probe-20261003/PROBE_REPORT.md`, `local/HANDOFF.md`.

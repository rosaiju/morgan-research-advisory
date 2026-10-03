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

## Measured results

See the "Overnight session" section of `local/HANDOFF.md` and `local/runs/probe-20261003/` (per-model probe
results and `stage1_projection.json`).

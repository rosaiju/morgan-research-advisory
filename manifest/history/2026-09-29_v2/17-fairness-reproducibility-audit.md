# 17. Fairness and reproducibility audit, v2 (re-run after the MiMo swap and hosted-route design)

September 29, 2026. The v1 audit is archived at `manifest/history/2026-09-29_v1_pre-MiMo/17-fairness-reproducibility-audit.md`. All v1 findings that still apply are carried forward.

This audit covers:
- [15](15-six-model-configuration-manifest.md) v2 and [16](16-frozen-evaluation-protocol.md) v2;
- [19](19-readiness-and-calibration-plan.md);
- `manifest/*.json`;
- `runner/`.

**Documented** means written into a manifest. **Tested** means executed. **Nothing has been tested against a model or a provider.**

## 1. Checks actually executed

| Check | Result |
|---|---|
| Original 32 model-source files vs `source-lock.json` | 32/32 match (v1 run) |
| **New:** MiMo RL @ `73875d00`, MiMo MOPD @ `adea8e2c` and Qwen FP8 @ `d2dc3565` non-weight files | 17/17 fetched, SHA-256 appended to `source-lock.json` (`fetch_model_sources.py` refuses weights, `tokenizer.json`, `vocab.json`, `merges.txt`) |
| **New:** RL vs MOPD interface files | config, generation_config, chat_template, tokenizer_config and configuration code are **byte-identical**; only the README differs |
| **New:** Qwen BF16 vs FP8 release | chat_template, generation_config and tokenizer_config **byte-identical**; config differs only by `quantization_config` (FP8 e4m3, 128×128 blocks, dynamic activations); `max_position_embeddings` 262,144 in both |
| Evaluation sources and data | 46/46 fetched and hashed (v1) |
| Item manifests | deterministic; **re-verified:** 1,280 unique final IDs, 216 unique development IDs, disjoint (assertions in `planning/cost_model_v2.py`) |
| Prompt templates | MMLU-Pro and MATH byte-identical to pinned Inspect (v1) |
| **New:** `models.json` v1 → v2 | recorded, reproducible transformation (`manifest/history/apply_v2_models.py`); v1 archived |
| **New:** runner offline tests (`runner/test_offline.py`) | **14/14 pass**. Covered: payloads carry the ceiling and explicit effort; no key in any payload; ceiling above a route limit refused; seed rule; SSE parsing; answer-only-in-reasoning gives `NO_FINAL_ANSWER`; status precedence; loop flag; network gate closed by default and without an authorisation file; redaction; **client-side Qwen rendering from the pinned template ends in `<think>` and carries the xhigh instruction** |
| **New:** `runner/secret_scan.py` | no credential-like strings in the package |
| JSON validity | all manifests and runner JSON parse |

Nothing was loaded, inferred or sent to any provider. No tokenizer vocabulary was downloaded.

## 2. Passed by design (documented, not tested)

These all carry over from v1:
- same tasks, items, prompts and scorers;
- answer keys isolated from the runner; the runner code never opens `answer_key_*`;
- explicit effort and sampling;
- a single status precedence;
- no random guessing, semantic retries or best-of selection;
- no hidden judges;
- preflight refusal;
- items and C frozen before outcomes.

**New in v2:**
- **Network gate:** it requires `MORGAN_ALLOW_NETWORK=1` **and** a user-written `runner/AUTHORIZATION.json` naming the stage, routes, spend cap and request cap.
- **Keys:** they are read only at send time from environment variables and never logged.
- **Separate strands:** capability and IFEval are separate in `evaluation.json`, and no composite exists.

## 3. Issues found and resolved (v1 items 1–15 carried; new items 16–27)

| # | Issue | Resolution |
|---|---|---|
| 16 | **MiMo generation_config:** `do_sample=false`, `max_new_tokens=2048` | explicit sampling in `models.json` and `routes.json`; never inherited |
| 17 | **Xiaomi API checkpoint:** cannot be tied to RL or MOPD | defined as a distinct configuration, H-MiMo-Xiaomi. The recommended route is DeepInfra, which states RL, pending written revision confirmation. Interface identity reduces the ambiguity to the weights. |
| 18 | **Hugging Face parameter count for MiMo:** ~524B | explained by packed MXFP4 U8 bytes; the model is 1.02T total / 42B active |
| 19 | **Ceiling rule not hosted-feasible:** v1's C = T ≈ 245,760 exceeds several routes' generated-token limits | v2 C_max = min route output limit = 131,072 (pending T1/T2); context windows are not treated as output limits |
| 20 | **Ceiling choice after calibration:** could have been arbitrary or cost-driven | pre-registered ladder rule on censoring counts D_m(L); accuracy, cost and runtime excluded |
| 21 | **Server-side templates:** hide the rendered prompt | payload hash, model echo, fingerprint; T3/T4 effort checks; client rendering on the dedicated Qwen route |
| 22 | **DeepSeek API effort default:** `high` | `reasoning_effort="max"` explicit |
| 23 | **Qwen route context extension:** Alibaba, Novita, SiliconFlow, Modal and Together advertise ~1M (vLLM requires YaRN beyond 262,144) | recommended route pins `--max-model-len 262144`, no YaRN |
| 24 | **Alibaba `thinking_budget`:** forces an answer when exceeded; default ambiguous (4,000 in the console) | Alibaba not recommended |
| 25 | **Together:** conflates Qwen3.8-Max with the open checkpoint; different effort vocabulary | not recommended |
| 26 | **Provider moderation and resource finish reasons:** had no status | `PROVIDER_FILTERED` status; resource/abort reasons mapped to `INFRASTRUCTURE_FAILURE` |
| 27 | **Xiaomi `repetition_truncation`:** a server-side loop intervention | flag `provider_repetition_truncation` with status `NO_FINAL_ANSWER`; a further reason to prefer DeepInfra for P35 |

**Blockers from v1 now closed for the hosted routes:**
- **GLM EOS names and the Kimi output parser:** providers return separated channels and finish reasons. These remain relevant only if self-hosted.
- **Tokenizer-based ceiling computation:** feasibility is shown from character counts, since 131,072 is far below the native contexts.

## 4. Unresolved issues (each blocks the stage named)

| Issue | Blocks | Prerequisite to close it |
|---|---|---|
| Z.ai `max_tokens` may exclude reasoning tokens | the C_max value; development calibration for P27/P28 | integration test T2; if excluded, a pre-outcome decision (client-side cut-off or another route) |
| MiMo served checkpoint and revision (DeepInfra) | final labelling of P35 | written answer from DeepInfra (stage 1); otherwise H-MiMo-Xiaomi, labelled |
| DeepInfra MiMo "fp8": native MXFP4-stored weights or a re-quantization? | precision identity for P35 | written answer (stage 1) |
| Qwen dedicated deployment (GPU host, vLLM version, cost) | P34 integration and calibration | separate authorisation to rent 16× B300/MI355X or 32× H200; alternatively the FP4 fallback, disclosed |
| First-party served precision undisclosed (DeepSeek, Z.ai, Moonshot, Xiaomi) | full precision identity | written answers; otherwise recorded as undisclosed |
| Provider aliases can change silently | reproducibility | drift abort on `model_echo_changed`; short run windows; record dates |
| Math-Verify not installed or tested; BBEH suffix provenance | scoring | v1 items, unchanged |
| Seeds unsupported on most routes | bit-level reproducibility | disclosed; configuration-level reproducibility only |
| Kimi price ($15 vs $12 output) and all other list prices | budgeting only | re-verify at stage 1 |

## 5. Fairness limits by design (disclose, don't fix)

**Carried from v1:**
- different sampling across families;
- equal tokens are not equal compute;
- native effort prompts differ;
- a single generation at temperature 1;
- contamination;
- a purposive sample;
- a ceiling effect on MATH-500.

**New in v2:**
- **Heterogeneous serving:**
  - Four models run on first-party APIs: DeepSeek, Z.ai ×2, Moonshot.
  - MiMo runs on a third party (DeepInfra) or on Xiaomi as a distinct configuration.
  - Qwen runs on a study-managed vLLM deployment of the publisher's FP8 release.
  - Serving stacks, kernels and batching differ, and served precision is partly undisclosed.
  - Each result is reported with its route ID.
- **Precision is not uniform:**
  - The native formats differ by model: DeepSeek FP8/FP4, GLM FP8, Kimi MXFP4, MiMo MXFP4/FP8, Qwen BF16.
  - Qwen served in FP8 is the publisher's own quantized release, disclosed as such. BF16 would need 24× B300.
  - The FP4 fallback, if used, is below native precision and must be labelled a different configuration.
- **Provider-fixed sampling:**
  - Kimi, Xiaomi and DeepSeek fix some sampling settings server-side. Kimi's and Xiaomi's fixed values equal the publisher recommendations.
  - DeepSeek's thinking-mode temperature is undisclosed.
- **Provider interventions:** Xiaomi's repetition truncation, if that route is used, is reported per route.
- **One common ceiling (≤131,072) is below several publishers' recommendations:**
  - DeepSeek 384K;
  - Qwen 262K reasoning + 131K final.
  - Censoring is measured and reported.

## 6. Reproducibility record per attempt (v2 runner specification)

Each attempt records:
- route ID, provider, model string and echoed model ID/fingerprint;
- request-payload SHA-256 (keys excluded), plus the rendered-prompt SHA-256 on the client-rendered route;
- ceiling, effort and sampling as sent;
- seed and whether it is honoured;
- finish reason and stop detail;
- prompt, completion and reasoning token counts;
- raw reasoning and final text;
- status and flags;
- estimated cost;
- wall time;
- rerun count;
- date.

## 7. Verdict

**Methodology:** complete and frozen as a procedure, including the new pre-registered ceiling-selection rule. The model set is v2, tentatively accepted.

**Adapter architecture:** built and offline-tested. It cannot send anything until the user authorises a stage.

**Not yet executable.** The remaining gates, in order:
1. Provider written answers (stage 1).
2. The integration test: 34 requests, cap $15; T2 decides the GLM ceiling question.
3. A decision and authorisation for the dedicated Qwen deployment, or acceptance of the FP4 fallback.
4. Math-Verify installation and scorer fixtures.
5. Development calibration, then freezing C_final.

**Hardware:** no hardware information was used for model selection.

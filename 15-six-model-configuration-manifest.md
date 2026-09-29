# 15. Six-model configuration manifest (v2)

> **Version 2 (2026-09-29).** The user tentatively accepted the set proposed in [18](18-final-candidate-and-execution-audit.md): **P35 MiMo-V2.6-Pro replaces P24 DeepSeek-V4.1-Flash**. The P24 row and its findings remain below, marked superseded, for history. The v1 file is archived at `manifest/history/2026-09-29_v1_pre-MiMo/`. Hosted execution routes are in [19](19-readiness-and-calibration-plan.md) and `runner/routes.json`.

September 29, 2026. **Proposed; nothing executed.** No inference, model loading, benchmark or weight download has occurred. Machine-readable version: [manifest/models.json](manifest/models.json). Source files: `manifest/<publisher>--<model>/`, all 32 re-verified against [manifest/source-lock.json](manifest/source-lock.json) on 2026-09-29 (32 match, 0 mismatch, 0 missing).

Every entry is labelled **verified** (read in the pinned, hash-checked source; line numbers cited), **proposed** (a study decision made now, before outcomes) or **pending** (needs a later authorized step; the runner must refuse final evaluation while any mandatory field is pending).

## Common study condition

**Primary condition, "native maximum-capability configuration":**
- each model's own documented template or encoder;
- its highest documented reasoning effort, set explicitly;
- its publisher-recommended sampling for single-step, non-agentic use;
- no tools, one turn, a fresh context per item, no study system message;
- identical tasks, prompts and scorers;
- one common output ceiling (pending; see [16](16-frozen-evaluation-protocol.md) §5).

Sampling therefore differs between families, as their publishers document. This is a native-configuration comparison, **not** an equal-compute or identical-token comparison.

## The six configurations

| ID | Checkpoint @ revision | Interface | Effort (explicit) | Sampling | Context | Stop / parse |
|---|---|---|---|---|---|---|
| **P35 (new)** | MiMo-V2.6-Pro-RL @ `73875d00` (the MOPD sibling @ `adea8e2c` is archived; the two share byte-identical config, template and tokenizer_config) | pinned Jinja; one boolean `enable_thinking`, on unless explicitly false | thinking enabled: the native maximum (**no effort levels exist**) | do_sample **true** explicit; T 1.0, top_p 0.95 (card). **generation_config sets do_sample=false and max_new_tokens=2048** | 1,048,576 (no YaRN) | EOS [151643, 151645, 151672]; parser `mimo`; hosted routes return `reasoning_content` |
| ~~P24~~ (superseded) | DeepSeek-V4.1-Flash @ `dba1be0a` | own Python encoder `encoding/encoding.py` (no Jinja) | `100` (int). **Encoder default is `high`=75** (L12-14, L441-449) | T 1.0, top_p 0.95 (README L109 evaluation setting) | 1,048,576 (released YaRN config) | EOS id 1; official parser asserts on missing `</think>`/EOS (L935-968) |
| P25 | DeepSeek-V4-Pro-0813 @ `72e1d323` | own encoder `encoding/encoding_dsv4.py`, not interchangeable with P24's | `max`. **Encoder default is `low`, which adds no effort prompt** (L64-80) | T 1.0, top_p 1.0 (README L134: 1.0 for non-agentic; generation_config) | 1,048,576 | EOS id 1; same parser rules (L703-741) |
| P27 | GLM-5.3-Flash @ `eb9eb208` | pinned Jinja; prefills `<think>` (L259-260) | `max`, validated in the rendered prefix (template maps any unknown value to max, L2-3) | do_sample **true** set explicitly; T 1.0, top_p 0.95 (generation_config has no do_sample) | 1,048,576 | EOS ids [154820, 154827, 154829]: **names pending** (vocabulary not downloaded) |
| P28 | GLM-5.3 @ `aca966e4` | pinned Jinja, same effort/think logic | `max` | as P27 | 1,048,576 | as P27 (pending) |
| P29 | Kimi-K3 @ `f831ab66` | official `encoding_k3.py` (fetched and audited; XTML format; **encode-only, no output parser**) | `max`, passed as the encoder's **`thinking_effort`** keyword (see finding 4) | T 1.0, top_p 0.95 (README L582 single-step); nested Transformers defaults (do_sample false, max_length 20, top_k 50) explicitly overridden | 1,048,576 | EOS 163586 `<\|end_of_msg\|>`; output parser pending (framework parser or fixture-tested study parser) |
| P34 | Qwen3.8-2.4T-A95B @ `207bd685` | pinned Jinja; thinking mandatory (disabling raises, L21-22) | `xhigh` (only xhigh/medium/low accepted, L25-27) | T 1.0, top_p 0.95, top_k 20, min_p 0, presence 0, repetition 1 (README L357) | **262,144 native** (no extension enabled) | EOS [248046 `<\|im_end\|>`, 248044 `<\|endoftext\|>`]; final after `</think>` |

**Precision identities.** These are recorded as native artifacts, never relabelled BF16 because a `dtype` field says bfloat16:
- **P35:** stored MXFP4, computed FP8 e4m3 in 128×128 blocks. The ~524B parameter count shown on Hugging Face counts packed U8 bytes; the model is 1.02T total / 42B active.
- **P24 (superseded):** FP8 blocks with FP4 experts.
- **P25:** FP8 with FP4 experts.
- **P27 and P28:** FP8 (e4m3).
- **P29:** compressed-tensors (the card says MXFP4 weights and MXFP8 activations).
- **P34:** no quantization config in the pinned config.

## Findings that change the configuration

1. **DeepSeek defaults would silently under-configure both models** (V4.1 now superseded; the V4-Pro finding stands, and the hosted API also defaults to `high`, so `max` must be sent). V4-Pro's encoder defaults to `low`, which injects no effort prompt at all. V4.1-Flash defaults to 75, not 100. Both are set explicitly, and the rendered prompt is logged to prove it.
2. **GLM's template turns typos into `max`.** Any effort value other than `low` or `high`, including a mistyped one, becomes `max`. Preflight checks that the rendered prompt contains `Reasoning Effort: Max`.
3. **GLM's generation config omits `do_sample`.** A backend could therefore default to greedy decoding. Sampling is enabled explicitly.
4. **Kimi's effort keyword differs between encoder and API, and its nested config defaults are boilerplate.**
   - The card documents an API field `reasoning_effort`, but the pinned encoder reads **`thinking_effort`**. Without it, the encoder injects no effort message at all (L618-633), so a backend forwarding `reasoning_effort` as a template keyword would silently drop it. The study passes `thinking_effort="max"` and verifies the rendered `thinking-effort` message.
   - The encoder only encodes prompts; it has no output parser (see integration gates).
   - `do_sample=false, max_length=20, top_k=50` are Transformers defaults, overridden by the card's documented recipe.
5. **Qwen's context is binding.** Its publisher recommends 262,144 reasoning plus 131,072 final tokens *within a 1M context*. The study does not enable context extension, so that recommendation is infeasible natively. Qwen's 262,144-token native context sets the upper bound on the common output ceiling.
6. **Publisher recommendations are unmatched, and no universal no-tools recipe exists.**

   | Model | Publisher output recommendation |
   |---|---|
   | DeepSeek-V4-Pro | 384K |
   | DeepSeek-V4.1 | ≥256K |
   | GLM pair | task-specific only (64K / 128K / 163,840) |
   | Qwen | 262K + 131K |

   A common ceiling is a study decision, not a publisher-endorsed setting. Budget censoring is therefore measured and reported, never hidden.
7. **Qwen's benchmark table is for a different product.** The README's table is labelled hosted Qwen3.8-Max, which has extra features; it is not evidence about this released checkpoint.
8. **Single-turn settings are recorded but inert.** `clear_thinking`, `preserve_thinking` and Kimi's preserved-thinking history only affect earlier assistant turns, so they have no effect here. They are set explicitly for reproducibility.
9. **MiMo's generation config would silently cripple it (v2).** `generation_config.json` sets `do_sample=false` and `max_new_tokens=2048`. A backend inheriting it would decode greedily and stop at 2,048 tokens. The card recommends temperature 1.0 and top_p 0.95; the study sets these explicitly.
10. **MiMo's hosted checkpoint identity is unverifiable on Xiaomi's API (v2).**
    - Both the RL and the MOPD model cards list the "Xiaomi MiMo Open Platform API".
    - Xiaomi publishes no snapshot IDs and returns no `system_fingerprint`.
    - The Xiaomi alias is therefore a distinct hosted configuration, **H-MiMo-Xiaomi**, and is never labelled as either checkpoint.
    - DeepInfra states that it serves the RL checkpoint (FP8); the revision needs written confirmation.
    - Because the interface files are identical, the ambiguity concerns the weights only.
11. **Hosted routes change what can be verified (v2).**
    - On server-templated APIs the rendered prompt is invisible. The study logs a request-payload hash, the echoed model ID and any fingerprint instead.
    - Providers parse the reasoning and final channels, which removes the GLM EOS-name and Kimi-parser blockers for the hosted routes. Those blockers remain only for self-hosting.
    - Only the dedicated Qwen route renders prompts client-side from the pinned template. There the rendered-prompt hash is logged; this is tested offline in `runner/test_offline.py`.

## Stop and parse rules (common to all six)

- **Natural stop:** only the documented end-of-turn token counts as a natural stop. A ceiling stop is classified `BUDGET_TRUNCATED` *before* any native parser runs, so a missing `</think>` caused by the cap is never mislabelled as malformed.
- **Reinserted EOS:** if a backend strips the stop token on a natural stop, the runner may re-append it for the official DeepSeek parser. It records the flag `stop_token_reinserted`.
- **Malformed output:** any other parser rejection is `MALFORMED_NATIVE_OUTPUT` and is never repaired.
- **Tool calls:** a tool-call emission in this no-tools study is malformed.

## Integration gates (all pending; required before any final generation)

- **Serving:** each checkpoint is served at the exact revision, with its native encoder or template.
  - DeepSeek's `deepseek-recipe` library may be used only if it is shown byte-identical to the pinned encoder on fixtures.
- **Sampling:** every parameter is honoured and logged, including top_k and min_p where set.
- **Stop tokens:** stop-token semantics are verified. The GLM IDs need to be mapped to token names.
- **Kimi output parser:** the encoder is now fetched, hash-pinned and audited. Still pending: an output parser, either the serving framework's documented Kimi-K3 parser or a strict study-authored one, which must pass synthetic fixtures; and pinned custom-code dependencies.
- **No silent re-quantization:** a different served precision would be a different configuration and must be labelled as such.
- **Context:** no context-extension flag is set for P34.
- **Ceiling:** the terminal output ceiling is computed with each model's tokenizer (see 16 §5).

Hardware, VRAM and cost played no part in any of the above. An unavailable execution route is reported as a missing experiment, never substituted.

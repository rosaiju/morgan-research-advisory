# 19. Readiness, execution routes and calibration plan

> **Stage-1 update (2026-09-29).** The v2 copy of this file is in `manifest/history/2026-09-29_v2/`. Superseded by [20](20-stage1-provider-questions.md) and [21](21-local-validation-report.md):
> - **§2 (Qwen):** the practical route is now **DeepInfra FP4, deviation D2**, with disclosure. You declined GPU rental, so the dedicated FP8 deployment is a reference only. Bitdeer FP8 (D1) is an upgrade if the provider confirms.
> - **§9 (blockers):**
>   - Math-Verify is installed and validated.
>   - Scorer fixtures pass.
>   - The BBEH suffix is verified and corrected.
>   - BBEH now uses the official Mini.
> - **Remaining before the integration test:** accounts, keys and your authorisation. The provider answers can arrive in parallel.
>
> The calibration procedure (§4) is unchanged and has not been run.

September 29, 2026. Preparation only. **No paid request, account, credit, inference or model loading.**

This document follows the user's tentative acceptance of the v2 set (MiMo-V2.6-Pro replacing DeepSeek-V4.1-Flash). The manifests were updated with history preserved: v1 is in `manifest/history/2026-09-29_v1_pre-MiMo/`.

Evidence labels:

| Label | Meaning |
|---|---|
| **[P]** | primary documentation (provider or publisher) |
| **[F]** | pinned file archived and hashed in this package |
| **[S]** | secondary listing (e.g. OpenRouter endpoint JSON) |
| **[A]** | our planning assumption |

## 0. Final six and exact identifiers

| ID | Released checkpoint (pinned) | Recommended route | Route identity status |
|---|---|---|---|
| P35 | `XiaomiMiMo/MiMo-V2.6-Pro-RL` @ `73875d00b30a89ef8cc353a0b60b0e9f9561952d` | DeepInfra `XiaomiMiMo/MiMo-V2.6-Pro` | provider states RL + fp8; revision unconfirmed |
| P25 | `deepseek-ai/DeepSeek-V4-Pro-0813` @ `72e1d3230f6c080a530b0a1d46f8eb4602340597` | DeepSeek `deepseek-v4-pro` | first party maps the alias to V4-Pro-0813 [P] |
| P28 | `zai-org/GLM-5.3` @ `aca966e4e02791568aa6a4ced368624b3d897f42` | Z.ai `glm-5.3` | first party; byte-identity not stated |
| P27 | `zai-org/GLM-5.3-Flash` @ `eb9eb208eb0d988989d07a6a12d0fdeb5f52574a` | Z.ai `glm-5.3-flash` (not `flashx`) | first party; byte-identity not stated |
| P29 | `moonshotai/Kimi-K3` @ `f831ab66814297da540d832a5235f8e904f29d06` | Moonshot `kimi-k3` | first party; byte-identity not stated |
| P34 | `Qwen/Qwen3.8-2.4T-A95B` @ `207bd685a7e3696cfaff12ded7c6a7ea0f88c996` (BF16) | dedicated vLLM deployment of `Qwen/Qwen3.8-2.4T-A95B-FP8` @ `d2dc35658bcf77e66643428cb52e774cc3b5bd29` | exact files pinned by us; publisher's FP8 release |

## 1. MiMo: can Xiaomi's `mimo-v2.6-pro` be verified as RL or MOPD?

**No. Xiaomi's API alias is therefore documented as a distinct hosted configuration, "H-MiMo-Xiaomi".**

**Evidence:**
- Both model cards claim the same API [P]:
  - The RL card (@`73875d00`) says it is "also available in … Xiaomi MiMo Open Platform API".
  - The MOPD card (@`adea8e2c`, "the MOPD upgrade of the MiMo-V2.6-Pro-RL checkpoint") makes the same claim.
  - Both cannot describe one alias at the same time.
- No versioning [P]:
  - Xiaomi's changelog has one V2.6 entry (2026-09-22), with no snapshot IDs and no mention of MOPD.
  - The API response returns `id`, `model` and `created` only, with no `system_fingerprint`.
- Independent evaluation [P]: AA's page links the RL checkpoint and says it used Xiaomi's API. That was not confirmed as RL on the day of evaluation, and MOPD appeared five days later.
- DeepInfra's model page states it serves "MiMo-V2.6-Pro-RL" at fp8 [P]. OpenRouter lists it with a max completion of 943,718 and supports seed, top_k and min_p [S].
- The RL and MOPD interface files are byte-identical: config, generation_config, chat_template, tokenizer_config and configuration code [F]. The ambiguity is purely about **which weights** are served.
- Xiaomi's API adds a non-native intervention: finish reason `repetition_truncation`. It also forces temperature 1.0 and top_p 0.95 in thinking mode, which equal the card's recommendation.

**Recommendation:**
- **Primary: `P35-deepinfra`,** conditional on DeepInfra confirming in writing:
  1. revision `73875d00`;
  2. whether "fp8" means the native MXFP4-stored / FP8-computed weights or a re-quantization;
  3. that `chat_template_kwargs.enable_thinking` is honoured and reasoning is returned separately;
  4. that the max tokens limit includes reasoning.
- **If DeepInfra cannot confirm:** use `P35-xiaomi` and report every result as "H-MiMo-Xiaomi (Xiaomi API `mimo-v2.6-pro`, run dates …)", not as MiMo-V2.6-Pro-RL.

## 2. Qwen3.8-2.4T-A95B: route comparison

Native facts [F]:
- the BF16 checkpoint;
- `max_position_embeddings` 262,144 with `rope_type` default;
- template effort vocabulary `xhigh` / `medium` / `low`;
- sampling 1.0 / 0.95 / top_k 20 / min_p 0.

The vLLM recipe [P] states that context beyond 262K requires YaRN, via `VLLM_ALLOW_LONG_MAX_MODEL_LEN`. **Any endpoint advertising ~1M context is therefore running an extended configuration.**

| Route | Checkpoint identity | Native context? | Precision documented? | Controls | Provider identity | Verdict |
|---|---|---|---|---|---|---|
| **Dedicated vLLM, Qwen FP8 release** (16× B300 / 16× MI355X / 32× H200) | exact repo + SHA pinned by us; publisher-made FP8; template, generation config and tokenizer config byte-identical to BF16 [F] | **yes** (`--max-model-len 262144`, no YaRN) | **yes** (FP8 e4m3 128×128, dynamic activations) [F] | full: client-rendered prompt (hash verifiable), top_k, min_p, seed, raw stop token | study-controlled | **Recommended (most reproducible)**; needs a separate GPU authorisation |
| DeepInfra `Qwen/Qwen3.8-2.4T-A95B` (serverless) | named; which FP4 weights is unstated | **yes** (262,144) [S] | **FP4** [P][S], below native | top_k, min_p, seed [S]; effort vocabulary none/low/medium/high **lacks xhigh**, so `chat_template_kwargs` must be confirmed | stable single provider | **Fallback**, labelled "FP4 configuration" |
| Alibaba Model Studio `qwen3.8-2.4t-a95b` | first party, names the open release | **no** (1M; 983,616 input in thinking mode) | no | `thinking_budget` forces an answer when exceeded; default ambiguous (4,000 in the console); `reasoning_effort` for this model undocumented; output 131,072 plus separate CoT 131,072 | stable | not recommended |
| Together `Qwen/Qwen3.8-2.4T-A95B` | page calls it "Qwen3.8 Max"; effort levels low/high/xhigh ≠ template | no (1.01M; 909K completion) [S] | no | top_k, min_p | stable | not recommended |
| Novita, SiliconFlow (fp8), Modal | named | no (~1M) [S] | only SiliconFlow (fp8) | varies | stable | not recommended |
| Venice | named | yes (262,144) | no | 65,536 max completion (below the ceiling) | stable | not recommended |
| Fireworks | library model, dedicated on-demand only (serverless not supported) | 262K | not stated | — | — | possible host for the dedicated route |

**Recommendation:** use `P34-dedicated-fp8`.
- **Why it wins:** it is the only route that satisfies all four of the user's criteria:
  - exact identity;
  - native context;
  - documented precision;
  - stable, study-controlled provider.
- **It is also the only route where the rendered prompt can be verified.** The offline test renders the pinned template and confirms the `<think>` prefill and the xhigh instruction.
- **Cost:** see §5.
- **Disclosure:** FP8 is the publisher's own quantized release, not the BF16 original. BF16 would need 24× B300, about 1.5× the GPU cost.
- **If the dedicated deployment is not authorised:** use `P34-deepinfra-fp4`, disclosed as a quantized configuration below native precision.

## 3. Output limits: generated tokens, not context

| Route | Context window | **Max generated tokens per request** | Reasoning counted in that limit? | Source |
|---|---|---|---|---|
| P35 DeepInfra | 1,048,576 | 943,718 | undocumented | [S] OpenRouter endpoint listing |
| P35 Xiaomi (H-MiMo-Xiaomi) | 1,048,576 | **131,072** (`max_completion_tokens` range 1–131,072) | **yes**, explicit | [P] |
| P25 DeepSeek | 1M | **393,216** (default 128K at max effort; 64K otherwise) | "tokens that can be generated"; reasoning reported inside completion details | [P] |
| P28 / P27 Z.ai | 1M | **131,072** (`max_tokens` 1–131,072) | **undocumented** | [P] |
| P29 Moonshot | 1,048,576 | **1,048,576** (default 131,072) | **yes** (counts toward completion_tokens) | [P] |
| P34 dedicated FP8 | 262,144 | 262,144 − prompt (engine setting) | yes | [F]/engine |
| P34 DeepInfra FP4 | 262,144 | 131,072 | undocumented | [S] |
| (not recommended) Alibaba Qwen | 1,000,000 | 131,072 output + 131,072 chain of thought (separate) | no (separate budgets) | [P] |

**Conclusion:** the largest **common** generated-token ceiling the recommended routes can support is **131,072**. It is binding on Z.ai, and on Xiaomi if that route is used. It is **not approved yet.** Two tests must pass first:
- **T1:** every route accepts `131072` as its output-limit parameter.
- **T2:** Z.ai's `max_tokens` bounds reasoning plus final tokens.

If T2 shows that reasoning is not counted, GLM's generated length cannot be capped server-side, and you must choose before calibration:
1. a client-side cut-off at C, counted from streamed usage (imperfect); or
2. a different GLM route; or
3. accept an uncapped GLM (breaks the common-ceiling design).

## 4. Development calibration procedure (pre-registered; `evaluation.json` → `budget_policy.development_calibration`)

1. **Run:** 216 development items × 6 models = 1,296 requests at **C_dev = 131,072**. One generation each, all models within one short window, at most 8 in flight per route.
2. **Record per attempt:**
   - generated tokens, and reasoning tokens where reported;
   - finish reason;
   - status and flags.
3. **Report per model and benchmark:**
   - token distribution (median, p90, p95, p99, max);
   - truncation at C_dev with Wilson bounds;
   - loops;
   - provider interventions;
   - infrastructure and filtered counts.
4. **Choose C_final:** the smallest L in **{65,536, 98,304, 131,072}** such that, for **every** model, **D_m(L) ≤ 2 overall and ≤ 1 per benchmark**.
   - **D_m(L):** the count of attempts that ended naturally within C_dev but used more than L tokens, i.e. the extra censoring that L would cause. D_m(L) ≤ 2 of 216 is ≤0.9%, with a Wilson 95% upper bound of 3.3%.
   - **Loops:** outputs already truncated at C_dev are censored at every L and do not count.
   - **Floor:** 65,536 keeps the 64K sensitivity analysis possible.
5. **Adequacy check:** truncation at C_dev ≤ 5% per model. A model that fails is labelled "budget-censored at the maximum valid common ceiling". There is no per-model ceiling.
6. **Freeze:** write C_final, the D-table and the development-summary hash into `evaluation.json`, and set `calibrated=true`, **before any final request.**
   - **Excluded from the decision:** development accuracy, cost and runtime.
   - **Sensitivity analyses** at 8K, 16K, 32K and 64K are computed afterwards from the final generations.

## 5. Cost scenarios by common ceiling (planning, not a protocol input)

**Model** (`manifest/planning/cost_model_v2.py`):
- **Output lengths [A]:** lognormal per benchmark, truncated at the ceiling. Central medians are 2.7K for MMLU-Pro, 3.3K for MATH, 10K for BBEH and 1.3K for IFEval.
- **Loops [A]:** a probability of 0.3% (low), 1% (central) or 3% (high) that an attempt loops to the ceiling.
- **Verbosity [I]:** per-model multipliers from AA.
- **Prices [P]:** first-party list prices. Kimi uses the upper $15 output price; Qwen uses the serverless $6.

This v2 model is more conservative than doc 18's point estimates because loops now run to the ceiling.

Totals in USD for all six models, low / central / high, with the modelled mean censored share in brackets:

| Common ceiling | Development (1,296 req) | Final (7,680 req) | Dev + final | Censoring, final (central) |
|---|---|---|---|---|
| 8,192 | 18 / 30 / 41 | 123 / 191 / 253 | **141 / 221 / 294** | 32% (scientifically unusable) |
| 16,384 | 20 / 38 / 63 | 143 / 257 / 398 | **163 / 295 / 461** | 15% |
| 32,768 | 21 / 45 / 86 | 153 / 315 / 570 | **174 / 360 / 656** | 6.1% |
| 65,536 | 22 / 50 / 109 | 160 / 358 / 750 | **182 / 408 / 859** | 2.3% |
| 98,304 | 23 / 53 / 123 | 164 / 380 / 855 | **187 / 433 / 978** | 1.5% |
| **131,072** (largest supported common value) | 24 / 56 / 133 | 168 / 396 / 930 | **192 / 452 / 1,063** | 1.2% |
| IFEval (optional, at 131,072) | — | 22 / 55 / 157 | — | — |

**By model, final set at 131,072** (low / central / high):

| Model | Cost |
|---|---|
| Kimi-K3 | $82 / $196 / $465 |
| Qwen (serverless) | $36 / $84 / $196 |
| GLM-5.3 | $31 / $72 / $164 |
| DeepSeek-V4-Pro | $11 / $26 / $62 (off-peak) |
| MiMo-V2.6-Pro | $5 / $11 / $25 |
| GLM-5.3-Flash | $3 / $7 / $17 |

**Dedicated Qwen FP8 route instead of serverless Qwen** [A]:
- **Assumptions:** 16 GPUs at $5–9 per GPU-hour, 1,500–4,000 tokens/s aggregate, plus 3 h for provisioning and weight loading.
- **Qwen dev + final:** $275–$1,416 (central about $330–$840), in about 4–10 h of deployment time.
- **Complete dev + final at 131,072:** about **$426 / ~$884 / $2,255** (low / central / high).
- **Comparison:** the serverless FP4 fallback gives about **$192 / $452 / $1,063**.

**Runtime at 131,072:**
- **Final evaluation:** about 11 h wall-clock central (4–27 h) at 8 concurrent requests per route with all six running in parallel. Kimi at about 39 tokens/s is the slowest.
- **Development calibration:** about 1.6 h central.

Cost alone does not change the protocol. The calibration rule decides C.

## 6. Exact request counts

- **Final items per model:** 1,280 unique questions, verified: MMLU-Pro 420 + MATH-500 400 + BBEH-sampled 460.

| Stage | Requests |
|---|---|
| Integration test (first paid test) | **34** (+6 dedicated Qwen, +4 Xiaomi MiMo only if used) |
| Development calibration | **1,296** |
| Final capability evaluation | **7,680** (MMLU-Pro 2,520, MATH-500 2,400, BBEH 2,760) |
| IFEval diagnostic (separate strand) | **3,246** |
| Repetitions | **0** |
| Infrastructure reruns | at most 2 per failed attempt (expected under 2%) |
| **Totals** | dev + final **8,976**; with IFEval **12,222**; with integration **12,256** |

## 7. Adapter architecture (built; offline-tested; network gated)

```
runner/
  routes.json            one entry per route: env-var names, model string, fixed study parameters,
                         output-limit parameter and documented maximum, identity/precision status, prices
  adapters.py            build_request (pure) -> payload_sha256 -> Transport.send (gated) -> parse_sse ->
                         normalise; render_qwen_prompt (pinned Jinja, dedicated route); estimated_cost; redact
  status.py              finish-reason -> status precedence and flags (no answer key access)
  integration_plan.json  the 34 synthetic requests of the first paid test, with pass criteria
  test_offline.py        14 offline tests (all pass)
  secret_scan.py         credential scan (clean)
  .env.example           variable NAMES only; .gitignore excludes .env, AUTHORIZATION.json, runs/
```

**Two locks are required before anything is sent:**
1. **Environment:** `MORGAN_ALLOW_NETWORK=1`.
2. **Authorisation file:** a user-written `runner/AUTHORIZATION.json` with the fields
   `{"stage", "routes", "max_usd", "max_requests", "authorized_by", "date"}`.

**Keys:**
- They are read from environment variables only inside `Transport.send`.
- They never enter payloads, hashes, records or logs.

**Scoring stays separate:** a separate scorer, not yet built, is the only component that reads answer keys.

## 8. Exactly what the first paid integration test would do

**Prerequisites (you):**
1. Create accounts and keys at DeepInfra, DeepSeek, Z.ai and Moonshot.
2. Put the keys in environment variables.
3. Write `runner/AUTHORIZATION.json`: stage `integration`, the six route IDs below, `max_usd` 15 and `max_requests` 34.
4. Set `MORGAN_ALLOW_NETWORK=1`.

**Requests (34 in total, synthetic prompts only, no benchmark or development items):**
- **Prompts:** two synthetic items, "What is 17 + 25?" and a chickens-and-cows puzzle.
- **Tests, per route:**
  - **T1:** the arithmetic prompt at an output limit of **131,072**. Proves the route accepts that limit. Also checks a natural stop, separated reasoning, usage fields and the model echo.
  - **T2:** the same prompt at a limit of **16**. It must end with `length`. Whether the truncation happened inside reasoning, and whether completion tokens stayed at 16 or fewer, shows if the limit counts reasoning. This is **the GLM question.**
  - **T3a / T3b:** the puzzle at maximum and at low effort, with a limit of 32,768. Records whether the effort parameter changes reasoning length. This is weak evidence, recorded rather than pass/fail, unless the API rejects the parameter.
  - **T4:** the invalid effort `"maxx"`. Records whether the server validates effort.
  - **T5:** T1 repeated with an identical payload. Records determinism; determinism is not required.
- **Routes and counts:**

  | Route | Requests |
  |---|---|
  | `P35-deepinfra` | 4 (T1, T2, T3a, T5; MiMo has no effort levels) |
  | `P25-deepseek` | 6 |
  | `P28-zai` | 6 |
  | `P27-zai` | 6 |
  | `P29-moonshot` | 6 |
  | `P34-deepinfra-fp4` | 6 (so the fallback Qwen route is validated even before any GPU decision) |

**Spend:**
- **Expected:** under $1.
- **Worst case:** about $12, if every 131,072-token request runs to the cap.
- **Hard cap:** $15, enforced in the authorisation file and in the provider consoles.

**Outputs:**
- a per-request JSONL log (no keys);
- a pass/fail table per route;
- the T2 verdict for each route;
- a secret scan.

**Pass rule:**
- Every route must pass T1, T2 and T3a.
- Any failure blocks development calibration for that route.
- The GLM T2 result settles C_max or triggers the decision in §3.

**Not part of this test:** the dedicated Qwen deployment and the Xiaomi MiMo route. Each needs its own authorisation.

## 9. Remaining blockers and recommended authorisation sequence

1. **Stage 1 (no spend):** send written questions to DeepInfra (MiMo revision and precision, Qwen FP4 source, `max_tokens` semantics, `chat_template_kwargs`), Z.ai (whether `max_tokens` includes reasoning; served precision) and Moonshot, DeepSeek and Xiaomi (served precision). I can draft the questions.
2. **Integration test:** 34 requests, $15 cap.
3. **Qwen route decision:**
   - either authorise a dedicated FP8 deployment: choose a GPU host, pin a vLLM version, planning cost $275–$1,400;
   - or accept the FP4 fallback with disclosure.
4. **Scorer build:** install Math-Verify and pass the scorer fixture suites (local, no model). Resolve the BBEH suffix provenance.
5. **Development calibration:** 1,296 requests at C_dev, cap about $150 (serverless) plus Qwen deployment hours if dedicated. Then freeze C_final.
6. **Final evaluation:** 7,680 requests. **IFEval:** 3,246 requests, optional, separate. Then scoring and statistics.

## 10. Sources (read 2026-09-29)

- **MiMo:**
  - [RL card](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-RL) and [MOPD card](https://huggingface.co/XiaomiMiMo/MiMo-V2.6-Pro-MOPD) (files archived and hashed);
  - [Xiaomi changelog](https://mimo.mi.com/docs/en-US/updates/model);
  - [Xiaomi OpenAI-compatible API](https://mimo.mi.com/docs/en-US/api/chat/openai-api);
  - [Xiaomi model page](https://mimo.mi.com/models/en-US/mimo-v2.6-pro);
  - [DeepInfra MiMo](https://deepinfra.com/XiaomiMiMo/MiMo-V2.6-Pro);
  - [OpenRouter MiMo endpoints](https://openrouter.ai/api/v1/models/xiaomi/mimo-v2.6-pro/endpoints).
- **Qwen:**
  - [vLLM Qwen recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-2.4T-A95B);
  - [Qwen FP8 repo](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B-FP8) (files archived);
  - [Alibaba model page](https://docs.modelstudio.console.alibabacloud.com/en/model-studio/qwen3-8-2-4t-a95b);
  - [Alibaba deep thinking](https://www.alibabacloud.com/help/en/model-studio/deep-thinking);
  - [DeepInfra Qwen](https://deepinfra.com/Qwen/Qwen3.8-2.4T-A95B);
  - [Together Qwen](https://www.together.ai/models/qwen3-8-max);
  - [Fireworks Qwen](https://fireworks.ai/models/fireworks/qwen3p8-2p4t-a95b);
  - [OpenRouter Qwen endpoints](https://openrouter.ai/api/v1/models/qwen/qwen3.8-2.4t-a95b/endpoints).
- **DeepInfra:**
  - [reasoning](https://docs.deepinfra.com/chat/reasoning.md);
  - [rate limits](https://docs.deepinfra.com/account/rate-limits.md);
  - [custom LLMs](https://docs.deepinfra.com/private-models/custom-llms.md) (4-GPU default limit: cannot host this Qwen).
- **Other first-party APIs:**
  - [DeepSeek chat API](https://api-docs.deepseek.com/api/create-chat-completion);
  - [Z.ai chat API](https://docs.z.ai/api-reference/llm/chat-completion);
  - [Z.ai thinking](https://docs.z.ai/guides/capabilities/thinking);
  - [Moonshot chat API](https://platform.kimi.ai/docs/api/chat);
  - [Kimi-K3 quickstart](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart).

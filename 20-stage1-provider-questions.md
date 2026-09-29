# 20. Stage 1: provider questions and practical Qwen route

September 29, 2026. **Stage 1 (no-cost) approved by the user.** These questions are **drafts for the user to send**. Nothing has been sent, no account created, no API called.

Each question states the protocol decision its answer settles. Provider names and URLs are as documented on 2026-09-29.

**Where to send them:**
- **DeepInfra, Z.ai and Bitdeer:** these questions block the integration test and route selection. Send these three first.
- **Xiaomi, DeepSeek and Moonshot:** improve disclosure but do not block the integration test.

---

## 1. DeepInfra (support / sales); blocks P35 and P34 route selection

> Subject: Model identity and serving configuration for XiaomiMiMo/MiMo-V2.6-Pro and Qwen/Qwen3.8-2.4T-A95B (research evaluation)
>
> We are preparing a documented academic benchmark and must report the exact serving configuration of each endpoint. Could you confirm the following?
>
> **MiMo-V2.6-Pro (`XiaomiMiMo/MiMo-V2.6-Pro`)**
> 1. Which Hugging Face checkpoint and revision are served: `XiaomiMiMo/MiMo-V2.6-Pro-RL` @ `73875d00b30a89ef8cc353a0b60b0e9f9561952d`, `XiaomiMiMo/MiMo-V2.6-Pro-MOPD` @ `adea8e2c5373181e5a973fa1ecb343cb31af214b`, or another revision? Will you notify users (or change the model name) if the served checkpoint changes?
> 2. Your model page lists "fp8". The released checkpoint stores weights as MXFP4 and computes in FP8 (e4m3, 128×128 blocks; `quantization_config` `store_dtype: mxfp4`). Do you serve these released weights unchanged, or did you re-quantize them? If re-quantized, from which source and with which method?
> 3. Which chat template is applied: the one in the released repository (`chat_template.jinja`, thinking controlled by `enable_thinking`, default on)? Is `chat_template_kwargs: {"enable_thinking": true}` honoured?
> 4. Is the reasoning returned separately (`reasoning_content`), and does `usage` report reasoning tokens?
> 5. Does `max_tokens` bound the **total generated tokens including reasoning**? What is the maximum accepted `max_tokens` for this model (we plan 131,072)?
> 6. Are `temperature`, `top_p`, `top_k`, `min_p` and `seed` honoured exactly as sent? Is any server-side repetition or loop truncation applied?
>
> **Qwen3.8-2.4T-A95B (`Qwen/Qwen3.8-2.4T-A95B`)**
>
> 7. Your listing says "fp4". Which weights are served: `nvidia/Qwen3.8-2.4T-A95B-NVFP4`, `Inferact/…-NVFP4`, `Inferact/…-MXFP4`, `RedHatAI/…-NVFP4`, `amd/…-Quark-MXFP4`, your own quantization, or something else? Please give the repository and revision, or the quantization method and calibration data.
> 8. Is the context served at the native 262,144 tokens **without** YaRN/rope-scaling (no `VLLM_ALLOW_LONG_MAX_MODEL_LEN` or rope-scaling override)?
> 9. Is the chat template from `Qwen/Qwen3.8-2.4T-A95B` @ `207bd685a7e3696cfaff12ded7c6a7ea0f88c996` used unchanged? Its effort vocabulary is `xhigh` / `medium` / `low`, while your reasoning docs list `none` / `low` / `medium` / `high`.
>    - How should we request the template's `xhigh` level: `chat_template_kwargs: {"reasoning_effort": "xhigh"}`, or `reasoning_effort: "xhigh"`?
>    - What does your `reasoning_effort: "high"` map to for this model?
> 10. Are `top_k=20` and `min_p=0` honoured? Is `seed` honoured?
> 11. Is reasoning returned as `reasoning_content`, and does `max_tokens` (maximum?) include reasoning tokens?
> 12. Which inference engine and version serve the model? Will you notify users of weight, quantization or engine changes?
> 13. **Only if convenient:** do you plan an FP8 (Qwen's official `Qwen/Qwen3.8-2.4T-A95B-FP8`) or BF16 serverless endpoint?
>
> **General**
>
> 14. Default concurrency is documented as 200 requests per model. Is there any per-request limit on generation time for long (≥100K-token) streaming outputs?

**What the answers decide:**
- **Q1–Q6:** whether P35 results may be labelled "MiMo-V2.6-Pro-RL", or must be reported as H-MiMo-Xiaomi.
- **Q7–Q12:** the exact disclosure for the P34 practical route (§3).
- **Q5/Q11:** whether the integration test is expected to find that the common ceiling includes reasoning on DeepInfra.

## 2. Z.ai (API support); blocks the common output ceiling

> Subject: Does `max_tokens` include reasoning tokens for glm-5.3 and glm-5.3-flash?
>
> For a research benchmark we need a common limit on the **total number of generated tokens (reasoning + answer)** per request.
> 1. For `glm-5.3` and `glm-5.3-flash` with `thinking: {"type": "enabled"}` and `reasoning_effort: "max"`, does `max_tokens` (maximum 131,072) limit **reasoning plus final answer together**, or only the final answer?
> 2. If only the final answer: is there a parameter that caps reasoning, or total generated tokens? What is the maximum reasoning length at `reasoning_effort: "max"`?
> 3. When the limit is reached during reasoning, what `finish_reason` is returned (`length`?), and is partial `reasoning_content` returned?
> 4. Does `usage.completion_tokens` include reasoning tokens? Is a reasoning-token count available?
> 5. Which weights are served: identical to `zai-org/GLM-5.3` @ `aca966e4e02791568aa6a4ced368624b3d897f42` and `zai-org/GLM-5.3-Flash` @ `eb9eb208eb0d988989d07a6a12d0fdeb5f52574a`? At what precision (the releases are FP8)?
> 6. Does `reasoning_effort: "max"` produce the same prompt as the released chat template's `Reasoning Effort: Max` system prefix? Is an invalid value rejected or silently mapped?
> 7. Are `do_sample: true`, `temperature: 1.0` and `top_p: 0.95` honoured in thinking mode? Is `seed` supported?
> 8. What concurrency and rate limits apply to a new account, and will you announce changes to the model behind `glm-5.3` / `glm-5.3-flash`?

**What the answers decide:**
- **Q1–Q3:** whether C_max = 131,072 is enforceable on GLM (19 §3). The integration test T2 also checks this empirically; a written answer lets us predict it.
- **Q5–Q7:** identity and sampling disclosure.

## 3. Qwen3.8-2.4T-A95B: practical route and smallest acceptable deviation

**No investigated hosted endpoint reproduces the released checkpoint exactly.** Every serverless option deviates in precision, in context length, or both. The deviations, ranked from smallest to largest:

| Class | Precision | Context | Template and controls | Available routes (2026-09-29) | Acceptable? |
|---|---|---|---|---|---|
| **D0** exact | BF16 released weights | native 262,144 | released template | self-hosted only (24× B300) | reference; not practical |
| **D1** | **Qwen's own FP8 release** (`…-FP8` @ `d2dc3565`; template and configs byte-identical to BF16; Qwen reports near-identical quality) | native 262,144 | released template | dedicated deployment (GPU rental, **not authorised**); Bitdeer FP8 serverless (**unconfirmed**; no public documentation) | **yes: smallest acceptable deviation** |
| **D2** | **third-party 4-bit** (NVFP4/MXFP4 by NVIDIA, Inferact, AMD, RedHat or the provider) | native 262,144 | template to confirm | **DeepInfra (FP4, documented)**; DigitalOcean (reported NVFP4; context unclear) | **yes, with explicit disclosure** (a different configuration of the same checkpoint) |
| **D3** | unknown | **extended to ~1M (YaRN)** | provider-specific (Alibaba `thinking_budget` forces an answer; effort vocabulary unclear) | Alibaba, Novita, SiliconFlow, Modal, Together | **no:** changes model computation on every input and adds provider interventions |

**Why D3 is worse than D2:** static rope scaling alters the positional computation for *all* sequence lengths, not only long ones. Alibaba's thinking-budget cut-off also changes the reasoning process itself. A 4-bit weight quantization of the same model at native context is a smaller, better-characterised deviation.

**Recommended practical route:**
1. **Now:** `P34-deepinfra-fp4` (class D2). It is documented, directly accessible, native context, supports top_k, min_p and seed, and has a stable single provider. It is included in the integration test.
2. **Upgrade to D1** if Bitdeer confirms the §4 questions (Qwen's own FP8 release, native context, released template). Otherwise D1 is reserved for a later dedicated-deployment replication, if you ever authorise GPU rental.

**Disclosure text** (for every table and the methods section, filled from the provider's answers):

> "Qwen3.8-2.4T-A95B (released BF16 checkpoint `Qwen/Qwen3.8-2.4T-A95B` @ `207bd685`) was evaluated through DeepInfra's serverless API, which serves a 4-bit (FP4) quantization [source: `<repo@revision or method from DeepInfra>`] at the native 262,144-token context without context extension, using the released chat template with `reasoning_effort=xhigh` [as confirmed by the provider]. All other models were served at their publishers' native precision (FP8 or MXFP4 formats). Results for Qwen therefore describe this quantized serving configuration; they are not a measurement of the BF16 weights. Precision effects are not separately estimated."

A precision-sensitivity replication at D1 is listed as future work. No claim is made that FP4 is lossless.

## 4. Bitdeer AI; optional, decides the D1 serverless upgrade for P34

> Subject: Qwen3.8-2.4T-A95B FP8 serverless endpoint: configuration details
>
> Artificial Analysis lists a Bitdeer AI endpoint for Qwen3.8-2.4T-A95B tagged FP8 with 262K context. For a documented research benchmark, could you confirm:
> 1. The API base URL, model ID, and public documentation page.
> 2. Whether the served weights are Qwen's official `Qwen/Qwen3.8-2.4T-A95B-FP8` (revision?) or another quantization.
> 3. Native 262,144 context without YaRN or rope-scaling overrides.
> 4. The chat template used, and how to set `reasoning_effort` to `xhigh`. Is reasoning returned separately (`reasoning_content`)?
> 5. The maximum `max_tokens`, and whether it includes reasoning tokens (we need 131,072 total).
> 6. Support for `top_k`, `min_p` and `seed`; inference engine and version; rate and concurrency limits; pricing; and whether you notify customers of model or engine changes.

## 5. Xiaomi MiMo Open Platform; needed only if P35 must fall back to the Xiaomi API

> 1. Which weights serve `mimo-v2.6-pro` today: `MiMo-V2.6-Pro-RL` @ `73875d00`, `MiMo-V2.6-Pro-MOPD` @ `adea8e2c`, or another checkpoint? On which date did any switch occur? Are dated snapshot model IDs available?
> 2. Served precision: the released MXFP4-stored / FP8-computed format, or other?
> 3. `finish_reason: "repetition_truncation"`: under what rule is it triggered, and can it be disabled for evaluation requests?
> 4. Does `max_completion_tokens` (maximum 131,072) include reasoning tokens? The documentation says yes; please confirm this also applies with `thinking: enabled`.

## 6. DeepSeek and Moonshot; disclosure only (do not block the integration test)

**DeepSeek:**
1. Does `deepseek-v4-pro` serve `DeepSeek-V4-Pro-0813` weights at their released precision (FP8 with FP4 experts)?
2. In thinking mode temperature has no effect: what fixed temperature is used?
3. Is `top_p: 1.0` honoured?
4. Does `max_tokens` (maximum 393,216) include reasoning tokens?

**Moonshot:**
1. Does `kimi-k3` serve the released `moonshotai/Kimi-K3` @ `f831ab66` weights at their released precision (MXFP4 weights, MXFP8 activations)?
2. Is API `reasoning_effort: "max"` identical to the encoder's `thinking_effort="max"` system message?
3. Which account tier supports 8 concurrent streaming requests with outputs up to 131,072 tokens?
4. Current price per 1M output tokens for `kimi-k3`? Public sources differ ($12 vs $15).

## 8. What the user does personally to provide API access (only when authorising the integration test)

1. **Create four accounts:**
   - DeepInfra (deepinfra.com): P35 MiMo and P34 Qwen;
   - DeepSeek Platform (platform.deepseek.com): P25;
   - Z.ai (z.ai, API platform): P27 and P28;
   - Moonshot / Kimi Platform (platform.kimi.ai): P29.

   No Xiaomi, Bitdeer or Alibaba account is needed for the integration test.
2. **Add the smallest prepaid credit each platform allows,** and set a **spend limit or alert** in each console if one is offered. The integration test needs under $1 in total ($15 hard cap). DeepInfra is post-paid on a card, so set its spending limit.
3. **Create one API key per platform.** Store keys only as Windows user environment variables, never in any file in this folder, chat or document. In PowerShell, typing each value at the prompt:
   ```powershell
   [Environment]::SetEnvironmentVariable("DEEPINFRA_API_KEY", (Read-Host "DeepInfra key"), "User")
   [Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY",  (Read-Host "DeepSeek key"),  "User")
   [Environment]::SetEnvironmentVariable("ZAI_API_KEY",       (Read-Host "Z.ai key"),      "User")
   [Environment]::SetEnvironmentVariable("MOONSHOT_API_KEY",  (Read-Host "Moonshot key"),  "User")
   ```
   Then open a new terminal. **Do not paste keys into the Claude session.**
4. **Tell Claude "integration test authorised".** Claude then writes `runner/AUTHORIZATION.json`, with:
   - stage `integration`;
   - the 6 route IDs;
   - `max_usd` 15 and `max_requests` 34;
   - your name and the date.

   Or write the file yourself using the template in `runner/README.md`.
5. **Enable the network gate for that terminal session only:** `$env:MORGAN_ALLOW_NETWORK = "1"`.
6. **Optional, in parallel:** send the §1, §2 and §4 questions from your own email (and §5/§6 if you want complete disclosure). Then forward the answers.

## 9. After answers arrive

1. Record each answer verbatim, with its date, in `runner/routes.json` (`checkpoint_identity`, `precision`, `route_max_output`).
2. Set each field's status from `verify` to `confirmed-provider` or `undisclosed`.
3. Then re-run `runner/test_offline.py` and the audit (17).

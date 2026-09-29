# 18. Final candidate audit and hosted-execution plan

> **Status (2026-09-29):** the user tentatively accepted the §5 set, and the manifests were updated to v2. Parts of §6–§7 are superseded by [19](19-readiness-and-calibration-plan.md):
> - **MiMo route:** DeepInfra is recommended. The Xiaomi alias is a distinct configuration.
> - **Qwen route:** a dedicated FP8 deployment is recommended.
> - **Output ceiling:** 131,072 is verified against *generated-token* limits and is still pending test T2.
> - **Costs:** re-modelled with loops running to the ceiling.

September 29, 2026. **Proposed for decision. Nothing executed:** no inference, no benchmark request, no model loading, no weight or tokenizer download, no account, credit or paid resource.

This document:
- audits the candidate set against MiMo-V2.6-Pro and any other current challenger;
- sets out a hosted execution route per model, with costs, runtimes and the stage gates.

It does **not** rewrite 15/16/17 or the JSON manifests. §9 lists exactly what would change if the proposed set is accepted.

Evidence labels used in this document:

| Label | Meaning |
|---|---|
| **[I]** | Independent: Artificial Analysis Intelligence Index v4.3.2 pages, read 2026-09-29 |
| **[P]** | Publisher (model card, API docs) |
| **[S]** | Secondary press or aggregator; used only where noted, never decisive |
| **[A]** | Our own planning assumption |

## 1. Why this audit was needed

**MiMo-V2.6-Pro was missing from our candidate pool.** It was released on 2026-09-22 with open weights (MIT), and the 34-model registry in 12/14 did not contain it. That is a discovery omission, and this audit corrects it.

**The two DeepSeeks were kept for a reason that doesn't hold.** Doc 14 kept DeepSeek-V4.1-Flash and V4-Pro-0813 because "their capability tradeoff is unresolved". The re-examination in §3 finds that, for *no-tools reasoning*, the tradeoff is largely resolved by both publisher and independent evidence.

## 2. Evidence used and its limits

**Why components, not the headline index:** the AA Intelligence Index v4.3.2 combines 10 evaluations, and five are agentic, tool or document-work tasks outside our research question: AA-Briefcase, GDPval-AA, AutomationBench-AA, Terminal-Bench 4.0 and GDP.pdf.

**The five components used** (each run at the model's max effort on its first-party API):
- Humanity's Last Exam (HLE);
- CritPt (frontier physics reasoning);
- SciCode;
- AA-Omniscience (knowledge accuracy net of hallucination);
- AA-LCR (long-context reasoning).

| Model (AA endpoint) | Index | HLE | CritPt | SciCode | Omniscience | LCR | Output tokens to run the index |
|---|---|---|---|---|---|---|---|
| **MiMo-V2.6-Pro** (Xiaomi API) | **46** | **49** | **27** | **61** | 8 | 86 | 144M |
| GLM-5.3 (max) | 45 | 42 | 19 | 59 | 14 | 80 | 209M |
| Kimi-K3 (max) | 44 | 47 | 23 | 59 | **20** | **89** | 161M |
| GLM-5.3-Flash | 42 | 40 | 15 | 52 | 7 | 80 | 181M |
| Qwen3.8-2.4T-A95B (released checkpoint) | 40 | 42 | 20 | 54 | 4 | 80 | 172M |
| DeepSeek-V4.1-Flash (max) | 39 | **39** (lowest) | **14** (lowest) | 52 | **−5** (lowest) | 84 | ~215M (derived from per-task tokens) |
| MiMo-V2.6-Flash | 38 | 35 | 12 | 51 | −13 | 74 | — |
| DeepSeek-V4-Pro-0813 (max) | 36 | 41 | 18 | 51 | 1 | 80 | 163M |

Sources: AA comparison pages [I] for MiMo-V2.6-Pro against each DeepSeek, GLM-5.3 against Kimi-K3, GLM-5.3-Flash against Qwen3.8-2.4T-A95B, and GLM-5.3-Flash against MiMo-V2.6-Flash.

**Limits of this evidence:**
- AA runs one configuration per model and publishes no confidence intervals.
- CritPt is a small set, so 1–4 point gaps on any component are within plausible noise.
- AA's endpoint is the first-party API, not a verified pinned checkpoint.
- These numbers **prioritise** candidates; they are not our study's result.

## 3. MiMo-V2.6-Pro against the two DeepSeeks

### 3.1 Checkpoint identity (the main MiMo risk)

- **Two releases:** Xiaomi published two full-size Pro checkpoints, both MIT and both 1.02T total / 42B active parameters [P]:
  - `XiaomiMiMo/MiMo-V2.6-Pro-RL` @ `73875d00b30a89ef8cc353a0b60b0e9f9561952d`, 2026-09-22;
  - `XiaomiMiMo/MiMo-V2.6-Pro-MOPD` @ `adea8e2c5373181e5a973fa1ecb343cb31af214b`, 2026-09-27. Its card says it adds multi-teacher on-policy distillation to cut **tool-call repetition**, an agentic failure mode.
- **Which one was evaluated or is served:** AA's model page links the **RL** checkpoint. Xiaomi's API (`mimo-v2.6-pro`) does not say which weights it serves; the MOPD update may or may not be live.
- **Proposed pin:** the **RL** checkpoint, because it is the one the independent evidence refers to and MOPD's stated gain is agentic.
- **Pending:** written confirmation from Xiaomi (or a provider) of which checkpoint the endpoint serves. If this can't be established, the hosted MiMo result must be labelled "Xiaomi API `mimo-v2.6-pro` as of <date>", not "the released RL checkpoint".
- **Parameter count:** a press report (Mixed-News) noted that Hugging Face shows about 524B parameters. That is explained by storage format: about 1.0T parameters are U8-packed MXFP4, two values per byte (HF dtype breakdown: BF16 10.6B, F8_E4M3 13.4B, U8 ≈1.0T). The vLLM recipe states the weights are "stored as mxfp4 and computed as FP8 (block-wise e4m3, 128x128)" and take 566 GB on disk.

### 3.2 Native interface, audited from the pinned RL files

- **Chat template:**
  - Thinking is controlled by a single boolean, `enable_thinking`. It is **on unless explicitly false**.
  - There is **no effort or budget variable**, so the native maximum configuration is simply thinking enabled.
  - No system prompt is injected unless tools are supplied.
  - Reasoning sits in `<think>…</think>`, and turns end with `<|im_end|>`.
- **Silent-default hazard, same class as findings 1–5 in 15:** `generation_config.json` sets `do_sample=false` and `max_new_tokens=2048`. A self-hosted Transformers run that inherited these would decode greedily and truncate at 2,048 tokens. The card recommends temperature 1.0 and top_p 0.95, and so does the API, which *forces* these in thinking mode.
- **EOS IDs:** [151643, 151645, 151672]. The vLLM parsers are `mimo` for reasoning and `mimo` for tool calls.

### 3.3 Comparison for our research question

**MiMo-V2.6-Pro against both DeepSeeks:** MiMo is higher on **all five** reasoning-relevant components [I]:

| Component | MiMo | V4.1-Flash | V4-Pro |
|---|---|---|---|
| HLE | 49 | 39 | 41 |
| CritPt | 27 | 14 | 18 |
| SciCode | 61 | 52 | 51 |
| Omniscience | 8 | −5 | 1 |
| LCR | 86 | 84 | 80 |

The HLE, CritPt and SciCode margins (8–13 points) are well beyond the plausible noise noted in §2.

**Vendor evidence is thin:** Xiaomi's published MiMo evaluation table is agentic only, and I found no vendor no-tools reasoning table. Its inclusion therefore rests on independent evidence. That is disclosed; it is not a reason to exclude it.

**V4.1-Flash against V4-Pro** (the decision about which DeepSeek to replace):
- **Publisher's own no-tools table** (pinned V4.1-Flash README L117–L123, max effort) [P]:

  | Benchmark | V4-Pro | V4.1-Flash |
  |---|---|---|
  | GPQA Diamond | 92.4 | 90.9 |
  | HLE, text subset | 42.7 | 39.1 |
  | MathArena Apex | 65.3 | 65.6 |
  | Codeforces | 3348 | 3471 |

  V4.1-Flash's advances in that card are almost entirely **agentic** (Terminal-Bench, DeepSWE, AutomationBench, HLE *with tools*).
- **Independent components** [I]: V4-Pro is higher on HLE (41 vs 39), CritPt (18 vs 14) and Omniscience (1 vs −5). V4.1-Flash is higher on LCR (84 vs 80), and the two are essentially tied on SciCode.
- **Headline index:** V4.1-Flash's higher score (39 vs 36) comes from the agentic components (AutomationBench 69 vs 57, Terminal-Bench 27 vs 14), which are outside Strand A.

**Decision:** **replace DeepSeek-V4.1-Flash with MiMo-V2.6-Pro; retain DeepSeek-V4-Pro-0813.**
- **Why:** among the seven, V4.1-Flash has the weakest no-tools reasoning evidence. It is lowest on HLE, CritPt and Omniscience.
- **Evidence is the reason, not family:** the replacement is not made for family diversity. Had the evidence favoured dropping V4-Pro, or dropping neither DeepSeek, that would have been proposed.
- **Pre-registered expectation:** the retained V4-Pro is the DeepSeek configuration with the stronger reasoning evidence, not a guaranteed winner. Our study may still find V4.1-Flash ≥ V4-Pro on our panel; that is now untested and should be stated as a limitation.

### 3.4 The closest call: GLM-5.3-Flash

This model was checked as a possible alternative removal instead of V4.1-Flash.

| Component | GLM-5.3-Flash | DeepSeek-V4.1-Flash |
|---|---|---|
| HLE | 40 | 39 |
| CritPt | 15 | 14 |
| SciCode | 52 | 52 |
| Omniscience | 7 | −5 |
| LCR | 80 | 84 |

- **Evidence:** GLM-5.3-Flash is equal or higher on four of five components. Omniscience is the only clear margin.
- **Status:** the two are nearly tied, and GLM-5.3-Flash is the **first reserve for removal** if a slot is needed.
- **Why it stays:**
  - It is weakly ahead on the evidence.
  - It carries the one comparison in the set that remains genuinely open: a newly trained hybrid sparse/linear-attention base against GLM-5.3. That is research value independent of family.

## 4. Other challengers: final check

- **Sources:** the AA open-weights ranking, AA per-model pages, and search for releases in September 2026.

| Candidate | Evidence | Verdict |
|---|---|---|
| MiMo-V2.6-Flash (310B/15B active, MIT) | Index 38; below GLM-5.3-Flash on HLE (35 vs 40), CritPt (12 vs 15), Omniscience (−13 vs 7) and LCR (74 vs 80) [I] | not a challenger |
| DeepSeek-V4-Flash-Vision | Index 35; a multimodal variant | not a challenger |
| Qwen3.8-27B (xhigh) | Index 34 | not a challenger (dense/scale reserve, as in 14) |
| K2 Horizon 375B-A23B | Index 31 | not a challenger |
| MiniMax-M3 | Index 29 | no change from 14 |
| Nemotron-3-Ultra, Inkling, Muse Glimmer, Mistral Medium 3.5 | Index 23 and below | no change from 14 |
| Qwen3.8-Max, Grok 4.7, and other hosted-only systems | not open weights | out of scope |

**Result:** no other open-weight model has evidence strong enough to displace one of the proposed six. This is bounded by what AA and search indexed on 2026-09-29; a release in the last few days could be missing.

## 5. Proposed final experimental set

These six are a justified contemporary research sample for comparing no-tools reasoning and general capability. They are **not** claimed to be the six best open models in existence.

| ID | Model and pinned checkpoint | Reason for inclusion |
|---|---|---|
| **P35 (new)** | MiMo-V2.6-Pro-RL @ `73875d00` | Highest independent reasoning-relevant evidence of any open-weight model (HLE 49, CritPt 27, SciCode 61) |
| P25 | DeepSeek-V4-Pro-0813 @ `72e1d323` | DeepSeek configuration with the stronger no-tools reasoning evidence, both from the publisher and independent |
| P28 | GLM-5.3 @ `aca966e4` | Independent Index 45; SciCode 59; strong across components |
| P27 | GLM-5.3-Flash @ `eb9eb208` | Weakly ahead of the displaced V4.1-Flash; tests a newly trained hybrid base against GLM-5.3 (the open comparison) |
| P29 | Kimi-K3 @ `f831ab66` | Second-highest HLE (47); highest Omniscience (20) and LCR (89) |
| P34 | Qwen3.8-2.4T-A95B @ `207bd685` | Released checkpoint independently scored under its own name: HLE 42, CritPt 20 |

**Dropped:** P24 DeepSeek-V4.1-Flash moves to reserve. This is prioritisation, not a finding that it is inferior on our panel.

## 6. Execution routes (hosted)

The laptop (32 GB RAM) cannot host any of these checkpoints. Every route below is a remote API. Pricing is per 1M tokens, taken from first-party pages on 2026-09-29 unless marked.

| Model | Recommended route (exact ID) | Checkpoint equivalence | Reasoning control | Sampling control | Max output | Reasoning/final separation | Precision disclosed | Rate limit (as documented) | Price in / out per 1M |
|---|---|---|---|---|---|---|---|---|---|
| MiMo-V2.6-Pro | Xiaomi MiMo API, `mimo-v2.6-pro` (OpenAI-compatible `api.xiaomimimo.com/v1`) | **Unclear: RL or MOPD** (pending) | `thinking: enabled` (the default and the maximum; no effort levels) | temperature and top_p **fixed at 1.0 / 0.95 in thinking mode**, matching the card | **131,072** | `reasoning_content`; `usage.completion_tokens_details.reasoning_tokens` | no (checkpoint is MXFP4 storage, FP8 compute) | 100 RPM, 10M TPM | $0.435 / $0.87 |
| DeepSeek-V4-Pro-0813 | DeepSeek API, `deepseek-v4-pro` (pricing page maps it to "DeepSeek-V4-Pro-0813") | named mapping [P]; served precision not stated | `reasoning_effort` low / high / **max** (default high, so **must set max**) | temperature **ignored** in thinking mode; top_p honoured only in 0.95–1.0, so set 1.0 per the card | **384K** | `reasoning_content` | no | 500 concurrent requests per account | off-peak $0.66 / $1.98; peak $1.32 / $3.96 |
| GLM-5.3 | Z.ai API, `glm-5.3` | first-party; not stated to be byte-identical | `reasoning_effort` low / high / **max** (default max); thinking always on | `do_sample`, temperature (0–1), top_p configurable | **131,072** | `reasoning_content`; **no reasoning-token field** | no | not verified | $1.40 / $4.40 |
| GLM-5.3-Flash | Z.ai API, `glm-5.3-flash` (not `flashx`) | first-party; not stated | as GLM-5.3 (docs recommend temperature 1, top_p 0.95, max effort) | as GLM-5.3 | **131,072** | as GLM-5.3 | no | not verified | $0.15 / $0.50 |
| Kimi-K3 | Moonshot API, `kimi-k3` (`api.moonshot.ai/v1`) | first-party; says the weights are released, not that the served model is byte-identical | `reasoning_effort` low / high / **max** (default max) | temperature and top_p **fixed at 1.0 / 0.95**, matching the card | **1,048,576** (default 131,072) | streaming `reasoning_content`; reasoning-token usage not documented | no | tiered by top-up; not verified | $3.00 / $15.00 per aggregators [S]; AA lists $2.40 / $12.00. Use $15 for budgeting |
| Qwen3.8-2.4T-A95B | **Decision needed:** Alibaba Model Studio `qwen3.8-2.4t-a95b` or a third-party provider serving the native 262K context (Fireworks, DeepInfra, Together) | Alibaba names the open-source release, but advertises a **~1M context**, which implies context extension. That deviates from our "no extension" setting (15, finding 5). The third-party 262K endpoints match native context, but their precision is undisclosed except Bitdeer (FP8). | effort low / high / xhigh (the pinned template accepts xhigh / medium / low; **verify the API vocabulary**) | Alibaba: not documented. OpenRouter/third-party: top_k, min_p and seed accepted | **131,072** (Alibaba and OpenRouter) | Alibaba field not verified | third-party mostly no | Alibaba dynamic; others not verified | Alibaba Singapore $2.00 / $6.00 (AA lists $2.50 / $7.50); third-party $1.90–2.00 / $5.70–8.00 |

**Opaque or flagged routes:**
- Aggregators (OpenRouter, Vercel, Requesty) route to changing upstreams, so the provider can change between requests. Use one only if the upstream provider is pinned per request and logged.
- Speed-tier variants (Fireworks FAST, "ULTRA", MiMo-UltraSpeed, GLM FlashX) are different serving configurations.
- Nebius GLM-5.3 is FP4, a relabelled precision.
- AA publishes a provider "accuracy" check for Kimi-K3, ranging 93–102% relative to native. It shows provider variance is real.

### 6.1 Protocol consequences of hosted execution (decisions for you, not yet made)

1. **Common output ceiling:**
   - **Why it changes:** three routes (MiMo, both GLMs) and Qwen's providers cap output at **131,072**. So the protocol's native-context ceiling (planning estimate about 245,760, file 16 §5) is not achievable when hosted.
   - **Proposal:** a pre-outcome amendment, T_hosted = min(native-derived T, smallest route max output) = **131,072** (16 × 8,192). The only alternative is dedicated self-hosted serving for four models.
   - **Why this is legitimate:** no outcomes exist, so this is a lawful pre-registration change. It must be recorded as an amendment, with the reason "execution route limit".
2. **Rendered-prompt verification is impossible on chat APIs:** templates are applied server-side. The gates in 15 ("rendered effort prefix verified", "rendered prompt SHA-256") must become:
   - hash the **request payload**;
   - record the echoed model ID and `system_fingerprint`, or the provider's equivalent;
   - add an integration check that max effort produces more reasoning tokens than low effort on the same fixture item (a stage-2 test).
3. **Some pending items become irrelevant, others appear:**
   - **No longer needed:** the Kimi output parser and GLM EOS token names, because providers return `reasoning_content` and `finish_reason`.
   - **Replaced by:** trust in provider-side channel parsing, recorded per attempt.
   - **Truncation:** `finish_reason = "length"` classifies an attempt as `BUDGET_TRUNCATED`.
4. **Seeds:** none of the first-party routes documents seed support. Mark `seed_unsupported_by_backend` and claim reproducibility at the configuration level only; file 17 already says this.
5. **Sampling equality:**
   - The fixed provider settings equal the publisher recommendations for MiMo, Kimi and GLM.
   - DeepSeek ignores temperature and uses a server value. Record it as provider-fixed.
6. **Qwen route:** choose between Alibaba (first party, but context extension enabled) and a native-262K third-party provider (precision to be confirmed in writing). I recommend a third-party provider **only if** it confirms both precision and chat template; otherwise Alibaba, with the deviation disclosed.
7. **Checkpoint drift:** first-party aliases can be silently updated. Record the response model ID on every attempt. Run each model's final set in a short window, and abort and report if the returned model ID changes.

## 7. Cost and runtime estimates (planning only)

### 7.1 Inputs

- **Prompts, measured offline from the pinned item data:**
  - Final set: 2.46M characters (≈0.62M tokens at 4 characters per token), plus about 500 tokens of native template or effort prefix per request [A], giving ≈1.26M input tokens per model.
  - Development set: ≈0.18M input tokens per model.
  - Longest prompt: 25.6K characters.
- **Output per item** (reasoning + final), for a median-verbosity model at max effort [A]:

  | Benchmark | Low | Central | High |
  |---|---|---|---|
  | MMLU-Pro | 1.5K | 4K | 10K |
  | MATH-500 | 2K | 5K | 12K |
  | BBEH | 6K | 15K | 40K |
  | IFEval | 0.8K | 2K | 6K |

  - These are assumptions: no documented per-item token counts exist for these models on these tasks. **Measuring them is the purpose of development calibration.**
- **Model verbosity multipliers** [I], relative to about 160M total index output tokens:

  | Model | Multiplier |
  |---|---|
  | MiMo | 0.90 |
  | DeepSeek-V4-Pro | 1.02 |
  | GLM-5.3 | 1.31 |
  | GLM-5.3-Flash | 1.13 |
  | Kimi | 1.01 |
  | Qwen | 1.08 |

- **Caps:** every item is capped at C = 131,072.
- **Caching:** no cache discounts assumed.
- **Throughput:** AA measurements on the recommended endpoints:

  | Model | Tokens/s |
  |---|---|
  | MiMo | 41 |
  | DeepSeek-V4-Pro | 81 |
  | GLM-5.3 | 83 |
  | GLM-5.3-Flash | 46 |
  | Kimi | 39 |
  | Qwen (Alibaba) | 39 |
  | Qwen (third-party) | 98–202 |

### 7.2 Estimates (six proposed models; the model script is in §10)

| Stage | Requests | Input tokens | Output tokens (all 6) | Cost, low / central / high | Upper bound (every item hits C) |
|---|---|---|---|---|---|
| Stage 2 integration test (about 6 short fixture requests per model) | ~36 | <0.1M | <1M | < $10 | ~ $150 |
| Development calibration (216 items) | 1,296 | ~1.1M | 3.8M / 9.5M / 24M | **$19 / $47 / $130** | $914 |
| Final evaluation (1,280 items) | 7,680 | ~7.6M | 27M / 68M / 177M | **$138 / $335 / $952** | $5,417 |
| **Complete experiment** (development + final) | 8,976 | ~8.7M | 31M / 78M / 201M | **$157 / $382 / $1,082** | $6,331 |
| IFEval diagnostic (541 prompts, optional and separate) | 3,246 | ~1.9M | — | $16 / $36 / $114 | $2,288 |

**Where the cost goes:** Kimi-K3 is about 49% of the central final cost ($164), Qwen $71, GLM-5.3 $63, DeepSeek-V4-Pro $22 (off-peak; $112 at peak in the high case), MiMo $9 and GLM-5.3-Flash $6. For reference, keeping V4.1-Flash would have cost about $9 central, so the swap is not driven by cost.

**Recommended authorisation budget:**
- about **$60** for stages 1–3 (verification, integration, calibration);
- a separate decision for the final run *after* calibration, when measured token counts replace the assumptions. Expect roughly $350–$600 including 20% for infrastructure reruns.
- **Spend caps:** hard caps must be set in the runner per model and per stage, and in each provider console where supported.

**Runtime** (the runner only does network I/O, so no laptop overheating risk; sleep and power are the risk; see §8):
- **Sequential, slowest model:** about 81 h central for the final set (Qwen on Alibaba at 39 tokens/s; range 32–211 h).
- **Development calibration:** about 1.5 h central (range 0.5–4 h) at concurrency 8.
- **Final evaluation:** about 10 h central wall-clock at concurrency 8 per model with all six in parallel (range about 4 h to 1.5 days). At concurrency 16 it is about 5 h, where documented limits allow.
- **Longest single request:** one maximal 131K-token generation at 39 tokens/s takes about 56 minutes. The 30-minute no-token watchdog in 16 is compatible, since tokens keep streaming.

### 7.3 Is 1,280 final items necessary? (analysis only; protocol unchanged)

Paired minimum detectable difference, 80% power, at the stated discordance rate (share of items where two models disagree):

| Items per benchmark | Discordance 10% | 20% | 30% |
|---|---|---|---|
| **420–460 (current)** | 4.1–4.3 pp unadjusted / 6.0–6.3 pp Holm-worst | 5.8–6.1 / 8.6–9.0 | 7.2–7.5 / 10.5–11.0 |
| 210–230 (half) | 5.8–6.1 / 8.6–9.0 | 8.3–8.6 / 12.1–12.7 | 10.1–10.6 / 14.8–15.5 |
| 100–150 | 7.2–8.9 / 10.6–13.0 | 10.2–12.5 / 15.0–18.3 | 12.5–15.3 / 18.3–22.5 |

**Assessment:**
- **The observed gaps are small:** the independent gaps between the proposed six on reasoning components are mostly **1–8 pp**.
- **The current size already limits resolution:** even at the current size, only the larger pairwise gaps will survive Holm correction across 45 comparisons.
- **Halving saves little:** it would save about $170 and about 5 h, but raise the detectable difference by about 40%. Most pairwise comparisons would then become uninformative.

**Recommendation:** keep 1,280.

**Cheaper, defensible options if cost ever became binding:**
- **Reduce MATH-500 first:** it has a likely ceiling effect, so few discordant pairs and little pairwise information. It accounts for about 19% of central output tokens.
- **Treat pairwise tests as secondary:** make per-model accuracy with Wilson intervals primary, and restrict confirmatory tests to a pre-declared subset of pairs, which reduces the Holm burden.

Either change must be a pre-outcome amendment; neither is made here.

## 8. Execution plan and stage gates

Nothing in this section is authorised yet. Each stage needs your explicit go-ahead.

| Stage | Action | Must pass before moving on |
|---|---|---|
| **0. Decisions** (no spend) | Accept or reject the proposed six; choose the Qwen route; accept or reject the hosted ceiling amendment (131,072); set spend caps | Written decisions recorded in 16/17 as pre-outcome amendments |
| **1. Provider verification** (accounts, no benchmark requests) | You create accounts and keys (Xiaomi, DeepSeek, Z.ai, Moonshot, the Qwen route) and store them in environment variables or the Windows Credential Manager, never in files in the repo. Ask each provider in writing for the exact checkpoint, served precision, context-extension state, max output, seed support, fixed sampling values, and the model-ID/fingerprint field. | Every route has documented answers; unanswered fields are recorded as "undisclosed"; keys confirmed absent from repo, logs and manifests (a pre-commit secret scan) |
| **2. Tiny integration test** (about 6 synthetic, non-benchmark requests per model) | Check: effort parameter accepted; max vs low reasoning-token contrast; `reasoning_content` present; `finish_reason` semantics by forcing `length` on a tiny `max_tokens`; streaming watchdog; retry and resume; payload hashing; cost accounting | Every model passes all checks; the parsers and status classifier pass fixtures; per-request logs contain no keys; measured cost matches the price sheet within 10% |
| **3. Development calibration** (216 items per model at C) | One generation per item; measure truncation rate, token distributions and infrastructure failures | Wilson bound reported per model. Truncation of 5% or less is "adequate"; otherwise the model is labelled censored and the run continues (no rescue). Zero unexplained infrastructure failures. Plumbing validated against the development answer key only. |
| **4. Freeze output budget** | Set `calibrated=true`, T and C in `evaluation.json`; lock manifests and hashes; record the provider model IDs observed | Preflight passes with no pending mandatory fields; you sign off on the final-run spend cap |
| **5. Final evaluation** (7,680 requests) | Resumable, checkpointed per attempt; all models inside a short window; model-ID drift abort; infrastructure reruns of 2 or fewer | Complete or `MISSING` status for every attempt; no key leakage; the answer key is never read by the runner |
| **6. Scoring and statistics** | Official scorers (Math-Verify with pinned fixtures, vendored BBEH, Inspect MMLU-Pro), then Wilson intervals, McNemar with Holm, paired bootstrap, matched-token sensitivity at 8K/32K/64K | Scorer fixtures pass; answer keys match the hash lock; the analysis script is frozen before scoring runs |

**Operational safety:**
- The runner should live on an always-on machine: a free-tier cloud VM, or the laptop on AC with sleep disabled. The Modern Standby freeze during Benchmark v2 is the precedent.
- It must be resumable, because a 10-hour run can be interrupted.
- No local model processes are involved.

## 9. Manifests affected if the proposed set is accepted (nothing changed yet)

| File | Change needed |
|---|---|
| `manifest/models.json` | Add P35 MiMo-V2.6-Pro-RL (interface, `enable_thinking=true`, sampling 1.0/0.95 with `do_sample` explicit, EOS IDs, MXFP4/FP8 precision, parser, checkpoint-identity gate); move P24 to a `reserve` block; add a hosted-route section per model |
| `manifest/source-lock.json` + a new `XiaomiMiMo--MiMo-V2.6-Pro-RL/` | Archive and hash the non-weight files at `73875d00`: README, config, generation_config, chat_template, tokenizer_config |
| `15-six-model-configuration-manifest.md` | Replace the P24 row with P35; add the MiMo findings (§3.2); add the hosted-route columns |
| `16-frozen-evaluation-protocol.md` §5 and `manifest/evaluation.json` `budget_policy` | Amendment: the terminal ceiling includes the route max output (131,072); the rendered-prompt gate becomes a request-payload gate for hosted routes |
| `manifest/dev-calibration-spec.json` | Update the model list |
| `17-fairness-reproducibility-audit.md` | New items: MiMo `do_sample`/`max_new_tokens` defaults; server-side templates; provider-fixed sampling; checkpoint drift; Qwen context extension on Alibaba |
| `14-capability-first-shortlist.md` | Mark as superseded on the selection question by 18 |
| `README.md`, `CLAUDE_CODE_HANDOFF.md` | Precedence update |

**Unchanged:** item manifests, answer keys, prompts, all hash locks for data and prompts, and the scorer plan. The sampled items are independent of the models.

## 10. Reproducibility of this audit

- **Offline scripts** (in `manifest/planning/`; no network, no inference):
  - `prompt_lengths.py`: prompt character lengths from the pinned data.
  - `cost_model.py`: the §7 estimates.
- **Web evidence read 2026-09-29:**
  - AA model, comparison and provider pages;
  - HF model API and raw files for both MiMo Pro checkpoints;
  - Xiaomi MiMo API docs (the OpenAI-compatibility page and the model page);
  - DeepSeek pricing, thinking-mode and rate-limit docs;
  - Z.ai GLM-5.3, GLM-5.3-Flash, pricing and chat-completion docs;
  - Moonshot's Kimi-K3 quickstart;
  - Alibaba Model Studio's `qwen3.8-2.4t-a95b` page;
  - the NVIDIA Qwen serving blog;
  - VentureBeat and Mixed-News articles (secondary).
- **Prices and limits change;** re-verify all of them at stage 1.

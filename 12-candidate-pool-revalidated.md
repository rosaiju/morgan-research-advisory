# Revalidated candidate pool: evidence, redundancy, and hardware dependencies

**Current selection policy:** [14 capability-first shortlist](14-capability-first-shortlist.md) supersedes hardware gates and shortlist requirements here. Six capability candidates are proposed independently of Morgan hardware. Deployment analysis follows capability selection.

September 29, 2026. Current discovery decision, not a frozen experimental set. Supersedes the nine-model pool and priority shortlist in earlier documents. No benchmarks or weight downloads performed.

## Scope and interpretation

This is the complete documented pool for this bounded review, not a claim to have enumerated every release worldwide. Discovery was reopened across publisher repositories, current release documentation, independent evaluator pages, and openness-oriented research releases. New names were checked against primary sources rather than admitted on social-media popularity. Inclusion means worth considering; it does not mean every model should be downloaded or benchmarked.

The capability construct is English text reasoning and general problem solving; deployment and application evaluation remain separate. Reasoning branding alone is insufficient. No family, including DeepSeek, is guaranteed an experimental slot. Downloaded models receive no preference. A distilled model can be an excellent candidate but does not inherit its teacher's benchmark scores or architecture.

Role labels: Q = quality-oriented hypothesis, E = potential deployment-efficiency tradeoff, R = reproducibility/transparency contrast. These describe reasons to investigate, not measured Morgan performance. Every model's actual feasibility depends on hardware, precision, context, batching, and permitted software. Even an 8B model is not guaranteed to fit the assigned allocation.

## A. Compact/moderate candidates and research contrasts

Each linked name is the exact checkpoint. Positive evidence is generally publisher-reported unless the independent-evidence section says otherwise. Negative evidence below is a limitation or scope argument, not proof of inferiority.

| ID / exact checkpoint | Role | Strongest reason to include | Strongest reason against a mandatory slot / redundancy |
|---|---|---|---|
| P01 [Qwen/Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) | E/Q | Broad published academic/reasoning evidence in a compact dense hybrid model; native reasoning controls | Cross-publisher protocol gaps; overlaps other compact generalists; do not infer MoE from family marketing |
| P02 [Qwen/Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) | Q | Current larger dense Qwen, native effort controls, publisher and independent evaluation coverage | Agentic evidence is not pure reasoning; long outputs can affect service utility; default effort is not equal compute |
| P03 [Qwen/Qwen3.6-35B-A3B](https://huggingface.co/Qwen/Qwen3.6-35B-A3B) | E/Q | Previously omitted sparse Qwen alternative; a different serving tradeoff from dense 27B | More total weights despite small active count; overlaps other 30B-class MoEs; newer dense version does not automatically dominate this architecture |
| P04 [google/gemma-4-12B-it](https://huggingface.co/google/gemma-4-12B-it) | E | 11.95B encoder-free dense model; documented reasoning and general-task evidence | Capability numbers below larger siblings in publisher table; config-level audit incomplete; its smaller footprint may still matter |
| P05 [google/gemma-4-26B-A4B-it](https://huggingface.co/google/gemma-4-26B-A4B-it) | E/Q | 25.2B total/3.8B active MoE offers distinct execution tradeoff | Not a 4B memory model; three Gemma sizes are unnecessary unless their resource tradeoffs remain decision-relevant |
| P06 [google/gemma-4-31B-it](https://huggingface.co/google/gemma-4-31B-it) | Q | Stronger within-family published capability profile; independent evaluation coverage | Higher dense-model memory/compute; independent composite evidence does not establish a universal win |
| P07 [openai/gpt-oss-20b](https://developers.openai.com/api/docs/models/gpt-oss-20b) | E/Q | Approximately 21B total/3.6B active; explicit effort controls and documented native quantization | Harmony and MXFP4 compatibility complicate naive common-backend comparisons; not directly comparable to BF16 memory claims |
| P08 [nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16) | E/Q | Hybrid Mamba/attention/MoE with published no-tools reasoning evidence | Specialized backend/parser and NVIDIA license; efficiency must be measured, not inferred from 3.5B active parameters |
| P09 [ibm-granite/granite-4.2-8b](https://huggingface.co/ibm-granite/granite-4.2-8b) | E | Compact dense model, explicit mode controls and published capability evidence | Convenience for ablations is not evidence of best capability; uncertain incremental value over other compact choices |
| P10 [meta-models/Muse-Glimmer-30B](https://huggingface.co/meta-models/Muse-Glimmer-30B) | Q/E | Dense approximately 29.6B reasoning/agent model; documented local quantization configurations | Much evidence concerns agent scaffolds; do not transfer those scores to single-turn reasoning; native versus quantized variants require separate labels |
| P11 [zai-org/GLM-4.7-Flash](https://huggingface.co/zai-org/GLM-4.7-Flash) | E/Q | Previously omitted 30B-A3B MoE; published math/science evidence and explicit evaluation recipes | Larger newer GLMs do not automatically supersede this size class, but its comparative baselines are older; some published tasks use 131K generation |
| P12 [deepseek-ai/DeepSeek-R1-0528-Qwen3-8B](https://huggingface.co/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B) | E | Explicit small reasoning distillation with mathematical and science results and documented decoding | Qwen3-8B base post-trained with DeepSeek reasoning traces; NOT full DeepSeek R1 and not an independent pretrained family. Older and narrower evidence than current generalists |
| P13 [deepseek-ai/DeepSeek-R1-Distill-Qwen-32B](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B) | Q/R | Larger historical reasoning distill with published standardized evaluations; useful if a distillation comparison matters | Qwen-derived dense weights, older release, overlaps current 27–35B candidates. No automatic slot merely to represent DeepSeek |
| P14 [allenai/Olmo-3.1-32B-Think](https://huggingface.co/allenai/Olmo-3.1-32B-Think) | R/Q | Training data/stages and evaluation recipes offer a materially stronger transparency case than weights alone | Transparency is not demonstrated superior current capability; dense 32B footprint. Keep if reproducibility is a substantive research objective, not a brand quota |
| P15 [LGAI-EXAONE/EXAONE-4.5-33B](https://huggingface.co/LGAI-EXAONE/EXAONE-4.5-33B) | Q | Previously omitted reasoning/multimodal family with documented benchmark evidence | EXAONE 1.2-NC terms require use-case eligibility review; Korean/document strengths may not match English text scope; no matched independent full-pool evidence established |
| P16 [microsoft/Phi-4-reasoning-plus](https://huggingface.co/microsoft/Phi-4-reasoning-plus) | Q/R | Enhanced Phi reasoning variant is the relevant specialist challenger, rather than automatically retaining the earlier plain Phi checkpoint | Older dense specialist; long reasoning/integration requirements; include only if published evidence or study role distinguishes it from compact newer generalists |

## B. Larger server candidates: not excluded by laptop limits

These require explicit multi-GPU/high-memory feasibility estimates. Low active parameter counts, Flash/Small names, and hosted API prices are not memory or latency guarantees. Exact hardware is unknown; none is currently approved for empirical admission.

| ID / exact checkpoint | Role | Evidence for consideration | Evidence limitation / redundancy |
|---|---|---|---|
| P17 [openai/gpt-oss-120b](https://developers.openai.com/cookbook/articles/gpt-oss/run-transformers) | Q/E | Larger open-weight MoE with documented quantized deployment | Native format/hardware dependence; not an automatic replacement for 20B if concurrency matters |
| P18 [nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4) | Q/E | Official technical report documents reasoning and hardware-specific throughput evaluation | NVFP4 kernels and precision differences; published throughput is not Morgan throughput; card fetch previously failed, report is corroborating source |
| P19 [inclusionAI/Ling-3.0-flash](https://huggingface.co/inclusionAI/Ling-3.0-flash) | Q/E | 124B total/5.1B active hybrid-linear MoE; explicit reasoning and serving recipes | Tailored agent prompts/cache infrastructure affect results; independent comparable coverage limited |
| P20 [mistralai/Mistral-Small-4-119B-2603](https://huggingface.co/mistralai/Mistral-Small-4-119B-2603) | Q/E | Reasoning-capable sparse larger alternative with distinct deployment profile | Small does not mean small weights; overlaps 120B-class MoEs |
| P21 [mistralai/Mistral-Medium-3.5-128B](https://huggingface.co/mistralai/Mistral-Medium-3.5-128B) | Q | Newer open-weight larger Mistral alternative overlooked previously | Modified MIT terms and substantial deployment requirements; retain actual license restrictions rather than treating as ordinary MIT |
| P22 [stepfun-ai/Step-3.5-Flash](https://huggingface.co/stepfun-ai/Step-3.5-Flash) | Q/E | 196B-class sparse model, approximately 11B active; primary technical report and backend support | Weight storage remains large; agentic and single-turn results must be separated |
| P23 [deepseek-ai/DeepSeek-V4-Flash-0731](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731) | Q/E | Full DeepSeek release; potentially different weight/resource tradeoff from V4.1 | Cannot assume newer V4.1 dominates memory efficiency because its architecture and total storage differ |
| P24 [deepseek-ai/DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) | Q/E | Full current multimodal DeepSeek, reasoning controls and detailed architecture report | 552B backbone plus conditional-memory considerations; low active count and compressed KV do not remove storage burden |
| P25 [deepseek-ai/DeepSeek-V4-Pro-0813](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813) | Q | Full updated Pro checkpoint is relevant to high-end capability coverage | Much larger infrastructure class; no justified claim it can fit Morgan allocation |
| P26 [deepseek-ai/DeepSeek-R1-0528](https://huggingface.co/deepseek-ai/DeepSeek-R1-0528) | Q/R | Full reasoning model and reference for the R1 distillation lineage; published repeated-sampling protocol | Older high-resource release; retain as reference unless reproducibility/longitudinal question warrants testing alongside newer full models |
| P27 [zai-org/GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash) | Q/E | 320B total/18B active current GLM alternative; explicit evaluation footnotes | Agentic harness, context and judge settings differ by task; not comparable to GLM-4.7-Flash merely by shared name |
| P28 [zai-org/GLM-5.3](https://huggingface.co/zai-org/GLM-5.3) | Q | Current large-family reference with documented effort settings | Substantial resources and scaffold-dependent published results |
| P29 [moonshotai/Kimi-K3](https://huggingface.co/moonshotai/Kimi-K3) | Q | Current released Kimi candidate prevents anchoring landscape on K2.6 | Full artifact/precision and service requirements need confirmation; do not transfer older K2.6 independent results |
| P30 [MiniMaxAI/MiniMax-M3](https://huggingface.co/MiniMaxAI/MiniMax-M3) | Q | Additional current open-weight reasoning family, multiple reasoning modes | Agent-heavy evidence and high-resource deployment; no verified universal advantage |
| P31 [thinkingmachines/Inkling-Small](https://huggingface.co/thinkingmachines/Inkling-Small) | Q/E | Distinct released family, smaller member of Inkling range | Small is relative to its family, not laptop-sized; limited matched evidence in this review |
| P32 [thinkingmachines/Inkling](https://huggingface.co/thinkingmachines/Inkling) | Q | Larger family reference prevents sampling only smaller releases | Additional resource burden; test only if competitive evidence and allocation justify it |
| P33 [nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16) | Q | Frontier-scale family member with technical report and training recipe | 550B-class storage; native NVFP4 sibling is another configuration, not identical to BF16 |
| P34 [Qwen/Qwen3.8-2.4T-A95B](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B) | Q | Released high-end Qwen checkpoint, relevant to capability ceiling | Rack-scale class. Hosted Qwen3.8-Max includes different features; do not assign its API scores automatically to released weights |

P16's official card confirms released 14B dense weights, MIT licensing, and additional reinforcement learning beyond Phi-4-reasoning. Its documented 32K context and sampling recipe require explicit integration checks; experimental context extension is not assumed. No candidate in this pool has passed a Morgan feasibility check.

## Redundancy decisions

The original Llama3.2-3B, Qwen2.5-7B, Granite3.3-8B, Phi-mini and small original R1 distills remain historical pilot records, not automatic empirical obligations. Qwen3-8B is a compatibility fallback. Qwen3.6-27B is redundant to the newer same-size Qwen3.8 for this scope unless deployment compatibility differs. Kimi-K2.6 remains independent-evidence context, not a required additional experiment beside K3. Plain Phi-4-reasoning and reasoning-plus should not both consume slots unless post-training is the research question.

Potential, not proven, redundant clusters: Gemma 12/26/31; compact Qwen/Granite/DeepSeek distill; 30B-class MoEs; 120B-class MoEs; very large full-model alternatives. Different sizes/architectures are not redundant when they occupy distinct feasible service points. At most one representative per unresolved equivalent role is the default workload rule, never a family exclusion.

## DeepSeek identity and evidence

The publisher explicitly says R1-0528-Qwen3-8B is Qwen3-8B-Base post-trained using distilled R1-0528 reasoning. The same card contains a separate table for FULL R1-0528. Full-model GPQA 81.0 must not be assigned to the 8B student, whose displayed GPQA value is 61.1. The card describes 64K generation and repeated sampling for pass@1 estimates. These numbers demonstrate the identity distinction; they are not directly comparable to the laptop's greedy 4K experiment. [Primary card](https://huggingface.co/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B/raw/main/README.md)

Do not infer an Ollama digest from a tag, treat Qwen-derived students as independent pretrained architectures, call a distill a quantized full model, or use professor preference as a selection score.

## Independent evidence: useful but bounded

Artificial Analysis's current comparison page displays Qwen3.8-27B xhigh at 34 and Gemma4-31B reasoning at 19 on index v4.3.2. It is one evaluator/version, not two incompatible publisher percentages. However, its rendered page also contains an estimate legend without exposing a complete per-component status mapping. Endpoint precision/revision and task-level settings were not fully audited. Treat this as independent published prioritization evidence, not a verified matched-weight causal comparison or grounds to remove Gemma. Do not compare these values with earlier v4.1/v4.2 numbers. API speed is not Morgan GPU speed. [Comparison](https://artificialanalysis.ai/models/releases/comparisons/qwen3-8-27b-vs-gemma-4-31b)

The v4.3 announcement assigns substantial weight to agent/coding workloads and private evaluations. That construct differs from our single-turn reasoning panel. [Methodology change](https://artificialanalysis.ai/articles/artificial-analysis-intelligence-index-v4-3)

An [independent Olmo page](https://artificialanalysis.ai/models/olmo-3-1-32b-think) provides coverage but does not justify treating openness as an accuracy score. [Epoch's Kimi-K2.6 record](https://epoch.ai/models/kimi-k2-6) is corroborating model evidence, not validation of K3. No independent matched comparison across all 34 entries was established. Missing coverage is unknown, not failure. The strongest positive evidence for many new families remains publisher reporting plus reproducible artifacts; this limits ranking confidence.

## Search boundary and exclusions

Searches included exact names and combinations of open weights, reasoning, September 2026, GLM Flash, Olmo Think, EXAONE, Step, Ling, Nemotron Ultra, Mistral Medium, DeepSeek full/distill, Qwen sparse and large releases. Primary cards linked above were opened, with previous primary audits retained for the original nine. Social and aggregator results were used only to discover publisher records. Specialized math-only, code-only, OCR, safeguard, and unofficial modified/abliterated derivatives are outside the default general-service pool. They require evidence of a distinct need to enter. Tiny edge models are not defaults because laptop constraints are not the objective. No claim that every omitted release is inferior is warranted.

Proceed with the decision procedure in [13](13-protocol-after-audit.md). Do not freeze four before hardware eligibility and the evidence matrix are complete.


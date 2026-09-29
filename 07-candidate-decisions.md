# Candidate pool and evidence-based dispositions

**Superseded candidate pool:** use [12 revalidated registry](12-candidate-pool-revalidated.md) and [13 selection procedure](13-protocol-after-audit.md). The mandatory nine-model screen below is withdrawn; retained as proposal history only.

September 29, 2026 cutoff. This is a proposed screening pool, not a ranking or final shortlist. All exact revisions and artifact licenses must be pinned before execution. Publisher sources below were examined; weight files were not downloaded or tested. The Nemotron Super card could not be fetched directly, so its release/configuration was corroborated using the [official technical report](https://research.nvidia.com/labs/nemotron/files/NVIDIA-Nemotron-3-Super-Technical-Report.pdf). The eight original laptop tags do not define the population of interest.

## Compact and moderate-size screening pool

Screen these nine configurations if hardware permits. This pool covers several model families and dense/MoE designs without requiring every size in every family. Two Qwen and two Gemma sizes expose a potentially important capability/resource tradeoff; those pairs are not independent architecture experiments.

| ID | Exact publisher checkpoint | Reason to screen | Evidence limitation |
|---|---|---|---|
| C01 | [Qwen/Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) | Compact recent general/reasoning candidate with published broad-task results | Scores are publisher-reported; no matched independent comparison established here |
| C02 | [Qwen/Qwen3.8-27B](https://huggingface.co/Qwen/Qwen3.8-27B) | Replaces Qwen3.6-27B as the main larger Qwen candidate; documented effort controls and newer reported results | Many reported gains involve agent scaffolds; do not equate them with raw single-turn reasoning |
| C03 | [google/gemma-4-12B-it](https://huggingface.co/google/gemma-4-12B-it) | Compact alternative family with thinking controls | Pin the exact 12B artifact; do not transfer 31B results |
| C04 | [google/gemma-4-31B-it](https://huggingface.co/google/gemma-4-31B-it) | Larger cross-family quality candidate | More weight memory than the 12B candidate; published scores are not our results |
| C05 | [ibm-granite/granite-4.2-8b](https://huggingface.co/ibm-granite/granite-4.2-8b) | Compact alternative with documented reasoning controls | No longer an automatic finalist simply because its controls simplify an ablation |
| C06 | [openai/gpt-oss-20b](https://developers.openai.com/api/docs/models/gpt-oss-20b) | Open-weight MoE alternative with effort controls; approximately 21B total and 3.6B active parameters | Preserve native format/precision and Harmony handling; active parameters are not memory footprint |
| C07 | [nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16) | Hybrid MoE alternative with reasoning and no-tools evidence | BF16 reference and quantized variants are distinct configurations; specialized architecture may affect backend feasibility |
| C08 | [google/gemma-4-26B-A4B-it](https://huggingface.co/google/gemma-4-26B-A4B-it) | MoE comparison prevents treating dense 31B as the only larger Gemma option | Retain during screening because serving behavior can differ; avoid three Gemma finalists without distinct measured tradeoffs |
| C09 | [meta-models/Muse-Glimmer-30B](https://huggingface.co/meta-models/Muse-Glimmer-30B) | Current Meta-family alternative, replacing reliance on Llama 3.2 3B as its representative | Text-only study does not evaluate multimodal/agentic claims; independent protocol coverage remains incomplete |

The numeric model labels describe classes, not complete loaded memory requirements. Compute eligibility only after confirming GPU allocation and supported artifact formats. Use BF16 reference where practical; preserve publisher-native quantization where integral to the release. Clearly label mixed-precision comparisons as configuration comparisons. Do not force all models into arbitrary third-party Q4 artifacts just to claim identical precision.

## Larger conditional pool

Include in the literature survey now. Promote at most two into our empirical screen if confirmed resources support them and comparable evidence suggests they could improve the capability/resource frontier. Apply the same held-out rules and record which compact entries, if any, were excluded for workload reasons. Do not conclude that the compact pool contains the strongest possible open models.

| Candidate | Role and admission rationale |
|---|---|
| [openai/gpt-oss-120b](https://developers.openai.com/cookbook/articles/gpt-oss/run-transformers) | Larger effort-controlled MoE reference; official deployment guidance supports considering it beyond laptop-sized models |
| [nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-NVFP4) | Larger quantized reasoning/serving alternative; hardware support must be verified |
| [mistralai/Mistral-Small-4-119B-2603](https://huggingface.co/mistralai/Mistral-Small-4-119B-2603) | Another larger-family alternative; the word Small is not a memory specification |
| [deepseek-ai/DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) | Current DeepSeek family reference; the card describes a 552B backbone and additional conditional memory, so its low active-parameter count does not make it an 8–16B-sized deployment |
| [zai-org/GLM-5.3](https://huggingface.co/zai-org/GLM-5.3) | Larger general/agentic reference with explicit effort settings; scaffold-dependent scores need protocol filtering |
| [thinkingmachines/Inkling-Small](https://huggingface.co/thinkingmachines/Inkling-Small) | Additional released family; full resource and protocol audit needed before empirical admission |
| [moonshotai/Kimi-K2.6](https://huggingface.co/moonshotai/Kimi-K2.6) | Larger alternative for landscape coverage; hosting feasibility is unconfirmed |
| [MiniMaxAI/MiniMax-M3](https://huggingface.co/MiniMaxAI/MiniMax-M3) | Larger alternative; compare text capability separately from tool/scaffold claims |

This is a bounded search, not a claim to enumerate every open checkpoint. Extremely large conditional models remain relevant to the survey even if the undergraduate experiment cannot host them. Hosted API access could supply supplementary capability evidence but would not validate Morgan deployment, and precision/version uncertainty must remain visible. No paid endpoint is authorized or provisioned here.

## Original eight: independent decisions

| Original candidate | Decision and reason |
|---|---|
| Llama 3.2 3B | Preserve pilot only. Optional historical small baseline, not required for current model selection. |
| Phi-4 Mini Reasoning | Survey/reserve for a specifically constrained small-model service. No automatic new experiment based on existing download. |
| Qwen2.5 7B | Preserve pilot baseline. Its custom-test win does not justify a core slot against newer candidates. |
| DeepSeek-R1 8B | Resolve exact upstream identity first. Optional historical specialist; do not substitute full DeepSeek scores. |
| Qwen3 8B | Compatibility fallback if newer artifacts cannot run; no automatic preference because already installed. |
| Granite 3.3 8B | Superseded as the primary IBM screening candidate; retain in survey history. |
| DeepSeek-R1 14B | Reserve rather than test every distilled size. Its inclusion needs a distinct evidence/resource role. |
| Phi-4 Reasoning 14B | Remove from mandatory finalist trio. Keep as an optional diagnostic of the original integration/greedy-decoding failures, outside primary selection unless later evidence warrants admission. |

These are scope decisions, not experimentally demonstrated defeats. Exact original checkpoint links and identity issues remain in [03](03-model-survey.md). If the professor specifically requires an original DeepSeek distill comparison, document that additional baseline rather than pretending it won admission on current capability evidence.

## What the numbers support

Qwen3.8-27B's own card reports GPQA Diamond 89.2 and LiveCodeBench v6 90.3; its table gives Qwen3.6-27B 87.8 and 83.9 respectively. This supports screening the successor, not assuming superior Morgan performance. Per-task generation details still require audit, and agent benchmark footnotes use differing harnesses and modified task sets. [Publisher source](https://huggingface.co/Qwen/Qwen3.8-27B)

Google's table reports MMLU-Pro 85.2/82.6/77.2 and GPQA Diamond 84.3/82.3/78.8 for Gemma 4 31B/26B-A4B/12B respectively. These are publisher observations, not a matched cross-publisher ranking. The earlier survey's uncertainty about 12B attribution is narrowed by this explicitly labeled table, but protocol uncertainty remains. [Publisher source](https://huggingface.co/google/gemma-4-31B-it)

The prior [20-record ledger](05-evidence-ledger.csv) remains a useful set of observations. It is neither complete for the updated pool nor sufficient to order the nine candidates. New observations are recorded in [10](10-additional-evidence.csv). No independent matched comparison across this entire pool was established. That specific gap justifies our screen.

## Finalist status

No full-evaluation finalist is named yet. The strongest defensible decision today is which candidates deserve screening, not who will win it. All nine compact candidates are eligible for the proposed screen subject to hardware; three or four advance using the preregistered rules in [06](06-independent-protocol.md). If resources cannot support all nine, amend scope before viewing screening outcomes and disclose the narrower population.

# Model survey and evidence assessment

Search cutoff: September 29, 2026. This is a bounded rapid review, not an exhaustive systematic review and not a new benchmark result. Exact checkpoint revisions must be pinned later; links currently point to publisher-maintained pages.

## Search and selection method

Start with all eight student-specified candidates, resolve their likely upstream identities, then screen newer publisher releases across Qwen, Microsoft, DeepSeek, Google, IBM, NVIDIA, Mistral, and OpenAI. Include downloadable post-trained models relevant to text reasoning or university-serving research. Include larger references so laptop capacity does not set the scientific ceiling. Exclude base-only checkpoints, unrelated modality specialists, and unofficial modified derivatives from the experimental shortlist.

Sources checked: publisher model cards and deployment documentation; benchmark repositories; one independent evaluator's dated analysis; and related methodological research. Search phrases included exact model IDs, reasoning settings, newer Granite/Mistral/Nemotron releases, independent open-weight comparisons, and Morgan GPU resources. Search snippets were used for discovery; substantive decisions below link to opened primary sources.

This review establishes a justified experimental sample, not the current global top three. No model weights were downloaded, no publisher scores reproduced, and no local Ollama artifacts inspected.

## Original candidate set

Upstream mappings below remain provisional until the local digest and Modelfile are inspected. In particular, `deepseek-r1:8b` cannot be resolved from the tag name alone.

| Local candidate | Publisher checkpoint / identity issue | Decision for new experiments |
|---|---|---|
| `llama3.2:3b` | [Llama-3.2-3B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct); custom Llama 3.2 license | Archive as small historical baseline; no new core slot |
| `phi4-mini-reasoning:3.8b` | [Phi-4-mini-reasoning](https://huggingface.co/microsoft/Phi-4-mini-reasoning); MIT | Survey only unless small-model efficiency becomes primary |
| `qwen2.5:7b` | [Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct); 7.61B, Apache-2.0 | Preserve pilot baseline; no evidence it is a current universal winner |
| `deepseek-r1:8b` | Could require distinguishing [original Llama 8B distill](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-8B) from [0528 Qwen3 8B](https://huggingface.co/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B) | Resolve identity; do not assign scores from the full R1 model |
| `qwen3:8b` | [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B), documented thinking switch | Compatibility fallback; also useful if continuity with the pilot is required |
| `granite3.3:8b` | [Granite-3.3-8B-Instruct](https://huggingface.co/ibm-granite/granite-3.3-8b-instruct); Apache-2.0 | Keep in survey; screen newer Granite for experimental role |
| `deepseek-r1:14b` | Likely [R1-Distill-Qwen-14B](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B), pending local verification | Reserve specialist; redundant to test every distill size without a scaling question |
| `phi4-reasoning:14b` | [Phi-4-reasoning](https://huggingface.co/microsoft/Phi-4-reasoning); MIT | Proposed specialist comparator, deliberately historical |

The student-reported DeepSeek 7B result belongs to another checkpoint. It must not be relabeled as an 8B result. Pilot percentages are not repeated in the evidence ledger because their raw artifacts and model identities have not been audited.

## Newer and larger candidates

| Exact checkpoint | Relevant documented feature | Assessment for this study |
|---|---|---|
| [Qwen/Qwen3.5-9B](https://huggingface.co/Qwen/Qwen3.5-9B) | Hybrid attention architecture; thinking/non-thinking; Apache-2.0 | Proposed newer capability challenger; test text only |
| [Qwen/Qwen3.6-27B](https://huggingface.co/Qwen/Qwen3.6-27B) | Larger post-trained model; serving and reasoning guidance | Strong larger deployment reserve, conditional on actual resources |
| [google/gemma-4-12B-it](https://huggingface.co/google/gemma-4-12B-it) | Thinking controls; Apache-2.0; multimodal architecture | First cross-family replacement option if practical selection takes priority over pilot diagnosis |
| [ibm-granite/granite-4.0-h-small](https://huggingface.co/ibm-granite/granite-4.0-h-small) | Earlier hybrid Granite alternative | Background; do not automatically equate newer dense releases with the same architecture |
| [ibm-granite/granite-4.1-30b](https://huggingface.co/ibm-granite/granite-4.1-30b) | Dense predecessor with documented benchmark protocols | Background; newer reasoning release available |
| [ibm-granite/granite-4.2-8b](https://huggingface.co/ibm-granite/granite-4.2-8b) | Full, non-thinking, and low-effort modes; same stated sampling settings across modes; Apache-2.0 | Proposed anchor for controlled mode experiment |
| [ibm-granite/granite-4.2-30b](https://huggingface.co/ibm-granite/granite-4.2-30b) | Larger dense model in the same new family | Reserve for a scaling study; not needed for the minimum experiment |
| [deepseek-ai/DeepSeek-R1-0528-Qwen3-8B](https://huggingface.co/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B) | Specifically identified Qwen3-based reasoning distillation | First specialist replacement if DeepSeek is required by the professor |
| [openai/gpt-oss-20b](https://developers.openai.com/api/docs/models/gpt-oss-20b) | 21B total / 3.6B active; low/medium/high effort; Apache-2.0 | Useful MoE/effort alternative; adds precision and Harmony-interface considerations |
| [openai/gpt-oss-120b](https://developers.openai.com/cookbook/articles/gpt-oss/run-transformers) | Larger downloadable alternative; documented quantized deployment | Larger reference, not a default experimental commitment |
| [nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16) | 30B total / 3.5B active hybrid MoE; NVIDIA-specific license | Interesting serving-efficiency alternative; outside minimal dense-model comparison |
| [mistralai/Mistral-Small-4-119B-2603](https://huggingface.co/mistralai/Mistral-Small-4-119B-2603) | 119B/A6B class; none/high reasoning controls | Survey-level larger alternative; name does not imply a small memory footprint |

License labels summarize publisher disclosures, not a legal clearance. Pin and preserve the actual license and derivative notices for the chosen artifact. Open-weight is the appropriate broad term; downloadable weights do not imply identical openness or training-data availability.

## Published observations: not a sortable leaderboard

These observations are recorded to show evidence of relevant capability and expose protocol differences. Missing values are not zero. Row order has no performance meaning.

| Checkpoint | Publisher-reported observation | Limits on comparison |
|---|---|---|
| Qwen3.5-9B | MMLU-Pro 82.5; GPQA Diamond 81.7; IFEval 91.5 | Mode, budget, scorer, and precision must match before reproducing or comparing |
| Qwen3.6-27B | GPQA Diamond 87.8; LiveCodeBench v6 83.9 | Larger model; benchmark/scaffold details matter; not a controlled size comparison |
| Phi-4-reasoning | MMLU-Pro 74.3; GPQA-D 65.8; IFEval Strict 83.4 | Microsoft evaluation; IFEval Strict is not automatically another report's unspecified IFEval metric |
| Granite-4.2-8B | MMLU-Pro 74.04; GPQA 64.14; LiveCodeBench v6 73.24 | GPQA is labeled without Diamond in the displayed table; preserve that ambiguity |
| Granite-4.2-30B | MMLU-Pro 77.60; GPQA 66.41 | Same publisher table, but all underlying conditions still need verification |
| DeepSeek-R1-Distill-Qwen-14B | MATH-500 pass@1 93.9; GPQA Diamond pass@1 59.1 | Original report uses up to 32,768 generation tokens and repeated sampling where applicable |
| DeepSeek-R1-0528-Qwen3-8B | AIME24 86.0; AIME25 76.3; GPQA Diamond 61.1 | Report describes 64K generation and 16 responses per query for sampled pass@1 estimates |
| Nemotron-3-Nano-30B-A3B-BF16 | MMLU-Pro 78.3; GPQA without tools 73.0 | Do not combine with its tool-enabled scores; protocol not fully audited here |

Sources are the corresponding model cards linked above. The [CSV ledger](05-evidence-ledger.csv) attaches a direct source and caveat to each numeric observation.

Gemma 4 12B's page exposes GPQA/MMLU-Pro evaluation metadata, but attribution and protocol were not resolved sufficiently here to use those numbers in selection. GPT-OSS capability and deployment were verified from official OpenAI documentation; this review does not substitute another publisher's comparison table for an independently reproduced GPT-OSS result.

## Independent evidence and what it does not establish

An April 13, 2026 [Artificial Analysis study](https://artificialanalysis.ai/articles/sub-32b-open-weights) reports substantial differences in accuracy-index scores and output consumption between reasoning/non-reasoning configurations of Qwen3.5 27B and Gemma 4 31B. This is useful independent motivation for measuring tradeoffs. It concerns different sizes from the proposed small candidates and a dated composite index. Do not transfer those scores to 9B or 12B checkpoints, or treat the index as Morgan's utility function.

[LiveBench](https://github.com/LiveBench/LiveBench) publishes model/configuration mechanisms and versioned benchmark machinery. The live leaderboard did not expose numeric rows to the browser used in this review, so no current LiveBench rankings are claimed. Its README also distinguishes available public releases from other evaluation data. Reproducibility requires an accessible frozen release, not just a leaderboard name.

No fully audited, protocol-matched independent evaluation covering all three proposed research checkpoints was established in this rapid review. That is a reason for a limited local replication on the GPU, not permission to invent a common ranking.

## Evidence classification

Use two independent labels: provenance (publisher, independent evaluator, or this project) and comparability (matched, partially specified, or insufficient). Publisher origin alone neither proves nor invalidates a result. A common table alone does not prove matching settings.

All cross-publisher numeric comparisons above are at most partially specified for this review. Do not average their scores, rank-normalize them, or claim that one checkpoint's percentage-point advantage predicts Morgan task performance.

## Configuration findings that change the plan

- Granite 4.2 documents temperature 1.0 and top-p 0.95 across modes. This supports a same-sampler within-checkpoint comparison, pending runtime validation.
- Qwen3-8B explicitly discourages greedy decoding in thinking mode. Its documented non-thinking sampling differs, so native-mode comparison can also change sampling.
- Qwen3.5-9B's card has differing non-thinking reasoning recommendations in separate sections. Select and record one documented recipe during development; do not silently mix them. Its long-output guidance also means a short budget must be described as constrained evaluation.
- Phi-4 Reasoning documents temperature 0.8, top-k 50, top-p 0.95 and a specific system/template structure. Its pilot failures cannot establish an intrinsic defect before interface and configuration checks.
- DeepSeek's 0528 instructions differ from the original R1 guidance, including system-prompt treatment. Match guidance to the exact checkpoint.
- GPT-OSS uses Harmony. Quantized memory guidance depends on the supported backend and hardware; a nominal size or VRAM headline is not a service-capacity guarantee. [Official deployment guide](https://developers.openai.com/cookbook/articles/gpt-oss/run-transformers)

## Survey conclusion

The original set remains useful historical coverage but is not an adequate frozen representation of the current model landscape. A three-checkpoint research sample can be justified by experimental roles, while newer and larger alternatives remain visible in the report. The experimental shortlist should be finalized after hardware and professor expectations are confirmed, before inspecting held-out results.

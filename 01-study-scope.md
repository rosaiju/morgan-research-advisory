# Proposed study scope

> Superseded proposal. Use [06-independent-protocol.md](06-independent-protocol.md). Do not execute the earlier design below.

Prepared September 29, 2026. Advisor proposal; professor agreement and project deadline are pending.

**Working title:** Reasoning Accuracy, Completion, and Deployment Tradeoffs in Selected Open-Weight Language Models for a University Service.

**Purpose:** survey open-weight model options, then investigate how supported inference configurations affect correct answer delivery. Use the findings to recommend an evaluated configuration for a Morgan-hosted prototype. Do not claim universal model superiority or production readiness.

## Research questions

**A. Capability:** How do thinking mode and generated-token allowance affect final-answer accuracy and completion on deduction and mathematical problem-solving tasks? How do two additional model configurations compare under a common declared task protocol?

**B. Deployment:** For the strongest practical configurations, what latency, memory use, completion rate, and request capacity are observed on the actual Morgan allocation?

**C. University application:** Can the configurations answer a small set of university questions using the same verified supporting passages? This is an exploratory evidence-use check, not a validation of an academic advising service.

Capability is the main empirical contribution. Deployment is a bounded feasibility test. University application is a small transfer check. Report each separately.

## Why this scope

The original pilot exposed sensitivity to output ceilings, decoding, formatting, and infrastructure interruptions. Those observations motivate a controlled experiment; they do not establish which model reasons best. A broader literature survey satisfies the need to examine more models without testing every candidate extensively.

Prior work already studies multiple metrics and deployment tradeoffs. This project should be described as a reproducible undergraduate study and local feasibility assessment, not the first work to consider these issues. [HELM](https://arxiv.org/abs/2211.09110) motivates scenario-specific, multi-metric reporting. A recent [deployment-aware evaluation preprint, v3](https://arxiv.org/abs/2604.07035v3) reports configuration-sensitive rankings; its abstract was reviewed for related-work screening, not its complete experimental artifacts.

## Minimum experimental design

Use three checkpoints provisionally identified in the [selection decision](04-shortlist-decision.md). The initial design has six conditions:

| Checkpoint role | Mode | Output allowance |
|---|---|---|
| Granite 4.2 8B, controlled comparison | Thinking | Lower and higher |
| Granite 4.2 8B, controlled comparison | Non-thinking | Lower and higher |
| Qwen3.5 9B, challenger | Thinking | Higher |
| Phi-4 Reasoning, specialist comparator | Native reasoning | Higher |

The first two rows represent four conditions. The last two add two conditions. Keep the same question set across all six. This is a within-model experiment plus cross-model comparison; it is not a fully crossed three-model factorial design.

Proposed starting allowances are 4,096 and 16,384 generated tokens, including reasoning and final answer. These are planning values only. Validate them on separate development items; if frequent truncation makes the higher condition uninformative, either increase it once within the compute budget or explicitly narrow the claim to performance under a restricted allowance. Do not tune using held-out test outcomes.

Use supported native templates. Hold sampling fixed across Granite modes, subject to later verification of the pinned implementation. Other models use preregistered documented settings. Even this controlled experiment estimates the effect of the supported mode switch, not a philosophical or mechanistic measure of internal reasoning.

## Task selection and data separation

- Deduction: select BBH task variants for logical deduction, tracking shuffled objects, and reasoning about colored objects. Preserve the reference wording and scoring rules. [BBH source](https://github.com/suzgunmirac/BIG-Bench-Hard)
- Mathematics: use a stratified subset of MATH-500, with a reviewed equivalence scorer. [Dataset](https://huggingface.co/datasets/HuggingFaceH4/MATH-500)
- University transfer: later create a small independently checked set using public catalog passages and fictional student records. Supply identical correct passages to every model; full retrieval is deferred.

A planning envelope is 120-200 unique reasoning questions, balanced across the two families, with three independently sampled attempts per condition. That is 2,160-3,600 generations for six conditions. It is not a power calculation or a promise that GPU time is sufficient. A later small pilot must determine the affordable count. Preserve a separate development set, save the final item manifest, and freeze the design before test generation.

If resources are tight, remove an optional extension or reduce the declared scope before final testing. Do not silently drop difficult items. Do not count repeated generations as independent questions. If uncertainty remains large, report an inconclusive comparison instead of forcing a winner.

## Measurements and analysis

Primary: correct final answers / all assigned items, averaged across attempts. Secondary: valid completion / all assigned items. Also report correctness conditional on completion as a diagnostic, never alone.

Record termination reason, final-answer presence, format validity, correctness, and repetition flag separately. Invalid and truncated attempts count as unsuccessful in the practical task-success estimate. Record machine interruptions separately and apply a predefined infrastructure retry policy consistently.

Report paired differences and question-clustered uncertainty. Stratify by task family. Keep full traces for diagnosis; do not award points for trace length or plausible-looking intermediate conclusions. Use each benchmark's answer convention, not a universal extra `FINAL:` demand.

For deployment, record both time to first token and time to first user-visible answer token, end-to-end latency, peak VRAM, completed requests per second, and errors. Token counts alone do not normalize computation across models.

## Included deliverables

1. Broad candidate survey with comparison limitations and source provenance.
2. Versioned protocol, item manifest, generation records, and scoring documentation.
3. Controlled capability results and uncertainty analysis.
4. A limited server test at a few loads and one demonstration through the existing prototype.
5. A final report with conditional recommendations and explicit unresolved questions.

## Deferred work

Fine-tuning, a multi-model router, multimodal evaluation, full RAG optimization, private student-data integration, autonomous tools, production launch, and a full Ollama-versus-vLLM experiment are outside the minimum scope. A short configuration or compatibility check is allowed during later setup; no setup is performed by this planning package.

## Completion criteria and boundaries

The study is complete when it can explain observed differences under frozen conditions, identify a feasible tested operating configuration or explain why none qualified, and provide enough artifacts to repeat the experiment. A universal winner is not required.

The existing laptop pilot remains a development case study. Its raw artifacts have not been audited here. No new local overnight benchmark should be launched solely to fill a comparison table.

Remaining scope decisions: professor agreement with the primary question, submission date, whether a live GPU demonstration is required, and the GPU-hour/time budget. Until those are known, this is a reviewable proposal rather than an agreed institutional research plan.

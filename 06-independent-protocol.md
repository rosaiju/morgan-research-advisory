# Independent evaluation protocol for Morgan State

**Historical proposal:** conflicting selection, sample-size, and inference provisions are superseded by [13 current protocol](13-protocol-after-audit.md). Use [12 current candidate registry](12-candidate-pool-revalidated.md). No experiment is authorized by this document.

Proposed September 29, 2026. For review before execution. No new benchmarks, model downloads, deployments, or GPU inspections were performed. This document supersedes the earlier reasoning-mode-centered proposal and its Granite/Qwen/Phi trio.

## 1. Decision and research question

Use a staged comparative evaluation: broad published-evidence screening, a small controlled screening study only where evidence is insufficient, then a held-out evaluation of three or four finalists. Conclude with conditional deployment recommendations. Write the final survey and results abstract after the experiments. Literature notes and this protocol are preparation, not finished empirical findings.

Question: Which evaluated open-weight model configurations provide strong text reasoning and reliable answer delivery, and which can support a university service on Morgan's confirmed infrastructure?

The experimental unit is a checkpoint plus template, precision, reasoning mode, decoding settings, and serving implementation. We cannot isolate intrinsic intelligence by changing all of these at once. Conclusions apply to evaluated configurations and tasks, not all possible configurations or intelligence in general.

Three separate outcomes:

* A, capability: reasoning-task accuracy and instruction following, with uncertainty and budget limits.
* B, deployment: resource use, latency, throughput, and operational reliability on confirmed hardware.
* C, application: correctness and grounding for a defined university workflow.

Do not combine A/B/C into a single score. Use separate benchmark results and an accuracy/resource tradeoff plot. A recommendation can be conditional: a quality-oriented choice and a lower-resource choice, rather than a universal winner.

## 2. Why this approach

Published evidence alone cannot settle deployment or resolve incompatible evaluation recipes. Exhaustively testing every release wastes effort and creates multiple-comparison problems. Screening all old laptop downloads preserves selection bias. A mode/budget ablation is informative but should not replace model selection as the central research question.

The chosen approach uses publications to remove clearly irrelevant or redundant candidates; our compute addresses unresolved comparisons. Similar concerns about evaluation setup and reporting appear in [Laskar et al.](https://aclanthology.org/2024.emnlp-main.764/) and [BetterBench](https://arxiv.org/abs/2411.12990). These sources motivate transparency, not a claim that our exact sample sizes or thresholds are established standards.

## 3. Verified facts and unresolved assumptions

Verified in this work: cited publisher cards and framework documentation exist; the source ledger contains published observations; several new releases postdate the original candidate pool. The prior pilot results, laptop specifications, and Morgan GPU access are user-reported and have not been audited against raw records or hardware.

Unknown: assigned GPU model/count/VRAM/interconnect, sharing policy, scheduler, available GPU-hours, operating system, software permissions, data rules, deadline, anticipated users, required latency, and grading requirements. No public announcement establishes this student's allocation. No assumed A100/H100/H200 configuration is used in selection.

Working scope: English text, single-turn reasoning, no external tools in A. Multimodal features are outside the primary experiment. Three or four finalists is a workload target, not a scientifically required number.

## 4. Freeze and evidence screening

Candidate discovery cutoff: September 29, 2026. Releases after the cutoff go into future work unless a documented pre-test amendment replaces an unavailable artifact. Never add a model after seeing held-out results to obtain a preferred winner.

The initial pool and dispositions are in [07](07-candidate-decisions.md). For each candidate record exact model ID, release/revision, downloadable artifact and license, total and active parameters when applicable, precision, documented modes, serving support, and benchmark provenance. Freeze weight revision, tokenizer/template hash, and software commits before execution. Current model-card links are mutable and are not immutable snapshots.

Evidence is classified independently by provenance (publisher / independent / this project) and comparability (matched / partly specified / insufficient). A common publisher table is not automatically matched. An independent endpoint can still use undisclosed precision or a different model revision.

Only compare numbers directly when dataset revision/split, prompt and shots, tools, scoring, generation budget, attempt aggregation, reasoning mode, and relevant artifact details match. Otherwise retain parallel observations and caveats; do not average or rescale them. Missing values are not zero. Distinguish sampled pass@1 estimates from pass@k, majority vote, and best-of-N.

Exclude from new screening: base-only checkpoints, unavailable weights, untraceable derivatives, narrowly specialized models outside the text-service scope, and redundant older variants with no distinct evidence or deployment role. Old age alone is not proof of inferiority. Retain one historical baseline only if continuity is a research question; it does not consume a finalist slot by default.

Hardware eligibility is a second gate. A model that cannot be hosted on the confirmed allocation remains in the capability survey, labeled untested for deployment, rather than being called unintelligent. Active MoE parameters do not represent weight-storage requirements.

## 5. Development checks before screening

Use 12 non-evaluation smoke-test prompts per configuration to verify template, reasoning/final channel separation, stop tokens, context accounting, scorer interface, and completion. These prompts check mechanics, not model rankings. Do not optimize prompts against the final set. Inspect rendered prompts and actual server settings; an API accepting a parameter does not prove it was applied.

Use documented native templates and inference guidance. Default primary reasoning mode is the publisher's default reasoning configuration, explicitly recorded; where no default exists use its published benchmark recipe. If contradictory guidance exists, resolve the conflict before scoring and record the chosen source. This compares documented configurations, not hypothetical optimally tuned models. Fix broken integration before labeling a capability failure.

Primary proposed output ceiling: 32,768 total generated tokens including reasoning and final output. This is a bounded study, not unlimited capability or a guaranteed sufficient allowance. Ensure context >= rendered input + ceiling + required special tokens within the supported context. Do not retain the old 8,192 context automatically.

The 12-prompt mechanics check also estimates runtime but is not a representative accuracy estimate. If completion is poor, review templates and budgets before freezing the screening protocol. If an expansion is needed, apply the declared policy to every candidate; do not rescue only favorites. A 65,536-token arm is a possible amendment, not a promise to run it. If infeasible, retain 32,768 and state the bounded estimand.

Do not impose the laptop's 1,200-second timeout on capability testing. Set a generous watchdog from measured GPU operation; report any time-censored requests explicitly. Infrastructure interruptions are invalid attempts retained in logs and rerun once after correction. Valid model truncations/wrong answers are not retry opportunities. Persistent infrastructure failure is missing evidence, not a model-accuracy zero.

## 6. Controlled screening where needed

Published evidence currently does not establish a fully matched ordering of the proposed compact pool. Therefore propose screening all eligible compact candidates, rather than naming final winners now. Larger candidates can enter under the hardware rule in 07. Do not run this on the CPU laptop overnight.

Proposed screening panel: 60 MMLU-Pro items balanced across subjects, 30 MATH-500 items stratified by subject/difficulty, 46 BBEH items (two per task if the pinned release has 23 tasks), and 20 IFEval prompts. Two independent generations per item: 312 requests per candidate. The IFEval panel is a separate instruction-following diagnostic. Confirm task counts from the pinned dataset before sampling.

Sampling: seed 20260929; stable sort by dataset item ID, stratify as described, then sample with a pinned random implementation. Publish item-ID manifests and hashes, not only the seed. Allocate development, screening, and final sets disjointly, checking content duplicates. Official mini subsets may overlap the full dataset and must not be assumed independent.

Report accuracy per benchmark, completion, errors, tokens, and resource observations. Do not infer a strong ranking from a one- or two-question advantage. A small screen selects informative finalists; it is not a publication-quality general ranking.

Finalist-selection rule, fixed before results:

1. Exclude configurations with unresolved integration or license/access blockers from deployment testing; retain the reason and capability evidence.
2. Identify tradeoff candidates using the three reasoning benchmark accuracies and measured memory. A screening disadvantage is practically material at 5 percentage points; this is a declared project tolerance, not a statistical constant.
3. Remove a candidate for evidence of inferiority only when another is at least as good within that tolerance across all three reasoning domains, better by at least the tolerance in one, and requires no more measured memory. Require paired uncertainty analysis to support the differences; overlapping uncertain estimates do not establish inferiority. Use instruction-following failures to flag a service limitation, not secretly change the reasoning score.
4. Aim for three or four finalists spanning the strongest observed reasoning profile, a lower-memory competitive option, and a credible alternative configuration/family. Family diversity breaks uncertain ties; it never overrides clear evidence of superiority.
5. If too many remain and evidence is inconclusive, add ONE preallocated screening tranche of the same size for all remaining ambiguous candidates, disjoint from the final set. If more than four still remain, prefer coverage of distinct measured tradeoffs, then lower memory, then stronger matched published evidence; log the choice. State that omitted near-ties were budget exclusions, not demonstrated losers. Fewer than three may suffice if eligibility is narrow.

No composite A/B/C ranking or forced statistically significant winner. No mandatory DeepSeek/Phi/Granite finalist. All candidate eliminations get a written disposition.

For operational clarity, the screening elimination check uses paired 95% question-cluster bootstrap intervals: the proposed replacement's lower difference bound must exceed -5 points in every reasoning domain and exceed +5 points in at least one, with no higher measured memory. This conservative exploratory rule will often leave ties. It is not a family-wise significance claim across all pairs; no formal superiority claim follows from screening. Exact boundary ties remain eligible. Bootstrap 10,000 resamples with seed 20260929; retain all repeats within a question and strata. Final reporting uses a fresh held-out sample.

## 7. Full capability evaluation

Proposed final panel: 280 MMLU-Pro items (20 per subject if the pinned release has 14), 150 MATH-500 items stratified by topic/difficulty, 230 BBEH items (10 per task if 23), and 100 IFEval prompts. These are held-out subsets, not official full-benchmark scores. Use original task prompts/few-shot examples and official scoring conventions through a pinned implementation; document any adaptation.

Three independent generations per item: 2,280 requests per finalist, or 6,840–9,120 for three–four finalists. Three repeats improve estimation of sampling variability but do not triple the number of independent questions. If this exceeds available GPU-hours, reduce the number of finalists or freeze a smaller stratified panel before results, and narrow claims. Never quietly stop a model early because it is losing.

Predeclared lean alternative if the measured runtime cannot fit the allocation: three finalists, 140 MMLU-Pro + 100 MATH-500 + 115 BBEH + 50 IFEval items, two generations each = 2,430 total final requests. Use the same disjointness and stratification rules and omit the secondary budget arm. Choose standard versus lean before screening results are opened, based on available compute and timing alone. Report wider uncertainty and avoid fine-grained subject claims. This alternative prevents the full proposal from becoming an unnecessarily large undergraduate experiment.

Primary metric: mean single-attempt correctness over all valid scored tasks within each benchmark. Score valid no-answer/truncation as zero and show completion separately. Also show accuracy conditional on submitted answers, clearly labeled because it can favor selective completion. Final-answer correctness uses the established scorer, not a universal custom FINAL marker. A mechanically correct answer in the final response can be graded according to that scorer; correctness found only in a reasoning trace does not count as delivered output.

Preserve per-attempt failure flags: wrong answer, no answer, format/extraction failure, truncation, watchdog timeout, repetition, infrastructure error. These may overlap; provide an exclusive terminal-status field for totals. Do not automatically stop repetitions in the capability arm using a heuristic that changes the effective budget across models.

Report 95% intervals and paired differences on common items using a stratified cluster bootstrap over questions, carrying all repeats together. This estimates uncertainty for the declared sampling design, not humanity's full task distribution. Show domain sample sizes and unweighted subject/task macro averages alongside item-weighted accuracy. Predeclare any significance tests and multiplicity correction; otherwise use descriptive uncertainty without claims of formal superiority. Publish distributions, not just means. Accept inconclusive comparisons.

A secondary efficiency arm uses 8,192 total output tokens on 20% of final reasoning items, selected before outputs, with the same configuration and three repeats. Report it as an accuracy/budget sensitivity study, never mix its score into the primary arm. Tokens differ across tokenizers and are not equal FLOPs; measure time and GPU use separately. No accuracy-per-token ratio as the sole objective, since tiny inaccurate models can look artificially efficient.

Visible reasoning traces support qualitative failure analysis only. They do not demonstrate faithful internal reasoning, and length is not quality. Select trace cases by a declared sample plus failure categories; label illustrative examples rather than assigning subjective intelligence points.

## 8. Serving and university application experiments

Use a pinned supported serving engine for A; prefer vLLM on compatible Morgan hardware, with a documented alternative if unsupported. Compare Ollama/vLLM/SGLang only as B after selecting a checkpoint and precision. A backend change needs a small correctness check because templates, kernels, and quantization may change outputs. It is not a pure speed comparison if artifacts differ.

On confirmed GPUs record GPU type/count/VRAM, drivers, CPU/RAM, interconnect, model precision, offload, context limits, batch settings, cache policy, and competing load. Measure cold load separately from warm operation.

B workload: short/medium/long input bins defined by source text and observed token counts, e.g. approximately 1K/4K/16K; short and long response requests; both synthetic fixed-length load and realistic completions, reported separately. Start concurrency 1,2,4,8,16 and stop at memory failure or unacceptable queue growth. Repeat steady-state windows at least three times. Add open-loop arrivals to expose queuing; closed-loop concurrency alone masks overload. Record achieved request rate, completed requests, output tokens/s, p50/p95 TTFT, time to first user-visible answer for reasoning models, p50/p95 total latency, errors, OOMs, queue delays, and peak memory. Do not interpret the first reasoning token as the first useful answer.

Use warm-up, randomized condition order, fixed workload manifest, and stated prefix-cache behavior. Benchmark runtime from request arrival, including queue delay. Report interval/sample count for tail metrics and do not claim stable p99 from tiny samples. Cancel/reconnect, server restart, one-hour mixed-load soak, and stalled-client handling are bounded reliability checks. [vLLM's serving benchmark](https://docs.vllm.ai/en/latest/cli/bench/serve/) can supply load tooling; it is not model-intelligence evidence.

Service-level targets (acceptable delay, concurrency, availability) must be agreed with Morgan, not invented as university requirements. Show curves before a target exists. Quantization is an explicit configuration change: check paired quality against the reference on a fixed subset and report memory/latency tradeoffs.

C is a separate optional case study after defining a real use case: 30–50 answerable/unanswerable questions against a frozen set of public Morgan documents, verified reference answers and citations. Use the same retriever/documents for model comparisons; separately measure retrieval recall and answer grounding. Compare with/without retrieval where useful. Tool tasks use mock read-only APIs with known expected arguments; measure tool selection, schema validity, argument correctness, and end-to-end success. Include irrelevant/adversarial retrieved instructions and missing information. Do not claim production readiness from a small demo. A reasoning winner can lose the application comparison.

## 9. Existing pilot and execution sequence

Preserve v1/v2 with exact settings and provenance. Do not combine their percentages with this study. Completion of the old run is optional supporting evidence, not a prerequisite; its current status is unverified. No stopping or restarting it is authorized by this proposal. Corrections to a genuine grading/runner bug require a versioned amendment, archived original results, and consistent rescoring/reruns of affected conditions. Do not redesign questions to rescue expected winners.

Sequence: review protocol -> confirm resources -> freeze pool/artifacts/configs -> mechanics check and runtime estimate -> freeze manifests and statistical plan -> screen -> document eliminations -> freeze finalists -> run held-out A -> run B -> optional C -> write results, final survey, and abstract -> archive reproducibility package.

Time estimate must come from measured token lengths and GPU service times. For serial work, sum prefill + generated tokens/decode rate + overhead across requests; batching and concurrency require measured throughput. State actual sample counts and a contingency allowance. No defensible fixed overnight completion promise exists now.

Completion package: source ledger and search log; inclusion/exclusion table; pinned environments and manifests; raw outputs/statuses; scorer version; per-benchmark results with uncertainty; deployment curves; limitations; conditional recommendation; final abstract reflecting actual findings. Review approval concerns this concrete protocol, not an already chosen winner.

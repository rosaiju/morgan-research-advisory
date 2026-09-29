# Benchmarks and framework decisions

**Audit corrections take precedence:** use [13 current protocol](13-protocol-after-audit.md) for exact dataset, scoring, context-budget, and selection corrections. The earlier sample sizes referenced below are not current instructions.

Proposed September 29, 2026. Benchmark names alone do not define a reproducible experiment. Pin datasets, prompts, scoring code, task implementation, and sample manifests. The sample counts in 06 are planning choices, not power guarantees.

| Instrument | Decision | What it contributes and does not establish |
|---|---|---|
| [MMLU-Pro](https://github.com/TIGER-AI-Lab/MMLU-Pro) | Primary broad academic component | Knowledge plus reasoning across subjects; not pure reasoning independent of learned knowledge. Use generation-based answers for reasoning models. |
| [MATH-500](https://huggingface.co/datasets/HuggingFaceH4/MATH-500) | Primary mathematical component | Checkable mathematical answers; narrow domain and possible training exposure. Pin mathematical equivalence scorer and audit ambiguous parses. |
| [BBEH](https://github.com/google-deepmind/bbeh) | Primary diverse hard-reasoning component | Harder successor to BBH; official full/mini sets exist. Task-level stratification prevents one task type dominating. |
| [IFEval](https://github.com/google-research/google-research/blob/master/instruction_following_eval/README.md) | Separate instruction-following component | Verifiable constraints; report strict prompt-level and instruction-level metrics separately. Not an intelligence measure. |
| [BBH](https://github.com/suzgunmirac/BIG-Bench-Hard) | Optional diagnostic, not default full suite | Deduction/object tracking fits the professor's examples; possible ceiling limits for newer models. Useful to diagnose a floor on harder tasks without changing the primary benchmark after seeing results. |
| [GPQA Diamond](https://github.com/idavidrein/gpqa) | Published evidence; optional extension | Expert science knowledge plus reasoning; demanding and narrow. Do not let it stand for the whole university service. Check access/license and exact split. |
| GSM8K | Historical context/smoke test only | Easy arithmetic can have limited discrimination for strong candidates. Do not add it merely because a runner supports it. |
| AIME | Supplementary published mathematical evidence | Small annual sets produce unstable rankings and contest math is narrow. Repeated samples do not create new independent problems. |
| [EvalPlus](https://github.com/evalplus/evalplus) / [LiveCodeBench](https://livecodebench.github.io/) | Conditional coding extension | Use if coding is an explicit service requirement; executable tests help objective grading, but sandboxing and problem dates/runtime must be pinned. Do not infer coding quality from MATH. |
| SWE-bench / Terminal-Bench / agent leaderboards | Survey context, not core single-turn capability test | Results depend on tools, scaffold, environment, task patches, turns, and budget. Large agent experiments exceed the minimum scope. |
| Chat preference arenas / LLM-judge composites | Contextual evidence only | Preference, style, model mix, and judge behavior differ from objective reasoning correctness. |
| Private or moving leaderboards | Shortlisting leads only unless protocol accessible | A versioned independent result can be useful; private data prevents full replication and moving composites cannot be merged across releases. |

Do not conclude that a benchmark is universally obsolete merely because frontier models saturate it; inspect relevance and score range for our candidate class. Conversely, a hard benchmark is not automatically relevant. Benchmarks selected here sample capabilities; none operationalizes all intelligence.

## Framework choice

Choose **Inspect AI with pinned Inspect Evals tasks** as the default orchestration layer, conditional on a mechanics check establishing correct templates, reasoning/final separation, task scoring, and access to these datasets. Its evaluation-set support is useful for managing repeated, resumable runs. [Inspect documentation](https://inspect.aisi.org.uk/eval-sets.html), [task repository](https://github.com/UKGovernmentBEIS/inspect_evals).

If an exact chosen task/protocol is better supported by [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness), use that implementation instead of recreating it. Generation and likelihood task modes answer different questions; next-token multiple-choice likelihood alone does not allow an explicit reasoning model to perform its normal generation process.

[EvalScope](https://github.com/modelscope/evalscope) is a credible alternative combining evaluation and performance tooling. [OpenCompass](https://github.com/open-compass/opencompass) provides broad model/task coverage. Neither is selected simply for catalog size. Do not benchmark the frameworks themselves or integrate three frameworks just to appear comprehensive. One runner plus official scorers and one serving load tool is the intended minimum.

Mandatory task audit: read the exact implementation and defaults. Even the MMLU-Pro repository currently documents optional retries of wrong answers in one API workflow. Such options must be disabled for single-attempt evaluation; a reputable repository does not make every example command an appropriate protocol. Pin zero semantic retries, retain failure logs, and distinguish transport retries from new attempts. [Repository documentation](https://github.com/TIGER-AI-Lab/MMLU-Pro)

## Fairness decisions

Identical task content, scorer, attempt count, and budget policy are controls. Identical chat-template strings or temperature across architectures are not inherently fair. Use supported native interfaces and declared publisher recipes. A comparison of these configurations answers a practical selection question; it does not identify a causal architecture effect.

Use the same total output-token ceiling for the constrained arm, while acknowledging tokenizer and reasoning-mode differences. Show completion and resource use. A short-budget failure is meaningful for that service constraint but not evidence of unlimited reasoning incapacity. A separate generous budget does not become unlimited merely by being larger.

No manual rescue of an answer discovered inside a trace. No reward for verbosity. No best-of-N substitution for mean single-attempt accuracy. No tuning from held-out errors. No copying a model's recommended agentic 100K+ token budget into a small reasoning experiment without a feasibility decision.

Source-driven examples: Qwen3.8 documents thinking temperature 1.0/top-p .95 and a different non-thinking recipe, plus effort levels. GPT-OSS requires correct Harmony handling. These motivate configuration records, not special treatment after a model loses. [Qwen guidance](https://huggingface.co/Qwen/Qwen3.8-27B), [official OpenAI deployment guidance](https://developers.openai.com/cookbook/articles/gpt-oss/run-transformers).

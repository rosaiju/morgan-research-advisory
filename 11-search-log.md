# Search log and evidence boundaries

Review date: September 29, 2026. This is a bounded rapid evidence review. No exhaustive platform scrape, systematic-review flow counts, or complete database coverage is claimed. Exact numbers of excluded search hits were not recorded; do not reconstruct fictional PRISMA counts.

## Search batches and decisions

| Search family / representative queries | Sources examined | Outcome |
|---|---|---|
| LLM evaluation survey benchmark validity; PRISMA ScR | [EMNLP review](https://aclanthology.org/2024.emnlp-main.764/), [BetterBench](https://arxiv.org/abs/2411.12990), [PRISMA-ScR](https://www.prisma-statement.org/scoping) | Adopt explicit source/protocol reporting; do not mislabel bounded review as systematic |
| site.github.com reasoning evaluation EvalScope OpenCompass Inspect | [EvalScope](https://github.com/modelscope/evalscope), [OpenCompass](https://github.com/open-compass/opencompass), [Inspect eval sets](https://inspect.aisi.org.uk/eval-sets.html), [lm-eval](https://github.com/EleutherAI/lm-evaluation-harness) | Prefer one runner with audited task implementation; frameworks do not establish fairness |
| site.reddit.com LocalLLaMA realistic benchmarks; leaderboard sensitivity | [Practitioner thread](https://www.reddit.com/r/LocalLLaMA/comments/1t79nq0/rant_make_your_benchmarks_realistic/), [primary sensitivity paper](https://arxiv.org/abs/2402.01781) | Use social observations for discovery only; verify methodological claims in primary sources |
| site.x.com evals benchmarks Hamel; ArtificialAnlys methodology | Indexed snippets/mirrors; [direct X attempt](https://x.com/nikunj/status/2032843263372308489) failed | No X-derived ranking or community-consensus claim retained |
| site.huggingface.co/Qwen Qwen3.8 27B | [Publisher card](https://huggingface.co/Qwen/Qwen3.8-27B) | Include newer Qwen in screening; preserve generation/scaffold caveats |
| Current open weights September 2026; exact Gemma/Granite/Nemotron identifiers | Cards linked in 07; [independent evaluator methodology](https://artificialanalysis.ai/methodology/intelligence-benchmarking) | Expand current families; do not use a changing composite as university utility |
| Inkling-Small; GLM-5.3; DeepSeek V4; MiniMax-M3; Muse-Glimmer 30B | Publisher cards linked in 07 | Large models remain visible; Muse enters moderate-size pool; unsupported hardware assumptions prohibited |
| Established MMLU-Pro MATH-500 BBEH IFEval | Original repositories/cards linked in 08 | Diverse reasoning panel plus separate instruction-following evaluation |
| Efficient evaluation tinyBenchmarks | [Primary paper](https://arxiv.org/abs/2402.14992) | Do not adopt score-prediction shortcut as proof of university suitability |

## Source precedence and unresolved work

Model identity/settings: publisher card, tokenizer/config files and official deployment documentation. Benchmark definitions: official task repositories/papers. Capability evidence: matched independent evaluation when available, otherwise labeled publisher results. Deployment evidence: our future measured hardware, not marketing memory estimates or another person's laptop. Social posts: discovery only.

The 17-model current screening/reference pool is intentionally bounded and not globally exhaustive. Full report review can add a source before protocol freeze when it exposes a materially different candidate. Do not continuously chase releases after the cutoff. Search snippets alone do not establish benchmark values. New numbers E21–E28 were verified in opened publisher tables. Other candidate entries are eligibility/discovery decisions, not scored rankings.

All local prose is synthesis and proposed design, with short source-attributed facts. No full copyrighted articles were copied. The bibliography is represented by inline primary-source links; citation-manager export and immutable source snapshots remain pre-submission tasks.

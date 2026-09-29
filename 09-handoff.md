# Handoff and review checklist

**Current selection policy:** [14 capability-first shortlist](14-capability-first-shortlist.md) supersedes hardware gates and shortlist requirements here. Six capability candidates are proposed independently of Morgan hardware. Deployment analysis follows capability selection.

**Current handoff:** read [12 revalidated candidate registry](12-candidate-pool-revalidated.md) and [13 corrected protocol](13-protocol-after-audit.md) first. They supersede the nine-model screen and conflicting instructions below. Morgan hardware remains unconfirmed; no final four selected, no benchmarks or downloads performed. Next dependency is the actual resource allocation in [02](02-gpu-confirmation.md), followed by review of the protocol. Do not execute historical proposals.

Current state: proposed protocol complete for review, September 29, 2026. No new experiments executed. The user explicitly requested no long local benchmark yet. Do not interpret these documents as permission to deploy, use paid APIs, email staff, or launch the benchmark.

## Read in order

1. [06 independent protocol](06-independent-protocol.md): current research question, settings policy, sample design, selection rules, and A/B/C separation.
2. [07 candidate decisions](07-candidate-decisions.md): nine compact/moderate screening candidates plus eight larger conditional references; no predetermined finalists.
3. [08 benchmark decisions](08-benchmark-decisions.md): recommended tasks and runner, fairness rules.
4. [10 additional evidence](10-additional-evidence.csv) and [05 original evidence](05-evidence-ledger.csv): published observations with caveats, not a common leaderboard.
5. [11 search log](11-search-log.md): source coverage and limitations.

Files 00, 01, and 04 contain a superseded mode/budget-centered proposal and a preselected Granite/Qwen/Phi trio. Do not execute them. File 03 is a historical literature snapshot; its candidate recommendations are superseded by 07. File 02 remains useful as an unconfirmed resource-request checklist. README flags precedence.

## Completed

* Reconsidered the methodology independently of laptop downloads and original winners.
* Updated landscape coverage, including Qwen3.8, current Gemma variants, Muse Glimmer, and larger reference families.
* Separated broad literature screening, controlled screening, held-out final evaluation, and deployment/application studies.
* Defined outcome metrics, configuration fairness, handling of censoring, and uncertainty.
* Specified candidate dispositions and conditions for larger-model admission.
* Preserved earlier evidence and clearly superseded earlier recommendations.

## Required before execution

* User review of this proposal; actual Morgan allocation and access details; deadline and available GPU-hours. These are missing facts, not evidence against any model.
* Pin exact weight/tokenizer/template revisions, license texts, server and framework commits. Current URLs are mutable.
* Audit chosen task implementations and extraction rules, including benchmark revisions and no wrong-answer retries.
* Generate disjoint item manifests with content-overlap checks. Do not select them by observed model success. No datasets or manifests have been generated yet.
* Resolve all documented model settings in an explicit per-configuration manifest. Do not assume API parameters are supported.
* Conduct the small mechanics check only after execution is authorized. Estimate cost/time from measured generation and serving behavior.
* Freeze amendments before screening. Larger-model admission requires a documented resource/evidence decision; no unsupported claim of best available open model.

## Execution and reporting

Follow the stages in 06. A nine-candidate first screen is 2,808 requests; an optional additional tranche increases that. Full evaluation is 2,280 requests per finalist before the secondary budget arm. These are workload counts, not runtime estimates or sample-size power guarantees.

Final report structure: motivation and Morgan scope; literature search and inclusion criteria; model landscape; critique of published comparability; pilot lessons; frozen methods; screening dispositions; capability results and uncertainty; deployment results; optional university case study; limitations; conditional recommendation; reproducibility appendix.

Write the final abstract after results. It must state actual evaluated configurations, sample scope, substantive findings, and limits; no invented winner or fabricated GPU measurements. A proposal abstract can be written now only if labeled prospective.

## Important limitations for the next agent

No production repository was located or inspected. No local Ollama model digest, existing benchmark progress, raw pilot output, or GPU hardware has been audited. Literature coverage is a bounded rapid review, not a systematic census of GitHub, Reddit, X, or all models. Social discussions are discovery leads only. New published values in 10 are checked against displayed publisher tables, not reproduced. Full protocol comparability remains unresolved. Documents propose a feasible scope, not statistical proof that three repeats or four finalists are sufficient for every effect size.


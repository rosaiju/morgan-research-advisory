# Current protocol: audit corrections and hardware-conditioned selection

**Current selection policy:** [14 capability-first shortlist](14-capability-first-shortlist.md) supersedes hardware gates and shortlist requirements here. Six capability candidates are proposed independently of Morgan hardware. Deployment analysis follows capability selection.

September 29, 2026. For review, not execution. This document overrides conflicting provisions of 06–09, particularly the mandatory nine-model screen, 5-point bootstrap elimination, implicit default modes, and predetermined screening/final counts. The candidate registry is now [12](12-candidate-pool-revalidated.md). No four-model set has been frozen.

## Research design retained

Published-evidence selection followed by controlled evaluation only where it adds information. Capability, deployment and university application remain separate. Original v1/v2 remain pilot evidence. Final survey/abstract follow results. No new local overnight run, paid endpoint, weight download, or deployment is authorized by these planning documents.

The new pool is a literature/discovery pool, NOT a commitment to screen 34 models. Hardware gate first, published evidence second, optional limited empirical comparison third. An exact shortlist cannot be truthfully produced from incompatible scores and unknown resources.

## Exact decision procedure once Morgan resources are known

### Step 1: freeze facts and constraints

Record GPU vendor/model/count, physical and allocated VRAM per device, interconnect, shared/exclusive allocation, CPU RAM, permitted offload, storage, OS/driver/runtime, allowed containers/custom code, scheduler limits, GPU-hours, and access. Record target input/output lengths, concurrency and acceptable response delay as university requirements or explicitly project-defined scenarios. Do not invent Morgan requirements.

For each candidate specify one reference artifact, precision, backend, and reasoning configuration, with full revisions/hashes. Estimate weights + quantization overhead + runtime workspace + KV/recurrent state at the same requested workload. Record an estimate interval and its assumptions. A weights-only fit is insufficient. Never select from active-parameter counts or aggregate VRAM alone. Native quantization is permissible, but the comparison is of configurations.

### Step 2: apply eligibility gates uniformly

Label each entry: eligible, conditionally eligible, survey-only, or unresolved. Reasons: artifact unavailable; license incompatible with the intended use; no supported stack on the allocation; estimated memory exceeds available resources; or projected experiment exceeds allocated time. Uncertain estimates remain conditional until a small authorized load check. Do not turn hardware exclusion into a claim of lower intelligence. Retain every disposition in a table.

### Step 3: make a comparability matrix before ranking

For every potentially decisive published result record exact model/configuration, evaluator, benchmark/version/split, shots, prompt, scorer, tools, effort, output ceiling, attempts/aggregation, precision if disclosed, and whether measured or estimated. Use same-source data only when the relevant recipe is matched. Different native temperatures may be acceptable for a documented native-configuration comparison, but not for a claim of equal compute. Never combine a hosted product's scores with a similarly named released checkpoint without evidence of equivalence.

Precedence: independently measured matched protocol with accessible task/method details; then documented publisher matched protocol; then incomplete contextual evidence. This orders evidential confidence, not intelligence. Unknown fields prevent a strong dominance claim, not eligibility. Record mixed benchmark results, and never average unrelated publisher percentages or different index versions.

### Step 4: remove scope redundancy, not inconvenient competitors

Represent identical weights in different packaging once in A; compare packaging in B if useful. Do not include both predecessor and successor of the same size/role when the successor has documented within-protocol improvements and no relevant compatibility/resource loss. Keep a predecessor if that condition fails. Do not merge dense and sparse variants merely because the family is the same. Do not reserve slots by brand or geographic origin. A full DeepSeek and its Qwen-derived distill are different candidate classes.

For matched evidence, mark candidate X capability-dominated only if Y is no worse on all shared prespecified capability domains and better on at least one, with reported uncertainty sufficient to support the conclusion. Missing domains or uncertainty imply provisional prioritization, not elimination. A smaller candidate can remain deployment-relevant even when capability-dominated. Never use memory to erase a capability result.

### Step 5: choose direct evaluation or an evidence-gap study

If approximately four feasible, nonredundant, well-supported candidates remain, advance them directly to held-out A. No separate small ranking screen is required. This is the preferred route.

If more remain, first identify the actual unresolved decision. Example: dense 27B versus sparse 35B at the same allocation, or a current 8B model versus a historical reasoning distill. Do not screen all 34 to answer one such question. The candidates being compared must be frozen before their outputs are seen.

If comparable published evidence cannot narrow the feasible set enough, there is no scientifically justified unique four yet. Use a common, predeclared bridge evaluation on the remaining relevant candidates, subject to available compute, rather than converting missing evidence into a rank. Default bridge design: 140 MMLU-Pro questions (10 per subject), 100 MATH-500 questions with proportional subject/difficulty allocation, and 115 BBEH questions (5 per task, verify task count), one generation each. These 355 independent questions provide broader coverage than the old 30-question math screen; they still do not establish small-effect superiority. Add a second generation only if budget permits, fixed in advance for every bridge candidate. All bridge IDs are disjoint from the final panel.

For proportional allocation use largest-remainder rounding, with strata sorted by name to break equal remainders; seed 20260929 within stable item IDs. Freeze item manifests and content-overlap checks. No online successive elimination, extra tranche triggered by desired results, or sample-size changes after scores.

### Step 6: bridge selection rule, only if Step 5 is needed

Use the three benchmark accuracies as a capability vector; publish all three. Do not include IFEval, memory, latency, brand diversity, or application scores in this vector. Nonanswers from valid model attempts count as failures; infrastructure failures are missing attempts handled by a fixed rerun policy.

Take candidates on the capability Pareto frontier first, then the next frontier if fewer than four remain. If a frontier straddles the four-slot boundary, order that frontier by the unweighted arithmetic mean of the THREE declared capability benchmark accuracies. This is an explicit administrative selection statistic, not a measure of universal intelligence or the final reporting score. The equal weights reflect this study's three-domain design; show how changing weights would affect inclusion, but do not use that sensitivity analysis to change the selected models after results.

For exact ties, choose by ascending SHA-256 of the exact checkpoint ID plus the fixed string 'Morgan-2026-09-29'. This arbitrary tie-break is reproducible and avoids hidden family preference; label tied exclusions as budget choices. Publish paired question-cluster uncertainty for all comparisons and state when the fourth/fifth distinction is uncertain. No claim that excluded candidates are statistically inferior follows. This rule is model-agnostic and cannot guarantee identifying the true best four from finite data.

This selection produces up to four capability candidates within an already hardware-eligible pool. If the service needs a smaller model outside that group, evaluate it separately as a deployment alternative or substitute one only through a documented pre-result change to the research objective. Do not silently insert an efficiency or openness favorite after seeing results. If the feasible pool is huge and even the bridge cannot fit the budget, narrow the hardware/service scenario before results and disclose that population boundary. Four is a budget target, not a scientific law.

### Step 7: freeze the experimental set

Produce a signed-off decision table containing eligibility, evidence, redundancy status, bridge inclusion if applicable, exact configurations, and reason for advancement. Freeze before held-out generation. No final model names are selected by this document.

## Audit corrections to evaluation implementation

MMLU-Pro: choose one explicit generative protocol; default proposal is zero-shot with the pinned Inspect task prompt for our controlled comparison, NOT a reproduction of publisher five-shot scores. Inspect's task implementation must be pinned. Do not run the original local script unchanged: its inspected version has short context/output defaults and random guessing on extraction failure. Missing extraction scores zero in our protocol. Disable semantic retries. [Publisher script](https://raw.githubusercontent.com/TIGER-AI-Lab/MMLU-Pro/main/evaluate_from_local.py), [Inspect task](https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_evals/main/src/inspect_evals/mmlu_pro/mmlu_pro.py).

MATH-500: load the exact H4 dataset/revision and its IDs, not generic Inspect MATH. The inspected generic task uses another MATH dataset, temperature .5, and multiple scorers including a model judge. Use a single explicitly chosen deterministic extraction/equivalence scorer, report parser errors, and validate synthetic fixtures. No unrequested grader API. The inspected symbolic utility uses SIGALRM; prefer a supported Linux execution path and verify timeout behavior. [Task](https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_evals/main/src/inspect_evals/math/math.py), [scoring utility](https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_evals/main/src/inspect_evals/math/utils.py).

BBEH: pin official answer extraction and its formatting rules. Inspect full and mini aggregation differ; our sampled panel uses explicitly named micro accuracy and task breakdowns, never the unqualified official full BBEH score. Do not report harmonic aggregation from two or five items per task as a stable full-benchmark estimate. [Official scorer](https://raw.githubusercontent.com/google-deepmind/bbeh/main/bbeh/evaluate.py), [Inspect implementation](https://raw.githubusercontent.com/UKGovernmentBEIS/inspect_evals/main/src/inspect_evals/bbeh/bbeh.py).

IFEval: separate diagnostic. Preserve original prompts, score the actual final-response channel, and report strict prompt-level and strict instruction-level separately. Loose scores are supplemental and named. Do not append a universal FINAL wrapper or strip arbitrary reasoning-like prose. Native channel parsing is allowed and recorded. [Official evaluator](https://raw.githubusercontent.com/google-research/google-research/master/instruction_following_eval/evaluation_lib.py).

Inspect remains a provisional runner, not a certified turnkey method. Freeze dataset revision, scorer commit, task arguments, rendered messages, native templates, effort and sampling settings explicitly. A model card saying latest Transformers is not an executable dependency specification.

## Budget and statistics corrections

Withdraw the old five-point bootstrap elimination criterion and the guaranteed nine-model screen. Thirty math questions cannot justify its intended precision, and 60 MMLU-Pro items were not equally divisible among 14 subjects. The new bridge has exact divisible allocations where possible. Sample counts remain proposed workload choices, not power guarantees.

The 32,768-token ceiling is provisional and includes reasoning plus final output. Input plus output must fit each configuration's supported context: a 32K-context model cannot receive 32K output allowance plus a nonempty prompt. Do not silently extend context or truncate inputs. Establish a common feasible ceiling for the primary comparison; larger-budget sensitivity conditions apply only to configurations supporting them and must be labeled separately. A development-only budget check must establish whether the ceiling meaningfully censors particular configurations. Compare feasible short/long budgets (for example 8K and up to 32K, optionally 64K in supported configurations) on the same development questions; do not rescue favorites. Choose the main ceiling before bridge/final outcomes. Higher ceilings do not prove unconstrained capability. No laptop wall-time limits in A. Decode watchdogs and invalid-attempt reruns are explicit.

Final sample size is fixed from available compute before outcomes, favoring more distinct questions over three repeats by default. Use two generations only when affordable for every finalist. Report mean single-attempt accuracy, completion, extraction failures and truncation separately. Repeats remain clustered by question; bootstrap does not create more independent items. Confidence intervals on the chosen sample do not establish unbounded intelligence. Public benchmark exposure is unknown; disjoint project splits do not establish training decontamination. Do not alter public questions to claim a new contamination-free benchmark.

## Immediate next authorized preparation and first future experiment

Now: obtain Morgan resource facts and prepare an offline scorer/template conformance specification. No inference is required to inspect task implementations or define synthetic fixtures.

After approval: first actual inference is an integration smoke test of Qwen3.5-9B and GPT-OSS-20B only IF both are supported, 12 nonbenchmark development prompts each, concurrency one. They exercise different interfaces; their choice for plumbing does not grant finalist status. If unsupported, choose the smallest eligible model for the same interface class. Check exact parameters, reasoning/final separation, stops, accounting and memory. This is not enough to choose a budget or rank capability. Follow with the separate development budget check, then the decision stages above.

B still measures real Morgan serving behavior; C still evaluates a defined university application separately. Existing completed work is preserved. Final abstract remains unwritten until actual results.


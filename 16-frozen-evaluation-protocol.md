# 16. Evaluation protocol (procedure frozen; empirical ceiling pending), v3

> **Version 3 (2026-09-29, stage 1):**
> - **BBEH sample:** the official BBEH Mini replaces the study-drawn BBEH sample.
> - **BBEH suffix:** corrected to the paper's verbatim text.
> - **Scorers:** implemented and validated (see [21](21-local-validation-report.md)).
> - **IFEval:** `langdetect` is seeded.
> - **Qwen route:** DeepInfra FP4, a disclosed deviation ([20](20-stage1-provider-questions.md) §3).
>
> The v2 file is archived in `manifest/history/2026-09-29_v2/`.

> **Version 2 (2026-09-29). Pre-outcome amendments; no model output exists.** The v1 file is archived in `manifest/history/2026-09-29_v1_pre-MiMo/`.
>
> **(a) Model set:** P35 MiMo-V2.6-Pro replaces P24.
>
> **(b) Ceiling:** the common ceiling now limits *generated* tokens and is bounded by each execution route's output limit, not its context window. See §5.0.
>
> **(c) Calibration:** C is chosen from a fixed ladder by a pre-registered censoring rule on development data, then frozen before any final request.
>
> **(d) Sensitivity analyses:** a 16K ceiling is added.
>
> **(e) Server-templated routes:** these log a request-payload hash, the echoed model ID and any fingerprint.
>
> **(f) New statuses and flags:**
> - `PROVIDER_FILTERED` (a new status);
> - the flags `provider_repetition_truncation` and `model_echo_changed`.
>
> **(g) Request counts:** exact counts are recorded in §9.
>
> Strand A (capability) and IFEval (instruction following) remain separate. **No composite score.**

September 29, 2026. **Proposed; nothing executed.** Machine-readable: [manifest/evaluation.json](manifest/evaluation.json). Model configurations: [15](15-six-model-configuration-manifest.md).

This supersedes the capability-evaluation parts of 06-13. Retained from [13](13-protocol-after-audit.md): its scorer and template corrections. **Not** retained: the 355-item bridge screen (the six models are evaluated together, with no elimination screen), the hardware gates, and the 8K/32K/64K proposal.

**What "frozen" covers:** every methodological choice below is fixed *before any outcome*. Two things are genuinely empirical and stay open:
- the numeric output ceiling, which needs tokenizers to count prompt lengths;
- the development censoring measurement.

`calibrated=false` until both are done, and the runner must refuse final generation until then.

## 1. Research question and scope

The question: how do six contemporary open-weight models compare on English, no-tools, single-turn reasoning and knowledge tasks under a documented native-maximum-capability configuration?

- **What this is:** a purposive comparison, not a claim about the world's best models.
- **Separate strands:** A (capability), B (deployment and serving) and C (university application) stay separate. There is no combined intelligence score.

## 2. Tasks and exact samples

| Benchmark | Source (pinned) | Final items | Development items (disjoint) | Role |
|---|---|---|---|---|
| MMLU-Pro | TIGER-Lab/MMLU-Pro @ `b189ec76`, test parquet | 420 (30 × 14 subjects) | 70 (the whole validation split) | knowledge + reasoning |
| MATH-500 | HuggingFaceH4/MATH-500 @ `6e4ed1a2`, test.jsonl | 400 | 100 (proportional subject × level) | mathematical reliability; ceiling likely |
| **BBEH Mini** (v3: the official subset; v1 drew its own 20 per task) | google-deepmind/bbeh @ `80d12ca9`, `bbeh/mini/data.json` | 460 (the official Mini: 20 × 23 tasks, from 4,520 items), micro average as in the paper | 46 (2 per task, excluding Mini) | hard multi-step reasoning |
| IFEval (separate diagnostic) | google-research @ `d36068b8` | all 541 | none | instruction following, never merged with the above |

**How the items are drawn:**
- **Script:** item IDs come from [manifest/generate_item_manifests.py](manifest/generate_item_manifests.py), using seed 20260929, stable source IDs and largest-remainder allocation with ties broken by stratum name.
- **Answer keys:** they are written to separate `answer_key_*.json` files that the runner never reads.
- **Overlap checks:** development and final sets are checked for overlap by ID and by content hash.

**Status:** generated on 2026-09-29 from the pinned data (all 46 source/data files fetched and hashed in `manifest/evaluation-files-lock.json`).
- **Result:** 1,280 final items and 216 development items.
- **Deterministic:** repeated runs produce identical output hashes (`manifest/items/item_manifest_lock.json`).
- **Isolated:** no answers appear in the item files, and there is no ID or content overlap between development and final sets.
- **No model outputs exist.**

**Excluded before outcomes:** GPQA Diamond. Its gated access and evaluator were not confirmed at freeze time, so it is excluded now rather than added later if the results fail to separate the models.

## 3. Prompt construction

- **Message:** a single user message containing the verbatim task prompt, with the answer-format instruction the pinned task template already carries. Nothing else is appended.
- **Templates** (files in `manifest/prompts/`, hashes in `prompts-lock.json`):
  - **MMLU-Pro:** the pinned Inspect `mmlu_pro` zero-shot template, confirmed byte-identical to the source string. This is honestly *our* zero-shot protocol, not a reproduction of publisher five-shot scores.
  - **MATH-500:** the pinned Inspect MATH prompt text (byte-identical), applied to the exact H4 items. The generic Inspect MATH task (another dataset, temperature 0.5, model judge) is not used.
  - **BBEH (v3, verified):**
    - **Prompt:** the task input, a blank line, then the **paper's suffix verbatim**, taken from the Reproducibility section of arXiv 2502.19187v2 and checked against the archived LaTeX source by `scoring/verify_bbeh_suffix.py`.
    - **What changed from v1:** the v1 study-authored suffix omitted the paper's examples and the multiple-choice letter instruction.
    - **Separator:** the blank line is a disclosed study choice.
  - **IFEval:** the original prompts, byte-identical, with no FINAL wrapper and no reasoning instruction.
- **Few-shot:** zero-shot throughout. There is no study system message; native templates' own effort prefixes are recorded.
- **Logging:** every request logs the exact rendered prompt or token IDs and its SHA-256.

## 4. Answer channel and scoring

- **What is scored:** only the **final channel**, meaning the content after the native reasoning delimiter or the parser's `content`. Reasoning text is stored in full but never scored.
- **No credit from reasoning:** a correct-looking answer that appears only inside the reasoning earns nothing.
- **Scorers:**
  - **MMLU-Pro:** a single A–J letter via the pinned Inspect pattern. If extraction fails, the result is `EXTRACTION_FAILURE` (0). There is **no random guessing**, which the original publisher script did.
  - **MATH-500:** Math-Verify at `ba3d3aaf` against the H4 `answer`, with no judge model. **Validated (v3; see 21):**
    - **Answer extraction:** the last `ANSWER:` line (Inspect rule).
    - **Parsing:** gold as `\boxed{…}`, prediction as `$…$`.
    - **Timeout:** a worker process with a 30 s outer kill-and-restart limit.
    - **Test results:** fixtures 45/45, all 500 gold answers round-trip; upstream suite 288/291 (the 3 test the unused inner timeout).
  - **BBEH:** the official `evaluate_correctness` from `bbeh/evaluate.py`, with its functions vendored because the module prints examples when imported. The official extractor has no failure state: with no answer prefix it compares the response's first line. So BBEH produces no `EXTRACTION_FAILURE`; a `no_answer_prefix` flag is recorded instead, and the official verdict stands.
  - **IFEval:** the official evaluator. Strict prompt-level and strict instruction-level results are the headline figures; loose variants are labelled supplemental.
    - **v3 determinism fix:** `langdetect` is seeded to 0. Unseeded, the language and case checks were nondeterministic.
    - **Tests:** the official unit tests pass (41 + 88 subtests).
  - **BBEH scorer defect (v3):**
    - **The defect:** 11 of 4,520 targets that end in "." cannot be matched by the official scorer.
    - **Impact:** none is in the official Mini final set, so the official scorer is kept.
- **Status precedence (one primary status per attempt):**
  1. `INFRASTRUCTURE_FAILURE`
  2. `MALFORMED_NATIVE_OUTPUT`
  3. `BUDGET_TRUNCATED`
  4. `NO_FINAL_ANSWER`
  5. `EXTRACTION_FAILURE`
  6. `INCORRECT`
  7. `CORRECT`
- **Additional flags** (can overlap with any status): `loop_suspected` (the most frequent 12-gram repeats 10 or more times), `stop_token_reinserted`, `seed_unsupported_by_backend`.
- **Counting:** every status except infrastructure failure scores 0 and stays in the denominator.
- **Reported separately:** accuracy, completion, truncation, no-final, extraction and malformed rates, and the missing count.

## 5. Output budget: policy frozen, value pending

### 5.0 v2 amendment: hosted execution (supersedes the terminal-ceiling rule below)

**The ceiling limits generated tokens, not context.** C limits **generated tokens (reasoning + final)** per request. It must not exceed any execution route's documented maximum for generated tokens. A context window is not an output limit: Qwen's 1M-context hosts still cap output at 131,072.

**Documented output limits per route:**

| Route | Max generated tokens | Includes reasoning? | Status |
|---|---|---|---|
| P35 DeepInfra | 943,718 | undocumented | OpenRouter listing; verify |
| P35 Xiaomi (H-MiMo-Xiaomi) | 131,072 | **yes** (doc) | verified doc |
| P25 DeepSeek | 393,216 (default 128K at max) | generated tokens; reasoning reported inside | verified doc |
| P28/P27 Z.ai | 131,072 | **undocumented** | verified doc limit; inclusion at T2 |
| P29 Moonshot | 1,048,576 (default 131,072) | **yes** (counts toward completion_tokens) | verified doc |
| P34 dedicated FP8 | 262,144 − prompt (engine) | yes | our setting |
| P34 DeepInfra FP4 (fallback) | 131,072 | — | OpenRouter listing; verify |

**The binding limit:** the largest common value supported by every recommended route is **C_max = 131,072**. The binding route is Z.ai's GLM pair, and also Xiaomi if that route is used.

**It holds only if:**
- integration test T2 shows that Z.ai's `max_tokens` bounds reasoning plus final tokens;
- test T1 shows that every route accepts 131,072.

If Z.ai excludes reasoning from `max_tokens`, a common generated-token ceiling cannot be enforced server-side for GLM, and a pre-outcome decision is required.

**Prompt headroom:** the longest prompt is 25,558 characters, at most about 12K tokens. It leaves Qwen's native 262,144 far above 131,072, so no tokenizer is needed to show feasibility.

**Development calibration** runs at C_dev = C_max.

**Choosing C_final (pre-registered):** C_final is the smallest value on the ladder **65,536 / 98,304 / 131,072** that satisfies the rule below for **every** model.
- **D_m(L):** the number of development attempts by model m that ended naturally within C_dev but used more than L tokens, i.e. the attempts that L would additionally censor.
- **Rule:** D_m(L) ≤ 2 overall (≤0.9% of 216; Wilson upper bound 3.3%) and D_m(L) ≤ 1 within each benchmark.
- **Excluded from D_m(L):** loops and other outputs already truncated at C_dev are censored at every L, so they are not counted.
- **Floor:** the ladder starts at 65,536 so the 64K sensitivity analysis remains possible.
- **What cannot influence C:** development accuracy, cost, runtime and model preference.
- **Adequacy:** truncation of 5% or less at C_dev per model. A model that fails is labelled "budget-censored at the maximum valid common ceiling"; there is no model-specific ceiling.
- **Freeze:** C_final and the D-table are written into `evaluation.json`, with `calibrated=true`, before any final request.

**Post-hoc sensitivity analyses:** at 8K, 16K, 32K and 64K. Always labelled secondary.

The v1 text below is retained as history. Its "C = T ≈ 245,760" rule is not achievable on hosted routes.

**v1 (superseded): one common ceiling C for all six, covering reasoning and final tokens together.**
- **Terminal ceiling:** T = min over models of (native context − largest rendered prompt in the final and development sets − 1,024), rounded down to a multiple of 8,192.
- **Binding model:** P34 (native 262,144 tokens, no extension) makes T slightly under 262,144. The exact value needs every model's tokenizer, which is **pending**.
- **Planning estimate:** the longest selected BBEH input is about 32,000 characters, roughly 8–11K tokens, so T is expected near 245,760 (30 × 8,192). This is a planning estimate only, not the frozen value.
- **Primary ceiling:** C = T, the largest ceiling valid for every configuration.

**Why this design:**
- The publishers recommend 256K–384K tokens or task-specific budgets, so any smaller common cap would be arbitrary. T is the largest cap the protocol can defend without context extension.
- Earlier pilots showed small caps censoring legitimate reasoning.
- A model-native-ceiling primary is rejected: those ceilings exceed P34's native context, and different caps per model would confound the comparison.

**Development calibration** (on the disjoint development items, one generation each, at C):
- **Purpose:** verify the plumbing, stop semantics and token accounting, and measure the budget-truncation rate.
- **Adequacy criterion:** truncation of 5% or less per configuration, with the upper 95% Wilson bound reported.
- **If a configuration fails:** proceed at C anyway. Label it "budget-censored at the maximum valid common ceiling" everywhere. Non-completion is a capability or configuration outcome, not an infrastructure error.
- **No rescue or tuning:** there is no per-model escalation. Development accuracy cannot change any prompt, setting, model or C.
- **No guarantee:** a development sample cannot promise zero truncation on the final set.

**Matched-token sensitivity, computed post hoc from the same generations** (v1: 8K, 32K and 64K; v2 adds 16K):
- **Method:** an attempt counts as completed at ceiling c only if it used c tokens or fewer. This is valid because a lower cap doesn't change earlier tokens of the same generation, provided per-attempt token counts are recorded.
- **Labels:** this is always a sensitivity analysis and never the primary result.
- **Caveat:** equal token counts are not equal compute across architectures and tokenizers.

**Operational watchdog (not a capability budget):**
- **Stall rule:** a request is aborted after 30 minutes with no new token, or 48 hours in total, and recorded as `INFRASTRUCTURE_FAILURE`.
- **No speed scoring:** wall-clock speed never enters any score.

## 6. Generations, seeds, retries

- **Generations:** one per item, favouring more distinct items over repeats (repeats would be clustered by item).
- **No selection among samples:** no pass@k, best-of or majority voting.
- **Seed:** each item's seed is `int(sha256("Morgan-2026-09-29|"+item_id)[:8],16) & 0x7fffffff`, the same for all six models. Backend seed determinism is not assumed; it is recorded, and sampling at temperature 1 is inherently stochastic.
- **No semantic retries.** A wrong, truncated, looping or unparseable answer is final.
- **Infrastructure reruns:** up to 2, with an identical rendered prompt, settings and seed. After that the attempt is `MISSING`.

## 7. Statistical plan

- **Per benchmark:** accuracy with a 95% Wilson interval for each configuration.
- **Pairwise comparisons:** 15 pairs × 3 capability benchmarks = 45. Each uses an exact McNemar test on item-level results, with Holm correction across all 45, and a paired-bootstrap 95% interval for the difference (10,000 item resamples, seed 20260929).
- **Precision:** with 400–460 items per benchmark, a single accuracy near 50% has roughly a ±4.5 percentage-point 95% interval. Smaller gaps are not claimed.
- **No composite score:** an unweighted three-benchmark mean may appear only as a labelled descriptive summary.
- **Missing data:** the primary analysis is complete-case; a sensitivity analysis scores missing items as incorrect.
- **Contamination:** public benchmarks may be in training data, and disjoint development/final splits do not remove this. No decontamination claim is made.

## 8. (v1 numbering retained) See §10 for preflight refusal conditions.

## 9. Exact request counts (v2)

The generator has verified 1,280 unique final item IDs and 216 unique development IDs, and the two sets are disjoint. Each model answers each item once.

| Stage | Requests | Composition |
|---|---|---|
| Integration test | **34** | synthetic prompts only; +6 for the dedicated Qwen route, +4 if the Xiaomi MiMo route is used |
| Development calibration | **1,296** | 216 × 6 |
| Final capability evaluation | **7,680** | 1,280 × 6: MMLU-Pro 2,520, MATH-500 2,400, BBEH Mini 2,760 |
| IFEval diagnostic (separate) | **3,246** | 541 × 6 |
| Repetitions | 0 | one generation per item |
| Infrastructure reruns | at most 2 per failed attempt | expected under 2% |

**Totals:**
- development + final: **8,976**;
- adding IFEval: **12,222**;
- adding the integration test as well: **12,256**.

## 10. Preflight refusal conditions (implementation requirement; was §8)

The runner must refuse to produce final generations unless **all** of the following hold:
- `calibrated=true`, and every `pending` field in `models.json` and `evaluation.json` is resolved;
- the item manifests and answer keys match `item_manifest_lock.json`;
- the scorer fixture suites pass;
- the effort setting is verified per model:
  - the rendered prefix on the client-rendered route;
  - the integration checks T1–T4 on server-templated routes (v2);
- a stage authorisation file exists for the final stage, with a spend cap (`runner/adapters.py` `check_gate`).

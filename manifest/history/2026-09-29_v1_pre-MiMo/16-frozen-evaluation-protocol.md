# 16. Evaluation protocol (procedure frozen; empirical ceiling pending)

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
| BBEH (sampled) | google-deepmind/bbeh @ `80d12ca9` | 460 (20 × 23 tasks; count verified: 22 tasks × 200 + 120 = 4,520 items) | 46 (2 per task) | hard multi-step reasoning |
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
  - **BBEH:** the task input followed by a **study-authored** suffix asking for the prefix "The answer is:". The pinned BBEH repository supplies neither a suffix nor a format instruction inside the inputs. The suffix is aligned with the official extractor but is not verified as the paper's verbatim prompt (an open item).
  - **IFEval:** the original prompts, byte-identical, with no FINAL wrapper and no reasoning instruction.
- **Few-shot:** zero-shot throughout. There is no study system message; native templates' own effort prefixes are recorded.
- **Logging:** every request logs the exact rendered prompt or token IDs and its SHA-256.

## 4. Answer channel and scoring

- **What is scored:** only the **final channel**, meaning the content after the native reasoning delimiter or the parser's `content`. Reasoning text is stored in full but never scored.
- **No credit from reasoning:** a correct-looking answer that appears only inside the reasoning earns nothing.
- **Scorers:**
  - **MMLU-Pro:** a single A–J letter via the pinned Inspect pattern. If extraction fails, the result is `EXTRACTION_FAILURE` (0). There is **no random guessing**, which the original publisher script did.
  - **MATH-500:** Math-Verify at `ba3d3aaf` against the H4 `answer`. It runs in a subprocess with a hard timeout (no SIGALRM dependency) and uses no judge model. **Pending:** installation and a synthetic fixture suite covering fractions, radicals, intervals, units, `\boxed`, multiple answers and malformed strings.
  - **BBEH:** the official `evaluate_correctness` from `bbeh/evaluate.py`, with its functions vendored because the module prints examples when imported. The official extractor has no failure state: with no answer prefix it compares the response's first line. So BBEH produces no `EXTRACTION_FAILURE`; a `no_answer_prefix` flag is recorded instead, and the official verdict stands.
  - **IFEval:** the official evaluator. Strict prompt-level and strict instruction-level results are the headline figures; loose variants are labelled supplemental.
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

**Primary: one common ceiling C for all six, covering reasoning and final tokens together.**
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

**Matched-token sensitivity, computed post hoc at 8K, 32K and 64K from the same generations:**
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

## 8. Preflight refusal conditions (implementation requirement)

The runner must refuse to produce final generations unless **all** of the following hold:
- `calibrated=true`, and every `pending` field in `models.json` and `evaluation.json` is resolved;
- the item manifests and answer keys match `item_manifest_lock.json`;
- the scorer fixture suites pass;
- the rendered effort prefix is verified per model.

# 21. Local validation report (scorers, Math-Verify, BBEH correction)

September 29, 2026. Everything here ran **locally**:
- no model, no inference, no API call;
- nothing but public source, data or paper files downloaded.

## 1. Math-Verify

**Installation:**
- **Environment:** `.venv-scoring/`, Python 3.14.4, git-ignored. Full lock in `scoring/requirements-lock.txt`.
- **Why an archive:** installing from git at the pinned commit failed on an upstream submodule step, so Math-Verify was installed from the **commit archive** of `huggingface/Math-Verify@ba3d3aaff23b3f4cac7a14672b4f6e293d97c98b`. The archive's SHA-256 is `4a0f87c3…fbae`, and it is kept in `scoring/vendor/`.
- **Consistency check:** the archive's `src/math_verify/parser.py` hashes to `ea527a5a…`, identical to the file previously locked in `evaluation-files-lock.json`.
- **Installed versions:** math-verify 0.9.0, latex2sympy2_extended 1.11.0, antlr4 4.13.2, sympy 1.14.0.

**Upstream test suite** (`tests/`, 291 tests):
- **Default run on Windows:** 245 fail. Math-Verify's inner timeout uses a process-spawn path on Windows, which fails with `WinError 6` under pytest. This is not a grading problem.
- **With the inner timeout disabled** (the `scoring/mv_no_inner_timeout.py` plugin; vendored code unchanged): **288 passed, 3 failed**.
- **The 3 failures** are `test_timeout.py`, which tests the inner timeout itself.
- **What replaces it:** the study never uses the inner timeout. It uses an outer, kill-and-restart worker timeout, which is tested separately (see below).

## 2. Study scorers (`scoring/scorers.py`; only the scorer reads answer keys)

| Benchmark | Implementation | Failure handling |
|---|---|---|
| MMLU-Pro | `parse_answers` single-answer logic from inspect_ai 0.3.271, ported verbatim (the version installed in the earlier pilot environment) | no match gives `EXTRACTION_FAILURE`; **no random guessing** |
| MATH-500 | last `ANSWER:` line via inspect_ai `ANSWER_PATTERN_LINE` (answer must be on the last line, as in `inspect_evals` `extract_answer`); then Math-Verify with gold as `\boxed{answer}` and prediction as `$…$` | empty or unparseable gives `EXTRACTION_FAILURE`; worker timeout (30 s default, kill and restart) gives `EXTRACTION_FAILURE` plus `scorer_timeout` |
| BBEH | official `evaluate_correctness`, vendored with only the import-time `print` examples removed (`scoring/vendor/bbeh_eval.py`, derivation hashed in `vendor-lock.json`) | no prefix sets flag `no_answer_prefix` and the official verdict stands |
| IFEval (separate strand) | official `evaluation_lib` strict and loose, vendored at google-research@`d36068b8` | `langdetect` seeded (§5) |

**Why these Math-Verify conventions:** tested before choosing.
- **Bare strings fail** on `\sqrt2`, intervals, sets, `\dfrac12`, `p-q` and `x^2+1`.
- **`$…$`-wrapped predictions pass all of them.**
- **All 500 MATH-500 gold answers** parse and self-verify under both `\boxed{}` and `$…$` wrapping.

**Fixture suite** (`scoring/test_scorers.py`): **45 passed**.
- **MMLU-Pro:** 12 format cases, plus a gold round-trip for **all 490** MMLU-Pro items (final and dev) using each item's real option count.
- **MATH-500:** 18 cases (fractions, decimals, radicals, intervals, sets, units, degrees, `\boxed`, text choices, wrong answers, missing or non-final `ANSWER` line), malformed LaTeX, a gold round-trip for **all 500** MATH-500 items, and timeout-then-recovery.
- **BBEH:** the 8 official examples from `evaluate.py`, the no-prefix flag, and a gold round-trip for **all 4,520** BBEH items (see §4).
- **IFEval:** end-to-end on a real IFEval prompt (`punctuation:no_comma`).

**Official IFEval unit tests** (`instructions_test.py`, fetched at the pinned commit): **41 passed, 88 subtests**, three identical runs, with `langdetect` seeded. See §5 for the unseeded result.

## 3. BBEH answer-format instruction: verified and corrected

- **Authoritative source:** BBEH paper, arXiv 2502.19187v2, LaTeX source, section "Reproducibility", box titled "Suffix". Archived at `manifest/evaluation-sources/bbeh_paper/arxiv-2502.19187v2-main.tex`, SHA-256 `85e7a15a…`.
- **The paper adds this suffix to every question:**
  > Think step by step, and when you provide the final answer, please use the prefix "The answer is:" without any modification, and provide the answer directly, with no formatting, no bolding, and no markup. For instance: "The answer is: 42" or "The answer is: yes". If the question is multiple choice with a single correct answer, the final answer must only be the letter corresponding to the correct answer. For example, "The answer is: (a)".
- **What was wrong:** the v1 template (study-authored) matched only the first sentence. It **omitted the examples and the multiple-choice letter instruction.**
- **Correction:** the template is now `{input}` + blank line + the paper suffix. `scoring/verify_bbeh_suffix.py` checks it against the LaTeX box and prints `MATCH`. The only difference is whitespace: LaTeX collapses a double space in the source.
- **Hashes:** new template SHA-256 `0ab0ba39…`. The v1 template is archived in `manifest/history/`.
- **Separator:** the paper says "suffix to the text of the question" without naming a separator. The blank line is a disclosed study choice.

## 4. BBEH sample: switched to the official BBEH Mini

- **Finding:** the pinned repository contains `bbeh/mini/data.json`. The paper (§4 and §5.2) defines **BBEH Mini** as 460 examples, 20 randomly selected per task, reported by **micro average**. The v1 fetch had missed this file.
- **Why switch:** the v1 protocol drew its *own* 460 (20 per task). The official Mini is authoritative and directly comparable to published Mini results, at the same size and the same metric.
- **Change:** the final BBEH items are now exactly the official Mini.
  - All 460 map uniquely to the pinned task files; each task has 20.
  - Only 48 overlap the v1 random draw.
  - Development items are 2 per task (46), seeded, excluding Mini by ID and content.
- **Unchanged:** the MMLU-Pro and MATH-500 items are byte-identical to v1. Totals remain 1,280 final and 216 dev.
- **Determinism:** the generator gives identical hashes on re-run. The v1 items and generator are archived.
- **New item hashes:**

  | File | SHA-256 |
  |---|---|
  | `items_final.json` | `20ebfb59…` |
  | `items_dev.json` | `3e8fd68b…` |
  | `answer_key_final.json` | `90ea1b22…` |
  | `answer_key_dev.json` | `e1453089…` |

- **Fetch re-run:** 46/46 previous files byte-identical, plus 2 added (`mini/data.json`, `leaderboard.md`).

**Official-scorer defect found:**
- **What happens:** for targets ending in a period, `evaluate_correctness` strips the period from the prediction (twice) but not from the reference. A perfect answer "The answer is: He really cried." scores **incorrect**; only an answer ending in "..." would pass.
- **Scale:** 11 of 4,520 items, all `bbeh_linguini`.
- **Effect on our sets:** **none are in the official Mini final set**, and one is in dev, where accuracy influences nothing.
- **Handling:** the official scorer is kept for comparability, and the fixture test pins this exact set.

## 5. IFEval reproducibility hazard (disclosed deviation)

- **The problem:** the official evaluator calls `langdetect.detect()` unseeded (instructions.py L158, L1416, L1448), and `langdetect` is randomised.
- **Evidence:** 1 of 10 calls classified an all-caps English sentence as German. The official unit test `test_english_capital_checker` failed once for this reason.
- **Instructions affected:** `language:response_language`, `change_case:english_capital` and `change_case:english_lowercase` can flip between scoring runs.
- **Fix:** the study scorer sets `langdetect.DetectorFactory.seed = 0` (`scoring/ifeval_seed.py`). The evaluator code is unchanged.
- **Disclosure:** reported as a determinism fix. With it, the official tests pass 3/3 runs.

## 6. Re-verification after all changes

See 17 §1 for the full table.
- Runner offline tests: 16/16 (including the integration executor's dry run and gate refusal).
- Scorer fixtures: 45/45.
- Math-Verify upstream: 288/291 (the 3 are the inner-timeout tests, as expected).
- IFEval official: 41 + 88 subtests.
- `source-lock.json`: 49/49 files match.
- Evaluation files: 48 locked.
- Secret scan: clean.
- JSON: all valid.

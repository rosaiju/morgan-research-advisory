# 17. Fairness and reproducibility audit

September 29, 2026. This audits [15](15-six-model-configuration-manifest.md), [16](16-frozen-evaluation-protocol.md) and the JSON manifests. **Documented** means written into a manifest. **Tested** means actually executed. Nothing in this package has been tested against a model; the only executed checks are listed in §1.

## 1. Checks actually performed (executed)

| Check | Result |
|---|---|
| 32 archived model-source files vs `source-lock.json` SHA-256 | **32 match, 0 mismatch, 0 missing** (2026-09-29) |
| Revision pins in `source-lock.json` equal the handoff table | match (all six) |
| Configuration facts cross-read from pinned files | the line references in 15 and `models.json` were read this session |
| Fetch of pinned evaluation sources and data (`fetch_evaluation_sources.py`) | **46/46 fetched**, SHA-256 recorded in `evaluation-files-lock.json`. Includes MMLU-Pro parquet files, MATH-500, all 23 BBEH task files, IFEval data and evaluator, the Inspect task sources, Math-Verify source and Kimi's `encoding_k3.py`. The script refuses weight/vocabulary paths; none were requested. |
| Item manifest generation (`generate_item_manifests.py`) | 1,280 final + 216 dev items; development/final disjoint by ID and content (asserted); answers only in the `answer_key_*` files; **deterministic** (identical hashes on repeated runs, after fixing a lock-file self-hash bug found during this check) |
| Prompt templates vs pinned sources | MMLU-Pro and MATH templates **byte-identical** to the pinned Inspect strings (AST extraction); all three hashed in `prompts-lock.json` |
| JSON manifests parse | all 6 files valid |

No inference, model loading, tokenizer loading or scorer execution happened. The original `fetch_evaluation_sources.ps1` was not run; it is superseded by the Python script and kept for history.

## 2. Passed by design (documented, not tested)

- **Same tasks and scorers:** every model gets the same tasks, items, prompts, scorers, single-turn fresh contexts and no-tools condition.
- **Answer-key isolation:** the keys sit in separate files the runner never reads; the generator checks development/final disjointness by ID and by content hash.
- **Explicit native settings:** every model's effort and sampling is explicit, which closes the three silent-default hazards found (§3 #1–3).
- **Status handling:** there is a single primary status with a stated precedence. Truncation, no-final, extraction, malformed and infrastructure outcomes are reported separately, and reasoning text is never credited.
- **No random-guess fallback, no semantic retries, no best-of selection.**
- **Frozen before outcomes:** sample sizes, seeds, the statistical test and multiplicity correction are all fixed. GPQA is excluded now, not after seeing results.
- **No hidden judges:** no LLM judge or other hidden API call appears anywhere in scoring.
- **Refusal gate:** the preflight refuses to run with `calibrated=false` or any pending field.

## 3. Issues found and resolved in the manifests

| # | Issue | Impact if missed | Resolution |
|---|---|---|---|
| 1 | DeepSeek-V4-Pro encoder defaults to `low` (no effort prompt) | Pro silently runs at its lowest effort | `max` set explicitly and verified in the rendered prompt |
| 2 | DeepSeek-V4.1 encoder defaults to 75, not 100 | not the maximum configuration | integer 100 set explicitly |
| 3 | GLM generation_config has no `do_sample` | a backend could decode greedily | `do_sample=true` explicit |
| 4 | GLM template maps any unknown effort value to `max` | typos go undetected | the rendered prefix is checked |
| 5 | Kimi nested config: `do_sample=false`, `max_length=20`, `top_k=50` | a backend could inherit these | overridden by the card recipe |
| 6 | Qwen rejects non-listed efforts, so a shared `max` string would crash | a family-agnostic config is invalid | per-model effort vocabulary (`xhigh` for Qwen) |
| 7 | DeepSeek parser asserts on a missing `</think>`/EOS | truncated outputs mislabelled "malformed", or a runner crash | ceiling stops are classified before parsing; the EOS reinsertion rule is flagged |
| 8 | Qwen's native context (262,144) is below its own output recommendation (393,216) | an infeasible or illegal common cap | the terminal ceiling is derived from the smallest native context, with no extension |
| 9 | Qwen's README table is the hosted Max product | wrong prior-evidence attribution | noted in the manifest; not used |
| 10 | Kimi encoder reads `thinking_effort`, not the API's `reasoning_effort`; without it no effort message is rendered | Kimi silently runs without effort guidance | `thinking_effort="max"` passed and the rendered message verified |
| 11 | Kimi encoder is encode-only (no output parser) | reasoning/final separation undefined | a framework parser or a strict, fixture-tested study parser is required (pending) |
| 12 | BBEH official extractor has no failure state (it falls back to the first line of the whole response) | answers could be "matched" from unstructured text; `EXTRACTION_FAILURE` impossible | official verdict kept for comparability; `no_answer_prefix` flag reported |
| 13 | BBEH inputs contain no answer-format instruction and the repo gives no suffix | the extractor's prefix is rarely produced | study-authored suffix, disclosed as not paper-verbatim |
| 14 | `bbeh/evaluate.py` prints examples when imported | noisy logs, a side effect | functions vendored, not imported as-is |
| 15 | Inspect's generic BBEH/MATH tasks use raw inputs, other datasets or harmonic aggregation | mislabelled results | only exact H4 MATH-500 items and our named BBEH-sampled micro accuracy are used |

## 4. Unresolved issues (open; each blocks final execution)

| Issue | Why it matters | Prerequisite to close it |
|---|---|---|
| Output ceiling value T | the primary budget cannot be fixed without prompt token counts per tokenizer | tokenizer files for all six (vocabulary download, a small non-weight file) plus the generated item manifests |
| Development censoring at C | the adequacy of C is unknown; if truncation exceeds 5% the protocol proceeds but labels the model censored | authorized development inference |
| Kimi output parser | P29's reasoning/final separation is unimplemented (the encoder is audited; resolved items #10/#11) | choose the framework parser or a study parser; pass the fixtures |
| GLM EOS IDs [154820, 154827, 154829] unnamed | natural stop could be confused with tool/observation stops | pinned tokenizer vocabulary |
| BBEH suffix provenance | the suffix is study-authored, not confirmed as the paper's prompt | compare with the BBEH paper appendix before execution; if it differs, adopt the paper text by a pre-result amendment |
| Math-Verify not installed or tested | scorer correctness is unproven | install the pinned version and pass the fixture suite |
| Backend fidelity | no serving stack has been shown to render these templates and encoders byte-identically, honour top_k/min_p and seeds, or preserve native quantization | integration smoke tests (authorized later) |
| Seed determinism | temperature-1 sampling may not be reproducible across backends or hardware | record per attempt; reproducibility is claimed at configuration level, not bit level |

## 5. Fairness limits that remain by design (disclose, don't fix)

- **Different sampling across families:** it follows each publisher's native recipe, so the comparison is native-configuration, not identical decoding.
- **Unequal compute:** equal token caps are not equal compute. Tokenizers, architectures (sparse and linear attention, MoE sizes) and effort semantics differ, and "max" means different things per family.
- **Native effort prompts:** these differ in length and wording, for example GLM's system-effort prefix and DeepSeek's long max-effort paragraph, so the raw serialized inputs are not identical.
- **Single generation at temperature 1:** item-level outcomes carry sampling noise. The interval estimates cover item sampling, not generation-to-generation variance.
- **Contamination:** public benchmarks may be memorised, and this is not measurable here.
- **Sample representativeness:** the six-model sample is purposive, and excluded models are not shown to be weaker.
- **Ceiling on MATH-500:** strong models may saturate it, so it cannot separate them finely.

## 6. Reproducibility record required per attempt (runner specification)

Each attempt must record:
- model revision and served precision;
- backend name and version;
- rendered prompt SHA-256;
- effort value as rendered, and the full sampling parameters as received by the backend;
- seed, and whether the backend honours it;
- output ceiling;
- stop reason and stop token;
- total, reasoning and final token counts (where separable);
- raw completion text;
- parsed channels;
- primary status and flags;
- scorer version and the extracted answer;
- rerun count.

## 7. Verdict

- **Methodology:** complete and frozen as a procedure.
- **Data preparation:** item manifests, answer keys and prompt templates are generated and hash-locked.
- **Configuration manifest:** complete, with the §4 items pending.
- **Not yet executable:** `calibrated=false`. The remaining blockers each need a *separately authorized* step:
  - tokenizer files, for the ceiling value and the GLM stop IDs;
  - Math-Verify installation and the scorer and parser fixture suites;
  - backend integration checks;
  - development calibration.
- **Hardware:** no hardware information was needed or used.

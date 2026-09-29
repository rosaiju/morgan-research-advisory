# 17. Fairness and reproducibility audit, v3 (after stage-1 local validation)

September 29, 2026. Earlier versions are archived:
- v1: `manifest/history/2026-09-29_v1_pre-MiMo/`
- v2: `manifest/history/2026-09-29_v2/`

This audit covers:
- 15, 16 (v3), 19, [20](20-stage1-provider-questions.md) and [21](21-local-validation-report.md);
- `manifest/`, `runner/` and `scoring/`.

**Tested** means executed locally. **Nothing has been sent to any provider, and no model was run.**

## 1. Checks executed (all reproducible with `python verify_all.py`: 14/14 pass)

| Check | Result |
|---|---|
| Model source files vs `source-lock.json` (original six, MiMo RL/MOPD, Qwen FP8) | 49/49 match |
| Evaluation sources vs `evaluation-files-lock.json` | 48/48 match (46 unchanged since v1, plus BBEH `mini/data.json` and `leaderboard.md`) |
| Item manifests vs `item_manifest_lock.json` | match; 1,280 final and 216 dev; deterministic on re-run; MMLU-Pro and MATH-500 byte-identical to v1 |
| Prompt templates vs `prompts-lock.json` | 3/3 (BBEH template re-hashed after correction) |
| Vendored scorer files vs `scoring/vendor/vendor-lock.json` | 6/6 |
| JSON manifests | 9/9 parse |
| Runner offline tests (now including the integration executor's dry run and its gate refusal) | 16/16 |
| Scorer fixtures | 45/45, including gold round-trips for all 490 MMLU-Pro, 500 MATH-500 and 4,520 BBEH items |
| IFEval official unit tests | 41 + 88 subtests (seeded `langdetect`) |
| Math-Verify upstream tests | 288/291. The 3 failures are the inner-timeout tests; the inner timeout is not used (outer worker timeout tested instead) |
| BBEH suffix vs paper LaTeX | MATCH |
| Secret scan (package code; third-party venv and vendor trees excluded) | clean |
| No stage authorised; network opt-in unset | yes |

## 2. Passed by design

**Carried from v2:**
- identical tasks, prompts and scorers;
- answer-key isolation: only `scoring/` reads keys;
- explicit effort and sampling;
- status precedence;
- no guessing, semantic retries, best-of or judges;
- preflight refusal and the network gate;
- keys only in environment variables;
- separate strands with no composite score;
- the ceiling rule pre-registered before outcomes.

**New in v3:**
- **Scorers are implemented and validated before any output exists.** Their conventions are fixed in `evaluation.json` and cannot be tuned on model outputs.
- **The BBEH sample and prompt now follow the authoritative source** (the official Mini and the paper's suffix) rather than study choices.

## 3. Issues resolved (v1 items 1–15 and v2 items 16–27 carried; new items 28–35)

| # | Issue | Resolution |
|---|---|---|
| 28 | **BBEH suffix:** the study-authored v1 suffix omitted the paper's examples and the multiple-choice letter instruction | replaced with the paper's verbatim suffix; machine-checked |
| 29 | **BBEH sample:** an official BBEH Mini exists, but v1 used its own random 20 per task | final = official Mini (micro average, comparable to published Mini results); dev re-drawn excluding Mini |
| 30 | **Official BBEH scorer:** cannot credit targets ending in "." (11/4,520, all linguini) | none in the final set; official scorer kept for comparability; asserted by test |
| 31 | **IFEval `langdetect` unseeded:** nondeterministic verdicts for 3 instruction types | seeded to 0 (disclosed); official tests pass 3/3 |
| 32 | **Math-Verify inner timeout:** broken on Windows (process spawn) | not used; outer kill-and-restart worker timeout, tested |
| 33 | **Math-Verify input convention:** bare strings fail radicals, intervals and sets | fixed: gold as `\boxed{}`, prediction as `$…$`; all 500 golds round-trip |
| 34 | **MATH answer not on the last line** | follows Inspect's `\Z`-anchored rule, giving `EXTRACTION_FAILURE` (fixture) |
| 35 | **Qwen practical route:** no hosted endpoint reproduces the BF16 checkpoint | explicit deviation ladder D0–D3; D2 (DeepInfra FP4, native context) chosen with verbatim disclosure text; D1 upgrade path; D3 (context extension) rejected |

## 4. Unresolved issues (block the stage named)

| Issue | Blocks | Prerequisite |
|---|---|---|
| Z.ai: does `max_tokens` include reasoning? | C_max value; P27/P28 calibration | Z.ai answer (20 §2) and/or integration test T2 |
| DeepInfra MiMo checkpoint/revision and "fp8" meaning | P35 labelling | DeepInfra answer (20 §1, Q1–Q2); otherwise H-MiMo-Xiaomi |
| DeepInfra Qwen FP4 source weights, native context, template, effort mapping (`xhigh` vs its `high`) | P34 disclosure; the effort setting is actually applied | DeepInfra answer (20 §1, Q7–Q12); integration T3a/T3b/T4 |
| Bitdeer FP8 identity (D1 upgrade) | optional | Bitdeer answer (20 §4) |
| First-party served precision (DeepSeek, Z.ai, Moonshot) | full disclosure only | answers, or recorded "undisclosed" |
| Provider alias drift | reproducibility | drift abort, short windows, dates recorded |
| Seeds unsupported on most routes | bit-level reproducibility | disclosed; configuration-level only |
| List prices (Kimi $12 vs $15) | budgeting | re-verify |

**Closed since v2:**
- Math-Verify installation and testing;
- scorer fixture suites;
- BBEH suffix provenance.

## 5. Fairness limits by design (disclose, don't fix)

Carried from v1/v2:
- different sampling across families;
- tokens are not compute;
- effort prompts differ;
- a single generation at temperature 1;
- contamination;
- a purposive sample;
- a ceiling effect on MATH-500;
- heterogeneous serving stacks;
- partly undisclosed precision;
- provider-fixed sampling;
- the common ceiling is below some publisher recommendations.

**Sharpened in v3:**
- **Qwen is served below its native precision** (FP4, deviation D2) while the others run at publisher-native formats.
- **This can only disadvantage Qwen,** if it matters at all. It is disclosed in every table (20 §3). No precision-effect estimate is claimed, and a D1 replication is listed as future work.
- **BBEH comparability:** BBEH is now the official Mini, so its numbers are comparable to published Mini micro-averages. Settings are not matched to the paper's, so comparisons are qualitative.

## 6. Reproducibility record per attempt

As in v2 (route ID, payload hash, model echo, settings sent, finish reason, token counts, raw text, status, flags, cost, date), **plus** the scorer version: the `vendor-lock.json` hash and `requirements-lock.txt`.

## 7. Verdict

- **Local preparation is complete.** Every check that needs no provider and no model passes.
- **The integration test is technically ready** (34 requests, a $15 cap, synthetic prompts). It can start as soon as you:
  - (a) create accounts and keys at DeepInfra, DeepSeek, Z.ai and Moonshot;
  - (b) write the authorisation file;
  - (c) authorise it.
- **The provider questions can be sent in parallel.** Their answers settle labelling and disclosure rather than whether the test can run. The exception is Z.ai: its answer about `max_tokens` is also measured directly by T2.
- **Nothing has been authorised beyond stage 1.**

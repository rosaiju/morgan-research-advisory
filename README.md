# Choosing an open-weight LLM for the Morgan lab server

Last updated 2026-10-28. Author: Rohan Sainju (rosai2@morgan.edu).

Every number below comes from a file in this repository, from the run logs and results files
(`local/runs/`, which git does not track), or from the Stage 2B results archive (`REPORT.md` and its notes, kept
outside git). Anything not in those files is marked **TODO**.

**No benchmark questions, answer keys or model answers appear in this README or anywhere in git.** Answer keys,
benchmark data and rendered prompts are git-ignored (see `.gitignore`).

---

## 1. What this project is

We are testing open-weight large language models to find the strongest one to run on the Morgan lab GPU server
for students. We only **run** the models (inference) and **score** their answers on fixed benchmarks. We do not
train or fine-tune any model (fine-tuning is listed as out of scope in `01-study-scope.md`).

---

## 2. Status at a glance

Times from the logs are in UTC.

| Stage | Dates | What was done | Main result | Status |
|---|---|---|---|---|
| Model selection | 2026-09-29 to 2026-10-02 | Built a 35-model candidate list, narrowed it to a 6-model hosted-API plan, then switched to 7 models that run locally | 7 models chosen for local testing | Done |
| Stage 1 (home computer) | Calibration 2026-10-02; probes 2026-10-03; official run 2026-10-04 (04:54 to 15:32); finalists recorded 2026-10-05 | 7 models x 22 items, 6,144 thinking tokens + 1,536 answer tokens | Qwen3.8-27B and Gemma 4 31B 21/22, gpt-oss-20b 20/22; these 3 went to Stage 2 | Done |
| Stage 2 (home + lab server) | gpt-oss-20b at home 2026-10-05 to 10-06; Qwen3.8-27B and Gemma 4 31B on the lab server 2026-10-15 to 10-17; analysis 2026-10-19 | 3 models x 284 new items, 16,384 thinking tokens + 2,048 answer tokens | Qwen 235/284 (82.7%), Gemma 233/284 (82.0%), gpt-oss 198/284 (69.7%). Qwen and Gemma are not significantly different; both beat gpt-oss | Done (forced-item reruns for Qwen and Gemma not yet run, see section 10) |
| Stage 2B (expanded benchmarks) | Set-up and pilot 2026-10-23; run started 2026-10-24; generation finished and scored 2026-10-28 | Qwen3.8-27B and Gemma 4 31B x 503 new items from 6 benchmarks (Tier 1), on the lab server, same settings as Stage 2 | Qwen 65.6%, Gemma 62.4%. Qwen is slightly ahead but not significantly (p = 0.068). Tied on GPQA; Qwen leads on coding and reasoning (section 7B) | Done; re-graded 2026-10-28 by an independent judge, no score changed (6 more benchmarks ready to run, see section 10) |

---

## 3. Earlier reports and how they fit together

These are the report-style documents in the repo, oldest first.

| Date | File | What it covered | Still current? |
|---|---|---|---|
| 2026-09-29 | `00-professor-brief.md` | First proposal: a 3-model explanatory study (Granite 4.2 8B, Qwen3.5 9B, Phi-4 Reasoning) | **Fully replaced** (the file itself says it is superseded) |
| 2026-09-29 | `14-capability-first-shortlist.md`, `18-final-candidate-and-execution-audit.md`, `19-readiness-and-calibration-plan.md` | Narrowing the candidate pool to 6 very large models to be run through paid hosted APIs | **Fully replaced** for what we ran (no API request was ever sent). Still the record of how the candidate pool was built |
| 2026-09-29 to 2026-10-03 | Old `README.md` (now replaced by this file; the old text is in git history) | Index of the API-era documents, with a banner pointing to the local plan | **Fully replaced** |
| 2026-10-02 | `local/REVISED_PROPOSAL_2026-10-02.md` | Why long reasoning budgets were impractical on the home computer; new placement rule, forced 6,144-token budget, smaller Stage 1 panel | **Partly replaced**: the Stage 1 parts were approved and used; its Stage 2 section (section 7) was replaced by the actual Stage 2 plan |
| 2026-10-02 to 10-03 | `22-local-evaluation-plan.md` | Local plan for 7 models and the probe speed results | **Partly replaced**: still correct for Stage 1; says nothing about Stage 2 |
| 2026-10-05 | `local/STAGE2_FINALISTS.md` | Stage 1 results and the rule that picked the 3 finalists | **Current** |
| 2026-10-05 | `local/STAGE2_PROJECTION.md` | Projected Stage 2 run times on the home computer | **Partly replaced**: Qwen and Gemma were actually run on the lab server (section 6) |
| 2026-10-06 | `local/stage2/sensitivity/forced_rerun_comparison_local-rtx4060_gpt-oss-20b.md` | gpt-oss-20b forced-item rerun at 24,576 tokens | **Current** |
| 2026-10-08 | `local/stage2/MORGAN_HANDOFF.md` | Operator guide for running Qwen and Gemma on the lab server | **Partly replaced**: the hardware it calls "not yet confirmed" is now known (section 5), and the run used GPU index 1, not 0 |
| 2026-10-19 | `local/analysis/stage2_paired_analysis.md` | Stage 2 scores, McNemar tests and bootstrap confidence intervals | **Current** |

TODO: confirm which of these were actually sent to Dr. Wang, and whether any report was sent outside this repo
(for example by email) that should be listed here.

**This README now replaces all of the reports above.** The files are kept as the detailed record.

---

## 4. How we chose the models (35 to 7 to 3)

### 4.1 Where the list of 35 came from

- `12-candidate-pool-revalidated.md` (2026-09-29) lists **34 candidates (P01 to P34)**. They came from a bounded
  search of publisher model pages, release notes and independent evaluator pages (Artificial Analysis, Epoch),
  plus the 8 models from the earlier laptop pilot. The search terms are in `11-search-log.md` and `12`.
- `18-final-candidate-and-execution-audit.md` added a 35th, **MiMo-V2.6-Pro** (released 2026-09-22), because
  it had been missed.

### 4.2 The narrowing steps, in order

The files do **not** describe a set of mechanical filters (license, GPU fit, release date, score cut-offs) that
cut 35 to 7. What they record is the following sequence:

| Step | File | Rule as written | Effect |
|---|---|---|---|
| A. Build the pool | `12` | Include released open-weight models relevant to English text reasoning; exclude math-only, code-only, OCR, safety and unofficial derivative models | 34 candidates |
| B. Capability-first shortlist | `14` | Expert judgement, not a score cut-off: exact released weights; documented reasoning mode; strong broad-capability evidence; relevance to open comparisons; avoid near-duplicates. **Hardware, price, speed and existing downloads were explicitly not used.** | 34 to 6 (28 dropped; the reason for each is in `14`) |
| C. Candidate audit | `18` | Add the missed MiMo-V2.6-Pro; replace DeepSeek-V4.1-Flash because it had the weakest no-tools reasoning evidence of the group (lowest on HLE, CritPt and Omniscience in Artificial Analysis components) | +1, -1: still 6 (the "v2" set) |
| D. Switch to local runs | `22`, `local/REVISED_PROPOSAL_2026-10-02.md` | Run on the home computer with llama.cpp instead of paid APIs. None of the 6 hosted models was kept. Seven smaller models were used instead: 6 from the pool (each had been dropped at step B) plus Ministral 3 14B Reasoning, which is not in the 35 | 7 models |
| E. Stage 1 screening | `local/STAGE2_FINALISTS.md` | Top 3 under the frozen Stage 1 scoring rules | 7 to 3 |

Why the project moved from hosted APIs to local runs: after we calculated the cost, running the models through APIs came out too high and was not worth it.

TODO: the rule used to pick the 7 local models at step D, including why Ministral 3 14B Reasoning was added from
outside the pool.

### 4.3 All 35 candidates

"Size" is as stated in the files (`12`, `14`, `18`, `03`, or the model's own card in `local/official/`). A size
written as "total / active" is a mixture-of-experts model.

| ID | Model | Size | Where it was dropped |
|---|---|---|---|
| P01 | Qwen3.5-9B | 9B | Step B |
| P02 | **Qwen3.8-27B** | 27B | **Kept: Stage 2 finalist** (dropped at B, brought back at D) |
| P03 | Qwen3.6-35B-A3B | 35B / 3B active | Step B |
| P04 | Gemma 4 12B | 11.95B | Step B |
| P05 | Gemma 4 26B-A4B | 25.2B / 3.8B active | Step B |
| P06 | **Gemma 4 31B** | 30.7B | **Kept: Stage 2 finalist** (dropped at B, brought back at D) |
| P07 | **gpt-oss-20b** | 21B / 3.6B active | **Kept: Stage 2 finalist** (dropped at B, brought back at D) |
| P08 | Nemotron 3 Nano 30B-A3B | 30B / 3.5B active | Step B |
| P09 | Granite 4.2 8B | 8B | Step B |
| P10 | Muse Glimmer 30B | 29.6B | Step E (Stage 1); dropped at B, brought back at D |
| P11 | GLM-4.7-Flash | 30B / 3B active | Step E (Stage 1); dropped at B, brought back at D |
| P12 | DeepSeek-R1-0528-Qwen3-8B | 8B | Step E (Stage 1); dropped at B, brought back at D |
| P13 | DeepSeek-R1-Distill-Qwen-32B | 32B | Step B |
| P14 | Olmo 3.1 32B Think | 32B | Step B |
| P15 | EXAONE 4.5 33B | 33B | Step B |
| P16 | Phi-4-reasoning-plus | 14B | Step B |
| P17 | gpt-oss-120b | 117B / 5.1B active | Step B |
| P18 | Nemotron 3 Super 120B-A12B | 120B / 12B active | Step B |
| P19 | Ling-3.0-flash | 124B / 5.1B active | Step B |
| P20 | Mistral-Small-4-119B | 119B | Step B |
| P21 | Mistral-Medium-3.5-128B | 128B | Step B |
| P22 | Step-3.5-Flash | about 196B / about 11B active | Step B |
| P23 | DeepSeek-V4-Flash-0731 | not stated in our sources | Step B |
| P24 | DeepSeek-V4.1-Flash | 552B backbone plus extra memory | Step C (replaced by MiMo) |
| P25 | DeepSeek-V4-Pro-0813 | not stated in our sources | Step D (hosted plan dropped; never run) |
| P26 | DeepSeek-R1-0528 (full) | not stated in our sources | Step B |
| P27 | GLM-5.3-Flash | 320B / 18B active | Step D (hosted plan dropped; never run) |
| P28 | GLM-5.3 | not stated in our sources | Step D (hosted plan dropped; never run) |
| P29 | Kimi-K3 | not stated in our sources | Step D (hosted plan dropped; never run) |
| P30 | MiniMax-M3 | not stated in our sources | Step B |
| P31 | Inkling-Small | not stated in our sources | Step B |
| P32 | Inkling | not stated in our sources | Step B |
| P33 | Nemotron 3 Ultra 550B-A55B | 550B / 55B active | Step B |
| P34 | Qwen3.8-2.4T-A95B | 2.4T / 95B active | Step D (hosted plan dropped; never run) |
| P35 | MiMo-V2.6-Pro-RL | 1.02T / 42B active | Step D (hosted plan dropped; never run) |
| (not in pool) | Ministral 3 14B Reasoning | 14B | Added at step D; dropped at step E (Stage 1) |


### 4.4 From 7 to the 3 models tested in Stage 2

Rule (`local/STAGE2_FINALISTS.md`, recorded 2026-10-05 before any Stage 2 item existed): **take the three
highest scores under the frozen Stage 1 scoring rules.**

| Rank | Model | Stage 1 score |
|---|---|---|
| 1= | Qwen3.8-27B | 21/22 |
| 1= | Gemma 4 31B | 21/22 |
| 3 | gpt-oss-20b | 20/22 |
| 4= | DeepSeek-R1-0528-Qwen3-8B, GLM-4.7-Flash, Muse Glimmer 30B | 19/22 |
| 7 | Ministral 3 14B Reasoning | 16/22 |

The same file says plainly that 22 items cannot show the finalists are better than the next three: the top six
are within two items of each other.

Note: Stage 2 tested **3** models, not 2.

---

## 5. System setup

### 5.1 Home computer (Stage 1, and gpt-oss-20b in Stage 2)

Source: `local/REPRODUCIBILITY.md`, `local/runs/*/RUN_INFO.json`.

| Part | Value |
|---|---|
| GPU and VRAM | NVIDIA GeForce RTX 4060, 8 GB (8,188 MiB); driver 591.86 (driver CUDA 13.1) |
| Other GPUs | None listed |
| CPU | Intel Core i7-14700F, 20 cores / 28 threads |
| RAM | 32 GB (2 x 16 GB DDR5 at 4,400 MT/s) |
| Storage | Kingston SNV3S1000G NVMe SSD |
| OS | Windows 11 Home 10.0.26200 |

### 5.2 Lab server (Qwen3.8-27B and Gemma 4 31B in Stage 2 and Stage 2B)

Source: `local/runs/stage2-morgan-gpu/RUN_INFO.json`, `local/stage2/STAGE2_DEVIATIONS.md`, Stage 2B `DECISIONS.md`.

| Part | Value |
|---|---|
| GPU and VRAM | NVIDIA RTX 4500 Ada Generation, 24 GB (24,570 MiB); driver 595.99.02 (driver CUDA 13.2) |
| Other GPUs | 2 x NVIDIA T1000 (8 GB each), not used for the runs. The RTX 4500 Ada is GPU index 1 (`CUDA_VISIBLE_DEVICES=1`) |
| CPU | 48 physical / 96 logical cores. CPU model not recorded |
| RAM | 123.2 GB as reported by the harness |
| Storage | Models and runs on a separate `/data` volume, about 10.6 TB |
| OS | Ubuntu 26.04 LTS (upgraded from 22.04), kernel 6.8.0-147-generic |

### 5.3 Software

| Item | Home computer | Lab server |
|---|---|---|
| llama.cpp | build b11349, commit `fb4b2737a` (official Windows CUDA binaries) | build b11349, commit `fb4b2737a` (built from a git clone) |
| CUDA | 12.4 runtime (bundled with the binaries) | 12.4 |
| Compiler | Clang 20.1.8 (as reported by `llama-server --version`) | gcc-13 as the CUDA host compiler; `llama-server --version` reports "built with GNU 15.2.0" |
| Python | 3.13.7 for the harness; 3.14.4 for prompt rendering and scoring | 3.13.16 |
| Package manager | pip with `venv` (`local/requirements-local-lock.txt`, `scoring/requirements-lock.txt`) | uv |
| Docker grader image | `python@sha256:0741d101873c12ab927e6f8653feb8862b9bd58771177acb1b885b95141f91b4` (python:3.14-slim), Docker Engine 28.5.1. Used only to grade the student programming items, only at home | Not used (all scoring is done at home) |

Common llama.cpp settings for every run: official publisher chat template, flash attention on, q8_0 KV cache, no
memory-mapping, prompt cache off, one request at a time, 8 CPU threads, no speculative decoding, text only.
Full list: `local/config_local.json` -> `backend.common_server_args`.

### 5.4 Models run

All models are 4-bit `Q4_K_M` GGUF files from `bartowski`, except gpt-oss-20b, which uses its native MXFP4. Exact
file revisions and SHA-256 hashes: `local/gguf_pins.json`. Sampling settings: `local/REPRODUCIBILITY.md` section 4.

**Stage 1 (home computer):** context 10,496 tokens; budget 6,144 thinking + 1,536 answer tokens. VRAM and speed
come from the probe (`22-local-evaluation-plan.md`, `local/HANDOFF.md`).

| Model (source checkpoint) | Parameters | Quant | File size | VRAM added at load | RAM added | Decode tok/s (fresh / after 8K) |
|---|---|---|---|---|---|---|
| deepseek-ai/DeepSeek-R1-0528-Qwen3-8B | 8B | Q4_K_M | 5.0 GB | 5.5 GB | 0.8 GB | 47.3 / 39.6 |
| openai/gpt-oss-20b | 21B / 3.6B active | MXFP4 | 12.1 GB | 6.2 GB | 6.4 GB | 42.2 / 40.5 |
| zai-org/GLM-4.7-Flash | 30B / 3B active | Q4_K_M | 18.5 GB | 6.2 GB | 12.6 GB | 34.4 / 30.4 |
| mistralai/Ministral-3-14B-Reasoning-2512 | 14B | Q4_K_M | 8.2 GB | 6.0 GB | 3.4 GB | 13.4 / 12.9 |
| meta-models/Muse-Glimmer-30B | 29.6B | Q4_K_M | 17.3 GB | 6.0 GB | 11.6 GB | 3.63 / 3.61 |
| Qwen/Qwen3.8-27B | 27B | Q4_K_M | 17.4 GB | 5.8 GB | 12.3 GB | 3.40 / 3.29 |
| google/gemma-4-31B-it | 30.7B | Q4_K_M | 19.6 GB | 5.9 GB | 15.9 GB | 2.61 / 2.50 |

On the 8 GB card, most of each larger model's weights sat in system RAM, which is why the dense ~30B models ran at
about 3 tokens per second.

**Stage 2:** budget 16,384 thinking + 2,048 answer tokens. VRAM is from the Stage 2 probe and the run telemetry;
speed is from the probe and the official run (`local/runs/stage2-*`).

| Model | Machine | Context | VRAM used at load / peak in run | Placement | Decode tok/s (fresh / at 16K) | Average tok/s over the whole run |
|---|---|---|---|---|---|---|
| gpt-oss-20b | Home | 23,296 | 6,865 / 7,259 MiB (whole card, includes the Windows desktop) | Experts split between GPU and CPU | 40.8 / 37.4 | 39.0 |
| Qwen3.8-27B | Lab server | 23,552 | 17,096 / 17,126 MiB | Entirely on GPU | 21.0 / 20.1 | 21.2 |
| Gemma 4 31B | Lab server | 23,552 | 20,842 / 20,858 MiB | Entirely on GPU | 17.8 / 15.3 | 17.5 |

---

## 6. Run time: home computer vs lab server

Times come from the attempt logs: start = model server start, end = last item finished. Every official run
finished every item on its first attempt, with no errors and no resumes.

### 6.1 Measured run times

| Run | Machine | Items | Budget | Qwen3.8-27B | Gemma 4 31B | gpt-oss-20b |
|---|---|---|---|---|---|---|
| Stage 1 | Home | 22 | 6,144 + 1,536 | 2.26 h | 3.47 h | 0.38 h |
| Stage 2 | Lab server | 284 | 16,384 + 2,048 | **16.29 h** | **15.76 h** | not run there |
| Stage 2 | Home | 284 | 16,384 + 2,048 | not run (projected only) | not run (projected only) | **12.47 h** |

The full Stage 1 run (all 7 models) took 10.64 h. Qwen and Gemma together took **32.05 h** on the lab server
(2026-10-15 16:37 to 2026-10-17 00:41 UTC).

### 6.2 Speed-up on the same work

Qwen and Gemma never ran the full Stage 2 at home, so there is no measured home time for the same 284 items. The
closest same-work comparisons are:

| Comparison | Model | Home | Lab server | Speed-up |
|---|---|---|---|---|
| Same development item, same Stage 2 settings (Stage 2 probe) | Qwen3.8-27B | 3.20 tok/s | 21.69 tok/s | 6.8x |
| | Gemma 4 31B | 2.52 tok/s | 18.42 tok/s | 7.3x |
| Decode speed at 16K tokens of context (Stage 2 probe) | Qwen3.8-27B | 3.02 tok/s | 20.06 tok/s | 6.6x |
| | Gemma 4 31B | 2.09 tok/s | 15.26 tok/s | 7.3x |
| Full Stage 2 run: home **projection** (realistic case, `local/STAGE2_PROJECTION.md`) vs lab server **measured** | Qwen3.8-27B | 122.2 h (5.1 days) | 16.29 h | 7.5x |
| | Gemma 4 31B | 166.5 h (6.9 days) | 15.76 h | 10.6x |
| | Both | 288.7 h (12.0 days) | 32.05 h | 9.0x |

On the same item, wall time was 231.9 s at home vs 50.7 s on the server for Qwen, and 271.1 s vs 40.8 s for
Gemma. The two machines wrote slightly different numbers of tokens for that item, so tokens per second is the
fairer measure.

The projection's range was 63 to 193 h for Qwen and 85.7 to 266 h for Gemma. Gemma's projection was high partly
because it assumed about 5,127 tokens per item, but Gemma actually wrote about 3,484 per item on the server (Qwen:
4,889 assumed, about 4,378 actual).

### 6.3 Checking "5 to 6 days down to 13 hours"

- **5 to 6 days** fits the home projections: 5.1 days for Qwen, 6.9 days for Gemma. These were projections from
  Stage 1 speeds. They were never measured, because those runs were moved to the lab server.
- **13 hours** does not match any lab-server run. Measured lab-server times were **16.29 h** (Qwen) and **15.76 h**
  (Gemma), 32.05 h for both. The only run near 13 hours is **gpt-oss-20b at home: 12.47 h**, which is a different
  model on a different machine.
- So the accurate statement is: **about 5 days (Qwen) and 7 days (Gemma) projected at home, versus about 16 hours
  each measured on the lab server.** That is about 7 to 11 times faster per model, and about 7 times faster on
  the same item.

---

## 7. Benchmarks and results

### 7.1 Stage 2 benchmarks

The same 284 items for every model, chosen with a fixed seed and excluding every item used before
(`local/stage2/SELECTION_AUDIT.md`).

| Benchmark | Items | What it tests | How it is scored |
|---|---|---|---|
| MMLU-Pro | 61 | Knowledge and reasoning, 14 subjects, multiple choice | Extracted answer letter vs key |
| MATH-500 | 58 | Competition math, all 7 subjects, levels 1 to 5 | Math-Verify equivalence check |
| BBEH (mini) | 67 | Hard reasoning puzzles, 23 task types | Official BBEH answer matching |
| IFEval | 80 | Following formatting instructions | Official checker, strict prompt-level |
| Student suite | 18 | Student-style tasks: programming, algorithms, debugging, concepts, reasoning, instruction following (3 each) | The app's own grader; programming items run in the Docker sandbox |

Only the final answer is scored; reasoning text is never scored. Statuses: CORRECT, INCORRECT,
EXTRACTION_FAILURE (no answer in the required format), BUDGET_TRUNCATED (ran out of tokens, or stopped by the loop
detector). Everything except CORRECT counts as wrong.

### 7.2 Stage 2 scores

From `local/analysis/stage2_paired_analysis.md`. Brackets are 95% Wilson confidence intervals.

| Model | Overall | MMLU-Pro | MATH-500 | BBEH | IFEval | Student |
|---|---|---|---|---|---|---|
| Qwen3.8-27B | **235/284 = 82.7%** [77.9, 86.7] | 46/61 = 75.4% | 56/58 = 96.6% | 42/67 = 62.7% | 74/80 = 92.5% | 17/18 = 94.4% |
| Gemma 4 31B | **233/284 = 82.0%** [77.2, 86.1] | 49/61 = 80.3% | 56/58 = 96.6% | 38/67 = 56.7% | 75/80 = 93.8% | 15/18 = 83.3% |
| gpt-oss-20b | **198/284 = 69.7%** [64.1, 74.8] | 41/61 = 67.2% | 51/58 = 87.9% | 22/67 = 32.8% | 68/80 = 85.0% | 16/18 = 88.9% |

### 7.3 Truncated and other failed items

| Model | Correct | Incorrect | Extraction failure | Budget truncated | Truncated items by benchmark |
|---|---|---|---|---|---|
| Qwen3.8-27B | 235 | 43 | 0 | 6 | all 6 in BBEH |
| Gemma 4 31B | 233 | 39 | 0 | 12 | all 12 in BBEH |
| gpt-oss-20b | 198 | 70 | 8 | 8 | 6 BBEH, 2 IFEval |

Items where the model hit the 16,384-token thinking limit and was told to answer ("forced conclusion"): Qwen 31,
Gemma 1, gpt-oss 56 (from the scored files).

With truncated items removed, the scores become Qwen 84.5%, Gemma 85.7% and gpt-oss 71.7%. The conclusions below
do not change.

### 7.4 Paired statistical tests

Each pair is compared on the same items. McNemar's exact test uses the items where only one model was right. The
bootstrap uses 10,000 resamples. There are 3 comparisons, so a strict (Bonferroni) cut-off would be p < 0.0167.

| Pair | Only A right | Only B right | McNemar p | Difference A - B (95% CI) | Significant? |
|---|---|---|---|---|---|
| Qwen vs Gemma | 17 | 15 | 0.86 | +0.7 points [-3.2, +4.6] | **No** |
| Qwen vs gpt-oss | 44 | 7 | 1.2 x 10^-7 | +13.0 points [+8.5, +17.6] | **Yes** |
| Gemma vs gpt-oss | 49 | 14 | 1.1 x 10^-5 | +12.3 points [+7.0, +17.6] | **Yes** |

In plain words:

- **Qwen3.8-27B and Gemma 4 31B are tied.** The 2-item gap is well within chance, and the confidence interval
  includes zero. It also flips direction when truncated items are removed (Gemma +1.1 points, p = 0.68).
- **Both are clearly better than gpt-oss-20b**, by about 12 to 13 points. This holds with truncated items removed
  too, and passes the strict cut-off.
- Per-benchmark differences (for example Qwen's lead on BBEH and Gemma's on MMLU-Pro) are based on small samples
  and were not tested. Treat them as descriptive only.

### 7.5 Sensitivity check: gpt-oss-20b with a bigger budget

Policy B (pre-registered 2026-10-05, before any Stage 2 run) reruns up to 20 randomly chosen forced items at
24,576 thinking tokens. For gpt-oss-20b, 6 of the 20 were correct officially and 8 in the rerun (2 changed from
wrong to right, none from right to wrong). 16 of the 20 still hit the larger limit. **The official score stays
198/284.** Source: `local/stage2/sensitivity/forced_rerun_comparison_local-rtx4060_gpt-oss-20b.md`.

### 7.6 Stage 1 results (for reference)

7 models x 22 items (MMLU-Pro 5, MATH-500 3, BBEH 2, IFEval 6, student suite 6), from `local/runs/stage1-v2/scored.jsonl`.

| Model | Total | MMLU-Pro | MATH-500 | BBEH | IFEval | Student |
|---|---|---|---|---|---|---|
| Qwen3.8-27B | 21/22 | 5/5 | 3/3 | 1/2 | 6/6 | 6/6 |
| Gemma 4 31B | 21/22 | 5/5 | 3/3 | 1/2 | 6/6 | 6/6 |
| gpt-oss-20b | 20/22 | 4/5 | 3/3 | 1/2 | 6/6 | 6/6 |
| DeepSeek-R1-0528-Qwen3-8B | 19/22 | 4/5 | 3/3 | 1/2 | 5/6 | 6/6 |
| GLM-4.7-Flash | 19/22 | 4/5 | 3/3 | 2/2 | 4/6 | 6/6 |
| Muse Glimmer 30B | 19/22 | 4/5 | 3/3 | 1/2 | 5/6 | 6/6 |
| Ministral 3 14B Reasoning | 16/22 | 5/5 | 1/3 | 0/2 | 4/6 | 6/6 |

---

## 7B. Stage 2B results (expanded benchmarks)

Source: the Stage 2B `REPORT.md` (scored 2026-10-28 05:54 UTC) and `REPORT_REGRADED.md` / `REGRADE_SUMMARY.md`
(re-graded 2026-10-28), with `DECISIONS.md`, `DEVIATIONS.md`, `RUN_PLAN.md` and `HANDOFF.md` from the same run. Only scores are shown here. Benchmark terms (for example GPQA and
Humanity's Last Exam) forbid reposting their items, so no questions, answer keys or model answers are published.

### 7B.1 What it tests and why

Stage 2 showed Qwen3.8-27B and Gemma 4 31B were tied. Stage 2B tests the same two models on **503 new questions**
covering skills Stage 2 did not test, to see if either one pulls ahead.

- **When:** set-up and pilot 2026-10-23; main run started 2026-10-24 (02:29 UTC); generation finished 2026-10-28
  (04:55 UTC); judging and scoring finished 2026-10-28 (05:54 UTC); re-graded with an independent judge
  2026-10-28 (18:00 UTC).
- **Where and how:** lab server, RTX 4500 Ada (GPU index 1), one model at a time. Same llama.cpp build, model
  files and settings as Stage 2 (16,384 thinking + 2,048 answer tokens).

| Skill | Benchmark | Items |
|---|---|---|
| Graduate-level science | GPQA Diamond | 198 |
| Coding | LiveCodeBench | 60 |
| Hallucination (short facts) | SimpleQA Verified | 80 |
| Expert-level questions | Humanity's Last Exam, text only (27 multiple choice + 53 short answer) | 80 |
| Multi-step reasoning | MuSR | 45 |
| Code reasoning | CRUXEval (output prediction) | 40 |
| | **Total** | **503** |

### 7B.2 Scores

Accuracy = percent fully correct. Items that ran out of tokens count as wrong. Brackets are 95% Wilson confidence
intervals.

| Benchmark | Items | Qwen3.8-27B | Gemma 4 31B |
|---|---|---|---|
| GPQA Diamond | 198 | 87.4% [82.0, 91.3] | 87.4% [82.0, 91.3] |
| LiveCodeBench | 60 | 83.3% [72.0, 90.7] | 73.3% [61.0, 82.9] |
| SimpleQA Verified | 80 | 13.8% [7.9, 23.0] | 11.2% [6.0, 20.0] |
| Humanity's Last Exam | 80 | 17.5% [10.7, 27.3] | 20.0% [12.7, 30.0] |
| MuSR | 45 | 95.6% [85.2, 98.8] | 84.4% [71.2, 92.3] |
| CRUXEval | 40 | 97.5% [87.1, 99.6] | 85.0% [70.9, 92.9] |
| **Overall** | **503** | **65.6% [61.4, 69.6]** | **62.4% [58.1, 66.5]** |
| Average of the 6 benchmarks | | 65.8% | 60.2% |

With out-of-token items removed, overall scores are Qwen 66.5% (n = 496) and Gemma 64.2% (n = 489).

### 7B.3 Paired tests (same items for both models)

"Only Qwen right" and "Only Gemma right" are the items where exactly one model was correct. McNemar's exact test
uses those items; the confidence interval is a bootstrap.

| Benchmark | Qwen - Gemma (points) | 95% CI | Only Qwen right | Only Gemma right | McNemar p |
|---|---|---|---|---|---|
| GPQA Diamond | +0.0 | [-4.0, +4.0] | 9 | 9 | 1.00 |
| LiveCodeBench | +10.0 | [+0.0, +20.0] | 8 | 2 | 0.11 |
| SimpleQA Verified | +2.5 | [-5.0, +10.0] | 6 | 4 | 0.75 |
| Humanity's Last Exam | -2.5 | [-12.5, +7.5] | 8 | 10 | 0.81 |
| MuSR | +11.1 | [+2.2, +20.0] | 5 | 0 | 0.06 |
| CRUXEval | +12.5 | [+0.0, +25.0] | 6 | 1 | 0.13 |
| **Overall** | **+3.2** | **[+0.0, +6.4]** | **42** | **26** | **0.068** |

In plain words:

- **Qwen is slightly ahead (65.6% vs 62.4%), but not significantly** (p = 0.068).
- **They tied on GPQA** (87.4% each).
- **Qwen's leads are on coding and reasoning**: LiveCodeBench (+10), CRUXEval (+12.5) and MuSR (+11.1). Each of
  these is a small sample and none is significant on its own.
- Both models got most SimpleQA and Humanity's Last Exam questions wrong; the gaps there are small and go both ways.

### 7B.4 Stage 2 and Stage 2B together

| Set | Items | Qwen3.8-27B | Gemma 4 31B | Qwen - Gemma (points) | 95% CI | McNemar p |
|---|---|---|---|---|---|---|
| Stage 2 | 284 | 82.7% [77.9, 86.7] | 82.0% [77.2, 86.1] | +0.7 | [-3.2, +4.6] | 0.86 |
| Stage 2B | 503 | 65.6% [61.4, 69.6] | 62.4% [58.1, 66.5] | +3.2 | [+0.0, +6.4] | 0.068 |
| **Combined** | **787** | **71.8% [68.5, 74.8]** | **69.5% [66.2, 72.6]** | **+2.3** | **[-0.1, +4.7]** | **0.089** |

Across all 787 items, Qwen is about 2 points ahead, and the difference is still not significant.

### 7B.5 Speed, thinking and memory

| Model | Mean time per item | Median time per item | Total time (503 items) | Mean thinking tokens | Mean total tokens written | Peak GPU memory |
|---|---|---|---|---|---|---|
| Qwen3.8-27B | 420 s | 369 s | 58.7 h | 8,632 | 8,914 | 17,126 MiB |
| Gemma 4 31B | 284 s | 226 s | 39.7 h | 4,406 | 4,976 | 20,858 MiB |

In plain words:

- **Qwen thinks about twice as much** (8,632 vs 4,406 thinking tokens per item) and **takes about 1.5 times as
  long** (420 s vs 284 s per item).
- **Qwen hit the 16,384-token thinking limit on 168 of 503 questions; Gemma did on 1.** At the limit the model is
  told to stop thinking and answer, and that answer is scored as usual (the same rule as Stage 2).
- **Sensitivity check:** if every item that hit the thinking limit is counted as wrong, Qwen drops to **50.7%** and
  Gemma stays at **62.4%**. So part of Qwen's score comes from answers it gave only after being cut off.
- Separately, some items ran out of the answer allowance and were counted wrong: Qwen 7, Gemma 14.
- Gemma uses more GPU memory (about 20.9 GB vs 17.1 GB at peak). Both fit on the 24 GB card.

### 7B.6 How answers were graded

- GPQA, MuSR and Humanity's Last Exam multiple-choice items are checked by matching the answer letter or choice.
  LiveCodeBench and CRUXEval are checked by running the code against tests.
- SimpleQA Verified and the 53 short-answer Humanity's Last Exam items need a model to judge whether the answer
  matches the reference. That is **257 judged answers** across both models.
- The planned judge, gpt-oss-20b, was not on the lab server at first, so **Qwen3.8-27B was the first judge** (low
  reasoning effort, temperature 0). This meant **Qwen graded its own answers** on these two benchmarks, which could
  have favoured Qwen.
- **Independent re-judge (2026-10-28):** gpt-oss-20b, which is not one of the models being compared, re-judged all
  **257** judged answers (129 of Qwen's, 128 of Gemma's). It used the same answers, judge code and official
  prompts; nothing was regenerated. Source: `REPORT_REGRADED.md`, `REGRADE_SUMMARY.md`.
- **The two judges agreed on correct vs incorrect for all 257 answers, so no score changed.** The only difference:
  3 of Gemma's SimpleQA answers were graded "not attempted" by Qwen and "incorrect" by gpt-oss. Both count as wrong.
  So there is no sign that Qwen favoured itself, and every result above stays the same.
- **Limit:** most judged answers are clearly wrong (about 16% are correct), which makes it easy for two judges to
  agree. Agreement shows the result did not depend on Qwen grading itself, but it does not prove both judges were
  right.
- A **human spot-check of 40 judged items** (20 SimpleQA, 20 Humanity's Last Exam, both models) is in progress.

---

## 8. Changes from the original plan

Each item is documented in the file named.

1. **Paid hosted APIs replaced by local runs** (`22`, 2026-10-02). The plan in `14` to `19` was to run 6 very large
   models through APIs. No API request was ever sent; 7 smaller models were run locally with llama.cpp instead.
   Reason: after we calculated the cost, using APIs came out too high and was not worth it.
2. **Long calibration stopped after 4 of 7 models** (`local/REVISED_PROPOSAL_2026-10-02.md`). At the
   pre-registered 24,576-token budget, Stage 1 projected to 300+ hours against a 24 to 48 hour budget. Muse, Qwen
   and Gemma got short speed probes instead.
3. **Forced 6,144 + 1,536 token budget for Stage 1** (same file). The model is told to stop thinking and answer
   at the limit, so no answer is lost to truncation.
4. **Placement rule** (same file). Attention layers and KV cache stay on the GPU; feed-forward or expert weights
   move to the CPU first. This avoided a large slowdown as context grew.
5. **Smaller Stage 1 panel** (same file). 22 items per model, a fixed subset of the already-locked 44-item core
   panel, to fit about 24 hours.
6. **Muse Glimmer forcing done by the harness** (commit `685dfcb`). llama.cpp's built-in budget forcing did not
   work on Muse's reasoning format, so the harness does the same thing in two steps.
7. **Stage 2 split across two machines** (`local/stage2/MORGAN_HANDOFF.md`). Dr. Wang approved moving Qwen and
   Gemma to a Morgan computer (2026-10-08). The home projection for them was about 5 to 7 days each
   (`local/STAGE2_PROJECTION.md`). gpt-oss-20b stayed at home.
8. **Forced-item rerun policy fixed as "Policy B"** (`local/stage2/FORCED_RERUN_POLICY.json`, 2026-10-05). Rerun
   a random sample of up to 20 forced items per model, as sensitivity only, instead of rerunning all of them.
9. **Lab-server port fix** (`local/stage2/STAGE2_DEVIATIONS.md`, 2026-10-14). On Linux, the port check needed
   `SO_REUSEADDR`, because a just-closed port blocked the server from starting twice. No effect on prompts,
   models, settings or scoring. Applied before the freeze.
10. **Lab-server build** (same file). llama.cpp was built from source on Linux with gcc-13 and CUDA 12.4, and
    Python 3.13.16 was installed with uv, instead of the Windows binaries and Python 3.13.7 used at home. Same
    llama.cpp commit.
11. **Lab-server GPU index** (same file). The run used GPU index 1 (`CUDA_VISIBLE_DEVICES=1`); the handoff assumed 0.
12. **Different placement on each machine** (by design). The rule was re-measured on the server: Qwen and Gemma
    fit entirely in the 24 GB GPU there, whereas at home most of their weights ran from system RAM.

Stage 2B changes (Stage 2B `DECISIONS.md`, `DEVIATIONS.md`, `RUN_PLAN.md`):

13. **Only Tier 1 was run.** The pilot projected about 133 hours (about 5.5 days) for the full set, against a
    66-hour target. Tier 1 (503 items) was kept whole and the other benchmarks were held back (section 10).
14. **LongBench v2 skipped.** No item fits the Stage 2 context size (the shortest is about 9,900 tokens; the room
    for a prompt is 4,992 tokens), and the context size was not changed.
15. **Code tests ran in a locked-down sandbox instead of Docker.** Docker needed admin rights on the server, so code
    ran in a bubblewrap sandbox: no network, read-only system, empty environment, 2 GB memory limit and the
    official time limits.
16. **Judge re-run.** gpt-oss-20b was not on the server at first, so Qwen3.8-27B judged SimpleQA Verified and
    Humanity's Last Exam short answers. gpt-oss-20b was then downloaded (hash checked) and re-judged all 257 judged
    answers. The two judges agreed on all 257 and no score changed (section 7B.6).
17. **Time limits.** Each item had a 40-minute limit and the model server was restarted after 5 minutes with no
    response, as the Stage 2B spec requires (Stage 2 allowed longer). No item hit the 40-minute limit.

---

## 9. How to reproduce

Run commands from the repo root. Full details: `local/REPRODUCIBILITY.md` (Stage 1), `local/stage2/README.md` and
`local/stage2/MORGAN_HANDOFF.md` (Stage 2).

**1. Rebuild the git-ignored data** (benchmark files, item lists, answer keys, scorer code):

```
python manifest/fetch_evaluation_sources.py     # re-download pinned data, checked against evaluation-files-lock.json
python manifest/generate_item_manifests.py      # items + answer keys; must match items/item_manifest_lock.json
python -m venv .venv-scoring                    # then install scoring/requirements-lock.txt
python scoring/setup_vendor.py                  # vendored IFEval + BBEH scorers, checked against vendor-lock.json
python verify_all.py                            # all local checks
```

**2. Set up the harness and models:**

```
python -m venv local/.venv && local/.venv/Scripts/pip install -r local/requirements-local-lock.txt
local/.venv/Scripts/python.exe local/fetch_models.py --all     # downloads and SHA-256-checks the GGUFs in gguf_pins.json
```

Install llama.cpp b11349 / commit `fb4b2737a` (Windows binaries, or a git-clone build on Linux; see
`MORGAN_HANDOFF.md` section 4b).

**3. Stage 1** (refuses to run without `local/STAGE1_APPROVED.json`):

```
local/.venv/Scripts/python.exe local/preflight.py
local/.venv/Scripts/python.exe local/run_local.py stage1 >> local/runs/stage1_v2.log 2>&1
.venv-scoring/Scripts/python.exe local/score_local.py local/runs/stage1-v2    # needs Docker Desktop running
```

**4. Stage 2** (per machine; set `MORGAN_HOST=local-rtx4060` or `morgan-gpu`; refuses without
`local/stage2/STAGE2_APPROVED_<host>.json`):

```
local/.venv/Scripts/python.exe local/stage2/preflight_stage2.py --full-hash
local/.venv/Scripts/python.exe local/stage2/probe_stage2.py <models>     # development items only
local/.venv/Scripts/python.exe local/stage2/freeze_stage2.py
local/.venv/Scripts/python.exe local/stage2/run_stage2.py                # resume with resume_stage2.py
.venv-scoring/Scripts/python.exe local/score_local.py local/runs/stage2-<host>   # scoring at home only
```

**5. Paired analysis:**

```
.venv-scoring/Scripts/python.exe -I local/analysis/paired_analysis.py local/runs/stage2-morgan-gpu/scored.jsonl local/runs/stage2-local-rtx4060/scored.jsonl <new-output.md>
```

The output should match `local/analysis/stage2_paired_analysis.md` (seeds and expected SHA-256 are in that file).
On other hardware, the same weights, seeds and settings reproduce the outputs only up to GPU/CPU floating-point
differences, and the timings will differ.

---

## 10. What's next

### 10.1 The rest of Stage 2B

Six more benchmarks are frozen, piloted and ready to run on the same two models with the same settings. Projected
time: **about 12 hours** (`RUN_PLAN.md`). Finished results are kept, so this only adds new items.

| Skill | Benchmark | Items |
|---|---|---|
| Data analysis | LiveBench data analysis | 30 |
| Language puzzles | LiveBench language | 30 |
| Multi-turn conversation | MultiChallenge | 50 |
| Over-refusal | XSTest | 60 |
| Multilingual | Global-MMLU-Lite | 45 |
| Tool calling | BFCL | 60 |

### 10.2 Comparison with Claude and Gemini

A comparison with **Claude Opus 5.5 and Gemini 4 Argon** on **250 of the same questions** is planned once API
credits are approved. 250 questions is enough to detect a 10-point gap. The code is built and tested with mock
calls only; no API has been called yet.

### 10.3 Grading checks for Stage 2B

- Independent re-judge with gpt-oss-20b: **done**. It agreed with the first judge on all 257 answers and no score
  changed (section 7B.6).
- Human spot-check of 40 judged items: in progress.

### 10.4 Still open from Stage 2

- Policy B forced-item reruns for Qwen3.8-27B and Gemma 4 31B have not been run. `run_forced_rerun.py` currently
  accepts only the gpt-oss selection, so it needs a small reviewed change and approval first
  (`MORGAN_HANDOFF.md` section 8). These reruns cannot change the official scores.

# Project details: choosing an open-weight LLM for the Morgan lab server

Last updated 2026-11-04. Author: Rohan Sainju (rosai2@morgan.edu).

This file holds the full record behind the short [README](../README.md): every table, the step-by-step model
selection, hardware and software details, run times, the full list of changes from the plan, reproduction steps and
the earlier reports. Section numbers are the same as in earlier versions of the README, so older references still
match. Results here are unchanged; the README shows the most important ones.

Every number comes from a file in this repository, from the run logs and results files (`local/runs/`, which git
does not track), or from the Stage 2B, model-panel, Stage 2C and Stage 2D results archives (`REPORT.md` and its notes, kept
outside git). Anything not yet confirmed is listed under [Open questions](#open-questions).

**No benchmark questions, answer keys or model answers appear in this file or anywhere in git.** Answer keys,
benchmark data and rendered prompts are git-ignored (see `.gitignore`).

Fine-tuning is listed as out of scope in `01-study-scope.md`.

## Contents

- [2. Status at a glance (full table)](#2-status-at-a-glance)
- [3. Earlier reports and how they fit together](#3-earlier-reports-and-how-they-fit-together)
- [4. How we chose the models (35 to 7 to 3)](#4-how-we-chose-the-models-35-to-7-to-3)
- [5. System setup](#5-system-setup)
- [6. Run time: home computer vs lab server](#6-run-time-home-computer-vs-lab-server)
- [7. Benchmarks and results (Stage 1 and Stage 2)](#7-benchmarks-and-results)
- [7B. Stage 2B results (expanded benchmarks)](#7b-stage-2b-results-expanded-benchmarks)
- [7C. Model panel and closed-model comparison (250 questions)](#7c-model-panel-and-closed-model-comparison-250-questions)
- [7D. Stage 2C: Ornith on the Stage 2 items, and licenses](#7d-stage-2c-ornith-on-the-stage-2-items-and-licenses)
- [7E. Stage 2D: local Wikipedia search (250 questions)](#7e-stage-2d-local-wikipedia-search-250-questions)
- [8. Changes from the original plan (full list)](#8-changes-from-the-original-plan)
- [9. How to reproduce](#9-how-to-reproduce)
- [10. What's next (full)](#10-whats-next)
- [Open questions](#open-questions)

---

## 2. Status at a glance

Times from the logs are in UTC.

| Stage | Dates | What was done | Main result | Status |
|---|---|---|---|---|
| Model selection | 2026-09-29 to 2026-10-02 | Built a 35-model candidate list, narrowed it to a 6-model hosted-API plan, then switched to 7 models that run locally | 7 models chosen for local testing | Done |
| Stage 1 (home computer) | Calibration 2026-10-02; probes 2026-10-03; official run 2026-10-04 (04:54 to 15:32); finalists recorded 2026-10-05 | 7 models x 22 items, 6,144 thinking tokens + 1,536 answer tokens | Qwen3.8-27B and Gemma 4 31B 21/22, gpt-oss-20b 20/22; these 3 went to Stage 2 | Done |
| Stage 2 (home + lab server) | gpt-oss-20b at home 2026-10-05 to 10-06; Qwen3.8-27B and Gemma 4 31B on the lab server 2026-10-15 to 10-17; analysis 2026-10-19 | 3 models x 284 new items, 16,384 thinking tokens + 2,048 answer tokens | Qwen 235/284 (82.7%), Gemma 233/284 (82.0%), gpt-oss 198/284 (69.7%). Qwen and Gemma are not significantly different; both beat gpt-oss | Done (forced-item reruns for Qwen and Gemma not yet run, see section 10) |
| Stage 2B (expanded benchmarks) | Set-up and pilot 2026-10-23; run started 2026-10-24; generation finished and scored 2026-10-28 | Qwen3.8-27B and Gemma 4 31B x 503 new items from 6 benchmarks (Tier 1), on the lab server, same settings as Stage 2 | Qwen 65.6%, Gemma 62.4%. Qwen is slightly ahead but not significantly (p = 0.068). Tied on GPQA; Qwen leads on coding and reasoning (section 7B) | Done; re-graded 2026-10-28 by an independent judge, no score changed (6 more benchmarks ready to run, see section 10) |
| Model panel (open models) | 2026-10-29 to 2026-11-01 | 4 more open models (Ornith-1.5-35B-A3B, K2-Horizon-MoVA-36B-A4B, Nanbeige4.3-33B, gpt-oss-20b) x 250 Stage 2B questions, on the lab server, same settings; compared with Qwen and Gemma on the same questions | Qwen still the best open model (65.6%). Ornith (64.0%) and Gemma (62.4%) are not significantly different from Qwen; Ornith is about 7 times faster (section 7C). On the Stage 2 items Ornith is significantly worse than Qwen (Stage 2C, section 7D) | Done |
| Closed-model comparison | 2026-11-01 | Claude Opus 5.5 and Gemini 4 Argon through their APIs on the same 250 questions and prompts | Closed models lead by about 18 to 21 points (excluding CRUXEval), mostly on factual knowledge (section 7C) | Done |
| Stage 2C: Ornith on Stage 2 items and license check | 2026-11-02 (generation 13:57 to 16:23) | Ornith-1.5-35B-A3B on the 284 Stage 2 items with the frozen Stage 2 settings; license check of the 5 models we might deploy | Ornith 194/266 = 72.9% vs Qwen 218/266 = 82.0% on the 266 items scored so far: significantly worse (-9.0 points, Holm p 0.00116). All 5 licenses allow free student use (section 7D) | Done; 18 student items pending laptop scoring (cannot reverse the result) |
| Stage 2D: local Wikipedia search | Set-up 2026-11-02; main run started 2026-11-02 23:15; report 2026-11-04 06:57 | Qwen3.8-27B and Ornith-1.5-35B-A3B with an offline Wikipedia search (BM25), same 250 panel questions and settings | Qwen 65.6% -> 72.4% (significant), Ornith 64.0% -> 68.0% (not significant); closes 29% of the gap to the closed models on average (section 7E) | Done |
| Stage 2E: improved search | | Better search for the same two models | | Running |

---

## 3. Earlier reports and how they fit together

These are the report-style documents in the repo, oldest first.

| Date | File | What it covered | Still current? |
|---|---|---|---|
| 2026-09-29 | `00-professor-brief.md` | First proposal: a 3-model explanatory study (Granite 4.2 8B, Qwen3.5 9B, Phi-4 Reasoning) | **Fully replaced** (the file itself says it is superseded) |
| 2026-09-29 | `14-capability-first-shortlist.md`, `18-final-candidate-and-execution-audit.md`, `19-readiness-and-calibration-plan.md` | Narrowing the candidate pool to 6 very large models to be run through paid hosted APIs | **Fully replaced** for what we ran. Before the plan was dropped, a small API connectivity test was run (38 short requests, about $0.01 in total); no benchmark or calibration was ever run through the APIs. Still the record of how the candidate pool was built |
| 2026-09-29 to 2026-10-03 | Old `README.md` (now replaced by this file; the old text is in git history) | Index of the API-era documents, with a banner pointing to the local plan | **Fully replaced** |
| 2026-10-02 | `local/REVISED_PROPOSAL_2026-10-02.md` | Why long reasoning budgets were impractical on the home computer; new placement rule, forced 6,144-token budget, smaller Stage 1 panel | **Partly replaced**: the Stage 1 parts were approved and used; its Stage 2 section (section 7) was replaced by the actual Stage 2 plan |
| 2026-10-02 to 10-03 | `22-local-evaluation-plan.md` | Local plan for 7 models and the probe speed results | **Partly replaced**: still correct for Stage 1; says nothing about Stage 2 |
| 2026-10-05 | `local/STAGE2_FINALISTS.md` | Stage 1 results and the rule that picked the 3 finalists | **Current** |
| 2026-10-05 | `local/STAGE2_PROJECTION.md` | Projected Stage 2 run times on the home computer | **Partly replaced**: Qwen and Gemma were actually run on the lab server (section 6) |
| 2026-10-06 | `local/stage2/sensitivity/forced_rerun_comparison_local-rtx4060_gpt-oss-20b.md` | gpt-oss-20b forced-item rerun at 24,576 tokens | **Current** |
| 2026-10-08 | `local/stage2/MORGAN_HANDOFF.md` | Operator guide for running Qwen and Gemma on the lab server | **Partly replaced**: the hardware it calls "not yet confirmed" is now known (section 5), and the run used GPU index 1, not 0 |
| 2026-10-19 | `local/analysis/stage2_paired_analysis.md` | Stage 2 scores, McNemar tests and bootstrap confidence intervals | **Current** |

**The project README now replaces all of the reports above.** The files are kept as the detailed record.

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

Why the project moved from hosted APIs to local runs: after we calculated the cost, running the models through APIs came out too high and was not worth it. The later closed-model comparison (section 7C) used APIs only for 2 models on 250 questions, which cost about $17.

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

### 5.2 Lab server (Stage 2, Stage 2B and the model panel)

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
| Docker grader image | `python@sha256:0741d101873c12ab927e6f8653feb8862b9bd58771177acb1b885b95141f91b4` (python:3.14-slim), Docker Engine 28.5.1. Used only to grade the student programming items, only at home | Stage 2 was scored at home. Stage 2B and the model panel were scored on the server in a bubblewrap sandbox, because Docker needs admin rights there. |

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
- A **human spot-check of 40 judged items** (20 SimpleQA, 20 Humanity's Last Exam, both models) is planned.

---

## 7C. Model panel and closed-model comparison (250 questions)

Source: the panel `REPORT.md` (built 2026-11-01 06:29 UTC), with `MODEL_SETTINGS.md`, `DECISIONS.md`,
`DEVIATIONS.md` and `HANDOFF.md` from the same run. Scores only; no questions or answers are published.

### 7C.1 Why we ran it

Dr. Wang asked two questions:

1. Is Qwen3.8-27B really the strongest open model for our 24 GB GPU?
2. How far are the best open models from the top closed models?

### 7C.2 How the new models were chosen

We checked independent rankings (the Artificial Analysis leaderboard of small open-weights models) and recent
releases in October 2026, and added the newest models that fit a 24 GB GPU:

| Model | Size (total / active) | License | Notes |
|---|---|---|---|
| Ornith-1.5-35B-A3B | 35B / 3B | MIT | Official 4-bit file; fits fully on the GPU |
| K2-Horizon-MoVA-36B-A4B | 36B / 4B | Apache-2.0 | Official 4-bit file; about 1.1 GB of it had to sit in CPU memory; needed a newer llama.cpp (section 8) |
| Nanbeige4.3-33B | 33B | Apache-2.0 | 4-bit file from bartowski (no official one); fits fully on the GPU |
| gpt-oss-20b | 21B / 3.6B | Apache-2.0 | Reference model from Stage 2 |

**Pool update:** Ornith, K2-Horizon and Nanbeige were released after the original 35-model pool was built
(section 4), so they are not in that list. This is an addition to the pool, not a change to the earlier steps.

### 7C.3 Setup

- **Questions:** 250 of the 503 frozen Stage 2B questions, picked at random with a fixed seed and balanced by
  category: GPQA Diamond 98, LiveCodeBench 30, SimpleQA Verified 40, Humanity's Last Exam 40, MuSR 22,
  CRUXEval 20.
- **Open models:** same lab-server GPU (RTX 4500 Ada) and the same frozen settings as Stage 2 and 2B (16,384
  thinking + 2,048 answer tokens). Each model used its own official chat template and recommended sampling. Qwen
  and Gemma were not re-run: their Stage 2B answers to these 250 questions were reused.
- **Closed models:** Claude Opus 5.5 and Gemini 4 Argon through their APIs, with the same prompts and the same
  18,560-token total limit (thinking + answer), thinking effort "high". Gemini has 249 scored items (one API call
  failed).

### 7C.4 Leaderboard

Accuracy = percent fully correct. Brackets are 95% confidence intervals. "Excl. CRUXEval" leaves out the 20
CRUXEval questions for **every** model (230 questions), because Anthropic's safety filter blocked all of Claude's
CRUXEval prompts. That column is the fairer comparison with Claude.

| Rank | Model | All 250 | Excl. CRUXEval (230) |
|---|---|---|---|
| 1 | Gemini 4 Argon (API) | **82.7%** [77.5, 86.9] | 81.3% [75.8, 85.8] |
| 2 | Claude Opus 5.5 (API) | **77.2%** [71.6, 82.0] | 83.9% [78.6, 88.1] |
| 3 | **Qwen3.8-27B** | **65.6%** [59.5, 71.2] | 63.0% [56.6, 69.0] |
| 4 | Ornith-1.5-35B-A3B | **64.0%** [57.9, 69.7] | 62.6% [56.2, 68.6] |
| 5 | Gemma 4 31B | **62.4%** [56.3, 68.2] | 60.0% [53.6, 66.1] |
| 6 | Nanbeige4.3-33B | **59.2%** [53.0, 65.1] | 56.5% [50.1, 62.8] |
| 7 | K2-Horizon-MoVA-36B-A4B | **56.4%** [50.2, 62.4] | 53.9% [47.5, 60.2] |
| 8 | gpt-oss-20b | **42.4%** [36.4, 48.6] | 37.8% [31.8, 44.2] |

Per benchmark (accuracy %; number of questions in the header):

| Model | GPQA (98) | LiveCodeBench (30) | SimpleQA (40) | HLE (40) | MuSR (22) | CRUXEval (20) |
|---|---|---|---|---|---|---|
| Gemini 4 Argon (API) | 95.9 | 86.7 | 75.0 | 37.5 | 100.0 | 100.0 (19 items) |
| Claude Opus 5.5 (API) | 90.8 | 96.7 | 75.0 | 60.0 | 95.5 | 0.0 (all blocked) |
| Qwen3.8-27B | 87.8 | 83.3 | 12.5 | 22.5 | 90.9 | 95.0 |
| Ornith-1.5-35B-A3B | 86.7 | 63.3 | 17.5 | 30.0 | 95.5 | 80.0 |
| Gemma 4 31B | 86.7 | 80.0 | 10.0 | 20.0 | 77.3 | 90.0 |
| Nanbeige4.3-33B | 82.7 | 80.0 | 5.0 | 7.5 | 90.9 | 90.0 |
| K2-Horizon-MoVA-36B-A4B | 79.6 | 63.3 | 2.5 | 17.5 | 86.4 | 85.0 |
| gpt-oss-20b | 45.9 | 50.0 | 5.0 | 10.0 | 95.5 | 95.0 |

### 7C.5 Open models vs Qwen

Same 250 questions for every model. Paired test (McNemar), corrected for making 5 comparisons (Holm).

| Model | Difference from Qwen (points) | 95% CI | Corrected p | Significant? |
|---|---|---|---|---|
| Ornith-1.5-35B-A3B | -1.6 | [-6.0, +2.8] | 0.60 | No |
| Gemma 4 31B | -3.2 | [-7.6, +1.2] | 0.46 | No |
| Nanbeige4.3-33B | -6.4 | [-11.2, -1.6] | 0.042 | **Yes, worse** |
| K2-Horizon-MoVA-36B-A4B | -9.2 | [-14.0, -4.8] | 0.0008 | **Yes, worse** |
| gpt-oss-20b | -23.2 | [-29.6, -17.2] | < 0.0001 | **Yes, worse** |

In plain words:

- **Qwen3.8-27B is still the best open model that fits our GPU**, but not by much.
- **Ornith and Gemma are statistically tied with Qwen on these 250 questions.** Ornith is weaker on coding
  (LiveCodeBench 63.3% vs 83.3%), but that is only 30 questions and was not tested on its own. **Update (Stage 2C):**
  on the Stage 2 items Ornith is significantly worse than Qwen (72.9% vs 82.0% on 266 scored items, Holm p 0.00116;
  section 7D), so it is not tied with Qwen overall.
- **Nanbeige, K2-Horizon and gpt-oss-20b are clearly worse than Qwen.**

### 7C.6 Gap to the closed models

Our two best open models against the two closed models, on the same questions. Gap = closed minus open
(points). All four overall gaps below are significant after correction.

| Open model | Closed model | Gap, all 250 [95% CI] | Gap, excl. CRUXEval [95% CI] |
|---|---|---|---|
| Qwen3.8-27B | Claude Opus 5.5 | +11.6 [+4.8, +18.4] | **+20.9** [+15.2, +27.0] |
| Qwen3.8-27B | Gemini 4 Argon | +17.3 [+12.0, +22.9] | **+18.3** [+12.6, +23.9] |
| Ornith-1.5-35B-A3B | Claude Opus 5.5 | +13.2 [+6.4, +20.0] | **+21.3** [+15.2, +27.4] |
| Ornith-1.5-35B-A3B | Gemini 4 Argon | +18.5 [+12.9, +24.1] | **+18.7** [+12.6, +24.8] |

Gap by benchmark for Qwen (points; "yes" = significant after correcting for 24 comparisons):

| Benchmark | vs Claude | vs Gemini |
|---|---|---|
| GPQA Diamond (science) | +3.1 (no) | +8.2 (no) |
| LiveCodeBench (coding) | +13.3 (no) | +3.3 (no) |
| SimpleQA Verified (facts) | **+62.5 (yes)** | **+62.5 (yes)** |
| Humanity's Last Exam (expert questions) | **+37.5 (yes)** | +15.0 (no) |
| MuSR (multi-step reasoning) | +4.5 (no) | +9.1 (no) |
| CRUXEval (code reasoning) | Claude blocked | +5.3 (no) |

**Main finding:**

- **The closed models are about 18 to 21 points ahead overall** (excluding CRUXEval; 12 to 18 points counting
  all 250 questions). This gap is real.
- **Most of the gap is factual knowledge.** On SimpleQA (short facts) the closed models are about **60 points**
  ahead. Small open models simply store fewer facts.
- **On science, coding and multi-step reasoning, Qwen is close** (3 to 13 points behind) **and none of these
  differences is significant.** The other significant gap is Claude on Humanity's Last Exam (+37.5).
- This suggests that giving the open models a way to look facts up could close much of the gap (section 10).

### 7C.7 Speed and efficiency

Same GPU and token limits. Qwen and Gemma times come from their Stage 2B run.

| Model | Score (all 250) | Mean time per question | Total time (250) | Speed vs Qwen | Decode speed | Peak GPU memory |
|---|---|---|---|---|---|---|
| Qwen3.8-27B | 65.6% | 419 s | 29.1 h | 1.0x | 21 tok/s | 17,126 MiB |
| **Ornith-1.5-35B-A3B** | **64.0%** | **59 s** | **4.1 h** | **7.1x faster** | 117 tok/s | 20,632 MiB |
| Gemma 4 31B | 62.4% | 289 s | 20.1 h | 1.4x faster | 18 tok/s | 20,858 MiB |
| Nanbeige4.3-33B | 59.2% | 438 s | 30.4 h | about the same | 18 tok/s | 22,186 MiB |
| K2-Horizon-MoVA-36B-A4B | 56.4% | 129 s | 8.9 h | 3.3x faster | 53 tok/s | 23,128 MiB |
| gpt-oss-20b | 42.4% | 104 s | 7.2 h | 4.0x faster | 99 tok/s | 11,630 MiB |

**Ornith is statistically tied with Qwen on these 250 questions but about 7 times faster** (59 s vs 419 s per
question). On the Stage 2 items it is significantly worse than Qwen (section 7D). It only uses
about 3B parameters per token, which is why it is so fast. For many students sharing one GPU, that matters a lot.
K2-Horizon's speed is not fully comparable, because part of it ran from CPU memory.

### 7C.8 Caveats

- **Claude's blocked questions.** Anthropic's safety filter refused all 20 of Claude's CRUXEval prompts and 3
  GPQA prompts. They count as wrong in the all-250 score. The CRUXEval prompt format (a worked example ending in an
  open "thought" tag) triggers the filter. Same prompts as every other model; no fallback model was used.
- **Closed models can't be force-stopped.** Open models are told to stop thinking at 16,384 tokens and answer. The
  APIs can't do that, so a closed model that thinks too long gets no answer (counted wrong). Gemini ran out on
  **13 of 40** Humanity's Last Exam questions, Claude on 1 of 40. This can only lower their scores.
- **Possible training-data contamination.** All six benchmarks are public, and the closed models may have seen some
  of these questions in training. We cannot check this. It could raise their scores.
- **Small samples per benchmark.** Per-benchmark results rest on 20 to 98 questions and are noisy. The overall
  paired tests are the main evidence.
- **Forced answers.** If every answer given after hitting the thinking limit is counted wrong, the order changes
  (for example Qwen drops to 50.0% and Gemma stays at 62.4%). Gemma rarely hits the limit; Qwen did on 81 of 250.

### 7C.9 Grading

SimpleQA and the Humanity's Last Exam short answers need a model to grade them. **Two independent judges
(gpt-oss-20b and Qwen3.8-27B) graded all 503 such answers and agreed on 98.4%** (Cohen's kappa 0.96). gpt-oss-20b
was the main judge; Qwen judged gpt-oss-20b's own answers, so no model was graded only by itself. Most
disagreements were on the closed models' answers (Claude 95.4% agreement, Gemini 94.6%).

### 7C.10 Cost

The full API run cost **$16.08** (Claude $6.58, Gemini $9.50), plus **$1.30** for the pilot.

---

## 7D. Stage 2C: Ornith on the Stage 2 items, and licenses

Copied from the Stage 2C results archive (`REPORT.md`, 2026-11-02). Benchmark names are the internal ids (bbeh_mini = BBEH, ifeval = IFEval, math500 = MATH-500, mmlu_pro = MMLU-Pro). The plain-language conclusion is in the README (section 5.2).

Ornith-1.5-35B-A3B was run on all 284 frozen Stage 2 items on the Morgan RTX 4500 Ada (GPU 1) with the frozen Stage 2 shared settings (same prompts, 16,384 thinking + 2,048 answer tokens, n_ctx 23,552, server forced conclusion, loop early-stop, per-item seeds) and Ornith's own panel settings (official Q4_K_M GGUF, official template, enable_thinking, T 1.0 / top_p 0.95 / top_k 20). Details: DECISIONS.md.

**Scoring status: 266 of 284 items scored on this server; 18 student items are pending laptop scoring** (the student grader and Docker sandbox exist only on the laptop; see LAPTOP_SCORING.md). The server scorer is the laptop's score_local.py/scorers.py unchanged and reproduces the laptop's Qwen, Gemma and gpt-oss Stage 2 scores on all 798 non-student rows (0 disagreements), so the four non-student benchmark scores below are final; the overall Stage 2 figure is on 266 items until the laptop step is done.


### 7D.1 Stage 2 scores per benchmark (primary: truncated = wrong)

| Model | bbeh_mini | ifeval | math500 | mmlu_pro | student | Overall (266 items, identical for all) | Stage 2 official overall (284) |
|---|---|---|---|---|---|---|---|
| Ornith-1.5-35B-A3B | 29/67 = 43.3% | 64/80 = 80.0% | 55/58 = 94.8% | 46/61 = 75.4% | pending laptop scoring | 194/266 = 72.9% | pending laptop scoring |
| Qwen3.8-27B | 42/67 = 62.7% | 74/80 = 92.5% | 56/58 = 96.6% | 46/61 = 75.4% | 17/18 = 94.4% | 218/266 = 82.0% | 235/284 = 82.7% |
| Gemma 4 31B | 38/67 = 56.7% | 75/80 = 93.8% | 56/58 = 96.6% | 49/61 = 80.3% | 15/18 = 83.3% | 218/266 = 82.0% | 233/284 = 82.0% |
| gpt-oss-20b | 22/67 = 32.8% | 68/80 = 85.0% | 51/58 = 87.9% | 41/61 = 67.2% | 16/18 = 88.9% | 182/266 = 68.4% | 198/284 = 69.7% |

Status counts (all 284 items): Ornith-1.5-35B-A3B BUDGET_TRUNCATED 8, CORRECT 194, INCORRECT 64, PENDING_LAPTOP 18; Qwen3.8-27B BUDGET_TRUNCATED 6, CORRECT 235, INCORRECT 43; Gemma 4 31B BUDGET_TRUNCATED 12, CORRECT 233, INCORRECT 39; gpt-oss-20b BUDGET_TRUNCATED 8, CORRECT 198, EXTRACTION_FAILURE 8, INCORRECT 70

### 7D.2 Paired tests on the Stage 2 items (Ornith vs each Stage 2 finalist)

Exact McNemar (two-sided), paired bootstrap 95% CI (10,000 resamples), Holm across the 3 overall comparisons; per-benchmark rows Holm-corrected across all of them. Full tables incl. truncated-excluded sensitivity: analysis/paired_analysis_*.md.

| Ornith vs | n | Ornith acc | other acc | diff (pp) | 95% CI | Ornith-only / other-only right | McNemar p | Holm p | significant |
|---|---|---|---|---|---|---|---|---|---|
| Qwen3.8-27B | 266 | 72.9 | 82.0 | -9.0 | [-13.9, -4.5] | 10 / 34 | 0.000388 | 0.00116 | **yes** |
| Gemma 4 31B | 266 | 72.9 | 82.0 | -9.0 | [-13.9, -4.1] | 11 / 35 | 0.000536 | 0.00116 | **yes** |
| gpt-oss-20b | 266 | 72.9 | 68.4 | +4.5 | [-0.8, +9.8] | 31 / 19 | 0.119 | 0.119 | no |

| Ornith vs | benchmark | n | diff (pp) | 95% CI | Ornith-only / other-only | McNemar p | Holm p |
|---|---|---|---|---|---|---|---|
| Qwen3.8-27B | bbeh_mini | 67 | -19.4 | [-31.3, -7.5] | 4 / 17 | 0.0072 | 0.0864 |
| Qwen3.8-27B | ifeval | 80 | -12.5 | [-22.5, -3.8] | 3 / 13 | 0.0213 | 0.213 |
| Qwen3.8-27B | math500 | 58 | -1.7 | [-5.2, +0.0] | 0 / 1 | 1 | 1 |
| Qwen3.8-27B | mmlu_pro | 61 | +0.0 | [-8.2, +8.2] | 3 / 3 | 1 | 1 |
| Gemma 4 31B | bbeh_mini | 67 | -13.4 | [-26.9, +0.0] | 7 / 16 | 0.0931 | 0.838 |
| Gemma 4 31B | ifeval | 80 | -13.8 | [-22.5, -5.0] | 2 / 13 | 0.00739 | 0.0864 |
| Gemma 4 31B | math500 | 58 | -1.7 | [-5.2, +0.0] | 0 / 1 | 1 | 1 |
| Gemma 4 31B | mmlu_pro | 61 | -4.9 | [-13.1, +3.3] | 2 / 5 | 0.453 | 1 |
| gpt-oss-20b | bbeh_mini | 67 | +10.4 | [-1.5, +22.4] | 13 / 6 | 0.167 | 1 |
| gpt-oss-20b | ifeval | 80 | -5.0 | [-15.0, +5.0] | 6 / 10 | 0.454 | 1 |
| gpt-oss-20b | math500 | 58 | +6.9 | [+0.0, +15.5] | 5 / 1 | 0.219 | 1 |
| gpt-oss-20b | mmlu_pro | 61 | +8.2 | [+0.0, +18.0] | 7 / 2 | 0.18 | 1 |

Sensitivity (items truncated by either model excluded): vs Qwen3.8-27B -9.4 pp (n 256, Holm p 0.000364); vs Gemma 4 31B -9.9 pp (n 252, Holm p 0.000337); vs gpt-oss-20b +3.2 pp (n 252, Holm p 0.302).

### 7D.3 Qwen3.8-27B vs Ornith-1.5-35B-A3B on everything both have run

Same GPU (RTX 4500 Ada 24 GB), same llama.cpp build b11349, same Q4_K_M quantization and Stage 2 budgets. diff = Ornith − Qwen (pp). Exact McNemar; paired bootstrap 95% CI (10,000 resamples, seeds 20261202+k); Holm across the benchmark rows (both stages together) and separately across the two overall rows. Time = mean wall seconds per item.

| stage | benchmark | n | Qwen acc | Ornith acc | diff (pp) | 95% CI | Ornith-only / Qwen-only | McNemar p | Holm p | significant | Qwen s/item | Ornith s/item | speed-up |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Stage 2 | bbeh_mini | 67 | 62.7 | 43.3 | -19.4 | [-31.3, -7.5] | 4 / 17 | 0.0072 | 0.072 | no | 496 | 86 | 5.8× |
| Stage 2 | ifeval | 80 | 92.5 | 80.0 | -12.5 | [-22.5, -3.8] | 3 / 13 | 0.0213 | 0.191 | no | 100 | 8 | 12.2× |
| Stage 2 | math500 | 58 | 96.6 | 94.8 | -1.7 | [-5.2, +0.0] | 0 / 1 | 1 | 1 | no | 95 | 12 | 7.8× |
| Stage 2 | mmlu_pro | 61 | 75.4 | 75.4 | +0.0 | [-8.2, +8.2] | 3 / 3 | 1 | 1 | no | 189 | 25 | 7.6× |
| Panel | gpqa_diamond | 98 | 87.8 | 86.7 | -1.0 | [-7.1, +5.1] | 4 / 5 | 1 | 1 | no | 422 | 58 | 7.2× |
| Panel | livecodebench | 30 | 83.3 | 63.3 | -20.0 | [-36.7, -3.3] | 1 / 7 | 0.0703 | 0.562 | no | 551 | 105 | 5.2× |
| Panel | simpleqa_verified | 40 | 12.5 | 17.5 | +5.0 | [-5.0, +15.0] | 3 / 1 | 0.625 | 1 | no | 314 | 4 | 71.4× |
| Panel | hle_text | 40 | 22.5 | 30.0 | +7.5 | [-5.0, +20.0] | 5 / 2 | 0.453 | 1 | no | 684 | 109 | 6.3× |
| Panel | musr | 22 | 90.9 | 95.5 | +4.5 | [+0.0, +13.6] | 1 / 0 | 1 | 1 | no | 248 | 48 | 5.2× |
| Panel | cruxeval_o | 20 | 95.0 | 80.0 | -15.0 | [-30.0, +0.0] | 0 / 3 | 0.25 | 1 | no | 69 | 13 | 5.3× |
| Stage 2 | overall (266 items) | 266 | 82.0 | 72.9 | -9.0 | [-13.9, -4.5] | 10 / 34 | 0.000388 | 0.000776 | **yes** | 206 | 31 | 6.7× |
| Panel | overall (250 items) | 250 | 65.6 | 64.0 | -1.6 | [-6.0, +2.8] | 14 / 18 | 0.597 | 0.597 | no | 419 | 59 | 7.1× |
| Stage 2 | student | 18 | 94.4 | pending laptop scoring | | | | | | | 13 | 4 | |

Speed and memory (whole run, same GPU):

| | Qwen3.8-27B (Stage 2) | Ornith (Stage 2C) | Qwen3.8-27B (panel) | Ornith (panel) |
|---|---|---|---|---|
| mean / median s per item | 206 / 71 | 31 / 8 | 419 / 409 | 59 / 27 |
| total generation hours | 16.3 (284 items) | 2.4 (284 items) | 29.1 (250) | 4.1 (250) |
| median decode tok/s | 21.7 | 117.3 | 21.4 | 117.0 |
| mean thinking tokens | 4189 | 3021 | 8605 | 6163 |
| thinking limit hit (forced) | 31 | 32 | 81 | 57 |
| peak GPU memory (MiB, 24,570 total) | 17126 | 20616 | 17126 | 20632 |
| parameters total / active | 27B / 27B (dense) | 35B / 3B (MoE) | | |

For reference, Stage 2 Gemma 4 31B: 199 s/item, 18.1 tok/s, peak 20858 MiB (same GPU). gpt-oss-20b's Stage 2 ran on the laptop RTX 4060 8 GB (158 s/item) and is not speed-comparable.

### 7D.4 Licenses (official Hugging Face model cards, read 2026-11-02 at the pinned revisions)

| Model | License | URL | Free to serve to students at a university? | Restrictions / flags |
|---|---|---|---|---|
| Qwen3.8-27B | Apache 2.0 (LICENSE file in repo) | https://huggingface.co/Qwen/Qwen3.8-27B | **Yes** | Keep the license and copyright notices when redistributing the weights; mark changed files; no trademark rights. No user caps, no acceptable-use policy. |
| Ornith-1.5-35B-A3B | MIT (card metadata) | https://huggingface.co/ornith-ai/Ornith-1.5-35B-A3B | **Yes, on the stated terms** | Keep the copyright + license notice when redistributing. **Flag:** the card's `license_link` (…/blob/main/LICENSE) returns HTTP 404, so the repo holds no license text. The card says it is built on Qwen3.5 and Gemma 4 (both Apache 2.0, compatible with MIT), but nobody has published the exact copyright line. Ask ornith-ai to add the LICENSE file, or record the card at the pinned revision (done: licenses/). No user caps or acceptable-use policy. |
| Gemma 4 31B (it) | Apache 2.0 | https://huggingface.co/google/gemma-4-31B-it (license page https://ai.google.dev/gemma/docs/gemma_4_license) | **Yes** | Plain Apache 2.0 text: notices + mark changes, no trademark rights. Unlike Gemma 1–3, the Gemma 4 terms carry no Gemma Prohibited Use Policy and no flow-down of use restrictions. The card encourages (does not require) content-safety safeguards. |
| Nanbeige4.3-33B | Apache 2.0 (card metadata; no LICENSE file in repo) | https://huggingface.co/Nanbeige/Nanbeige4.3-33B | **Yes** | Apache 2.0 notices. Minor flag: there is no license text file in the repo, only the metadata tag. |
| K2-Horizon-MoVA-36B-A4B | Apache 2.0 (card metadata; no LICENSE file in repo) | https://huggingface.co/IFM/K2-Horizon-MoVA-36B-A4B | **Yes** | Apache 2.0 notices. Same minor flag as Nanbeige. |

None of the five licenses limits the number of users, requires a commercial agreement above a user threshold, or imposes an acceptable-use policy. Serving the model behind a web app is not "redistribution", so the notice duties apply only if the weights themselves are handed out. A university still needs its own usage policy, student-data/privacy review and content safeguards, but no license blocks free student use. Card copies and SHA-256: licenses/SOURCES.txt. (Not legal advice; the university's counsel should confirm.)

---

## 7E. Stage 2D: local Wikipedia search (250 questions)

Copied from the Stage 2D results archive (`REPORT.md`, generated 2026-11-04). "Retrieval" = the local Wikipedia search. The plain-language summary is in the README (section 5.1).

Generated 2026-11-04T06:57:32+00:00. Items: the 250-question panel subset (`subset_250.json`): gpqa_diamond 98, livecodebench 30, simpleqa_verified 40, hle_text 40, musr 22, cruxeval_o 20.

**Set-up.** Qwen3.8-27B and Ornith-1.5-35B-A3B were rerun on the same 250 questions with exactly the panel settings (same GGUF files, llama.cpp b11349, official chat templates, sampling, seeds, thinking budget 16,384 + 2,048, n_ctx 23,552, one GPU), except that each prompt starts with passages retrieved from an offline English Wikipedia index (wikimedia/wikipedia 20231101.en, snapshot 1 Nov 2023; 18,940,032 passages of ≤200 words). Retrieval: BM25 (Pyserini/Lucene, k1 0.9, b 0.4) top-10 passages in rank order, keeping each passage only if the block's passage characters (title + text) stay within 3,000 (a passage that would overflow is skipped); no reranker (frozen in RETRIEVAL_CONFIG.json, SHA-256 `f1a873b08d27232b…`, chosen on 100 separate SimpleQA questions). The query is the question text; nothing about the test questions was used to tune retrieval. Scoring: the panel scorers; SimpleQA and HLE short answers judged by gpt-oss-20b (primary) and Qwen3.8-27B (second), judges see the original question without passages. "Without retrieval" numbers are the panel's (Qwen: its Stage 2B answers, as in the panel). Claude Opus 5.5 and Gemini 4 Argon ran without retrieval.

### 7E.1 With vs without retrieval (same model, same 250 questions)

diff = with − without (percentage points). Paired bootstrap 95% CI (10,000 resamples, seed 2026); exact McNemar on discordant items (b = right only with retrieval, c = right only without). Holm correction within each table (4 overall tests; 12 per-benchmark tests).

| model | items | without | with | diff (pp) | 95% CI | b / c | exact p | Holm p | significant |
|---|---|---|---|---|---|---|---|---|---|
| Qwen3.8-27B | all 250 (n 250) | 65.6 | 72.4 | +6.8 | [+2.0, +11.6] | 28 / 11 | 0.0095 | 0.0379 | **yes** |
| Qwen3.8-27B | excl. CRUXEval (230) (n 230) | 63.0 | 70.4 | +7.4 | [+2.2, +12.6] | 28 / 11 | 0.0095 | 0.0379 | **yes** |
| Ornith-1.5-35B-A3B | all 250 (n 250) | 64.0 | 68.0 | +4.0 | [-1.2, +9.2] | 26 / 16 | 0.1641 | 0.3283 | no |
| Ornith-1.5-35B-A3B | excl. CRUXEval (230) (n 230) | 62.6 | 66.5 | +3.9 | [-1.7, +9.6] | 25 / 16 | 0.2110 | 0.3283 | no |

Per benchmark:

| model | benchmark | n | without | with | diff (pp) | 95% CI | b / c | Holm p | significant |
|---|---|---|---|---|---|---|---|---|---|
| Qwen3.8-27B | gpqa_diamond | 98 | 87.8 | 93.9 | +6.1 | [+2.0, +11.2] | 6 / 0 | 0.3125 | no |
| Qwen3.8-27B | livecodebench | 30 | 83.3 | 73.3 | -10.0 | [-23.3, +0.0] | 0 / 3 | 1.0000 | no |
| Qwen3.8-27B | simpleqa_verified | 40 | 12.5 | 57.5 | +45.0 | [+25.0, +62.5] | 20 / 2 | 0.0015 | **yes** |
| Qwen3.8-27B | hle_text | 40 | 22.5 | 12.5 | -10.0 | [-22.5, +2.5] | 2 / 6 | 1.0000 | no |
| Qwen3.8-27B | musr | 22 | 90.9 | 90.9 | +0.0 | [+0.0, +0.0] | 0 / 0 | 1.0000 | no |
| Qwen3.8-27B | cruxeval_o | 20 | 95.0 | 95.0 | +0.0 | [+0.0, +0.0] | 0 / 0 | 1.0000 | no |
| Ornith-1.5-35B-A3B | gpqa_diamond | 98 | 86.7 | 85.7 | -1.0 | [-8.2, +5.1] | 5 / 6 | 1.0000 | no |
| Ornith-1.5-35B-A3B | livecodebench | 30 | 63.3 | 63.3 | +0.0 | [-10.0, +10.0] | 1 / 1 | 1.0000 | no |
| Ornith-1.5-35B-A3B | simpleqa_verified | 40 | 17.5 | 60.0 | +42.5 | [+22.5, +60.0] | 19 / 2 | 0.0024 | **yes** |
| Ornith-1.5-35B-A3B | hle_text | 40 | 30.0 | 17.5 | -12.5 | [-22.5, -2.5] | 0 / 5 | 0.5625 | no |
| Ornith-1.5-35B-A3B | musr | 22 | 95.5 | 86.4 | -9.1 | [-22.7, +0.0] | 0 / 2 | 1.0000 | no |
| Ornith-1.5-35B-A3B | cruxeval_o | 20 | 80.0 | 85.0 | +5.0 | [+0.0, +15.0] | 1 / 0 | 1.0000 | no |

### 7E.2 Gap to Claude Opus 5.5 and Gemini 4 Argon, before and after retrieval

gap = closed − open accuracy (pp; positive = closed model ahead), on the items both models have (Gemini: 249). closed = gap before − gap after; share = closed / gap before (only when the gap before is positive). The closed models ran without retrieval (panel answers). The test is on the gap AFTER retrieval (paired bootstrap CI, exact McNemar, Holm within the overall table (8) and the per-benchmark table (24)). Claude's 20 CRUXEval items were refused by Anthropic's safety filter (counted wrong), so read the excluding-CRUXEval rows for the overall comparison.

| open model | closed model | items | closed acc | open before | open after | gap before | gap after | closed (pp) | share closed | gap after 95% CI | Holm p (after) | still significant |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3.8-27B | Claude Opus 5.5 | all 250 (n 250) | 77.2 | 65.6 | 72.4 | +11.6 | +4.8 | +6.8 | 58.6% | [-2.0, +11.6] | 0.2007 | no |
| Qwen3.8-27B | Claude Opus 5.5 | excl. CRUXEval (230) (n 230) | 83.9 | 63.0 | 70.4 | +20.9 | +13.5 | +7.4 | 35.4% | [+7.4, +19.6] | 0.0002 | **yes** |
| Qwen3.8-27B | Gemini 4 Argon | all 250 (n 249) | 82.7 | 65.5 | 72.3 | +17.3 | +10.4 | +6.8 | 39.5% | [+5.6, +15.7] | 0.0004 | **yes** |
| Qwen3.8-27B | Gemini 4 Argon | excl. CRUXEval (230) (n 230) | 81.3 | 63.0 | 70.4 | +18.3 | +10.9 | +7.4 | 40.5% | [+5.2, +16.5] | 0.0005 | **yes** |
| Ornith-1.5-35B-A3B | Claude Opus 5.5 | all 250 (n 250) | 77.2 | 64.0 | 68.0 | +13.2 | +9.2 | +4.0 | 30.3% | [+2.4, +16.0] | 0.0256 | **yes** |
| Ornith-1.5-35B-A3B | Claude Opus 5.5 | excl. CRUXEval (230) (n 230) | 83.9 | 62.6 | 66.5 | +21.3 | +17.4 | +3.9 | 18.4% | [+10.9, +23.9] | 0.0000 | **yes** |
| Ornith-1.5-35B-A3B | Gemini 4 Argon | all 250 (n 249) | 82.7 | 64.3 | 67.9 | +18.5 | +14.9 | +3.6 | 19.6% | [+9.2, +20.5] | 0.0000 | **yes** |
| Ornith-1.5-35B-A3B | Gemini 4 Argon | excl. CRUXEval (230) (n 230) | 81.3 | 62.6 | 66.5 | +18.7 | +14.8 | +3.9 | 20.9% | [+8.7, +20.9] | 0.0000 | **yes** |
| Qwen3.8-27B | Claude Opus 5.5 | gpqa_diamond (n 98) | 90.8 | 87.8 | 93.9 | +3.1 | -3.1 | +6.1 | 200.0% | [-8.2, +2.0] | 1.0000 | no |
| Qwen3.8-27B | Claude Opus 5.5 | livecodebench (n 30) | 96.7 | 83.3 | 73.3 | +13.3 | +23.3 | -10.0 | -75.0% | [+10.0, +40.0] | 0.2656 | no |
| Qwen3.8-27B | Claude Opus 5.5 | simpleqa_verified (n 40) | 75.0 | 12.5 | 57.5 | +62.5 | +17.5 | +45.0 | 72.0% | [-5.0, +40.0] | 1.0000 | no |
| Qwen3.8-27B | Claude Opus 5.5 | hle_text (n 40) | 60.0 | 22.5 | 12.5 | +37.5 | +47.5 | -10.0 | -26.7% | [+32.5, +62.5] | 0.0001 | **yes** |
| Qwen3.8-27B | Claude Opus 5.5 | musr (n 22) | 95.5 | 90.9 | 90.9 | +4.5 | +4.5 | +0.0 | 0.0% | [+0.0, +13.6] | 1.0000 | no |
| Qwen3.8-27B | Claude Opus 5.5 | cruxeval_o (n 20) | 0.0 | 95.0 | 95.0 | -95.0 | -95.0 | +0.0 | – | [-100.0, -85.0] | 0.0001 | **yes** |
| Qwen3.8-27B | Gemini 4 Argon | gpqa_diamond (n 98) | 95.9 | 87.8 | 93.9 | +8.2 | +2.0 | +6.1 | 75.0% | [-2.0, +6.1] | 1.0000 | no |
| Qwen3.8-27B | Gemini 4 Argon | livecodebench (n 30) | 86.7 | 83.3 | 73.3 | +3.3 | +13.3 | -10.0 | -300.0% | [+0.0, +30.0] | 1.0000 | no |
| Qwen3.8-27B | Gemini 4 Argon | simpleqa_verified (n 40) | 75.0 | 12.5 | 57.5 | +62.5 | +17.5 | +45.0 | 72.0% | [-2.5, +37.5] | 1.0000 | no |
| Qwen3.8-27B | Gemini 4 Argon | hle_text (n 40) | 37.5 | 22.5 | 12.5 | +15.0 | +25.0 | -10.0 | -66.7% | [+7.5, +42.5] | 0.2329 | no |
| Qwen3.8-27B | Gemini 4 Argon | musr (n 22) | 100.0 | 90.9 | 90.9 | +9.1 | +9.1 | +0.0 | 0.0% | [+0.0, +22.7] | 1.0000 | no |
| Qwen3.8-27B | Gemini 4 Argon | cruxeval_o (n 19) | 100.0 | 94.7 | 94.7 | +5.3 | +5.3 | +0.0 | 0.0% | [+0.0, +15.8] | 1.0000 | no |
| Ornith-1.5-35B-A3B | Claude Opus 5.5 | gpqa_diamond (n 98) | 90.8 | 86.7 | 85.7 | +4.1 | +5.1 | -1.0 | -25.0% | [-2.0, +12.2] | 1.0000 | no |
| Ornith-1.5-35B-A3B | Claude Opus 5.5 | livecodebench (n 30) | 96.7 | 63.3 | 63.3 | +33.3 | +33.3 | +0.0 | 0.0% | [+16.7, +50.0] | 0.0391 | **yes** |
| Ornith-1.5-35B-A3B | Claude Opus 5.5 | simpleqa_verified (n 40) | 75.0 | 17.5 | 60.0 | +57.5 | +15.0 | +42.5 | 73.9% | [-7.5, +35.0] | 1.0000 | no |
| Ornith-1.5-35B-A3B | Claude Opus 5.5 | hle_text (n 40) | 60.0 | 30.0 | 17.5 | +30.0 | +42.5 | -12.5 | -41.7% | [+27.5, +57.5] | 0.0003 | **yes** |
| Ornith-1.5-35B-A3B | Claude Opus 5.5 | musr (n 22) | 95.5 | 95.5 | 86.4 | +0.0 | +9.1 | -9.1 | – | [+0.0, +22.7] | 1.0000 | no |
| Ornith-1.5-35B-A3B | Claude Opus 5.5 | cruxeval_o (n 20) | 0.0 | 80.0 | 85.0 | -80.0 | -85.0 | +5.0 | – | [-100.0, -70.0] | 0.0003 | **yes** |
| Ornith-1.5-35B-A3B | Gemini 4 Argon | gpqa_diamond (n 98) | 95.9 | 86.7 | 85.7 | +9.2 | +10.2 | -1.0 | -11.1% | [+4.1, +17.3] | 0.1206 | no |
| Ornith-1.5-35B-A3B | Gemini 4 Argon | livecodebench (n 30) | 86.7 | 63.3 | 63.3 | +23.3 | +23.3 | +0.0 | 0.0% | [+6.7, +40.0] | 0.6250 | no |
| Ornith-1.5-35B-A3B | Gemini 4 Argon | simpleqa_verified (n 40) | 75.0 | 17.5 | 60.0 | +57.5 | +15.0 | +42.5 | 73.9% | [-2.5, +35.0] | 1.0000 | no |
| Ornith-1.5-35B-A3B | Gemini 4 Argon | hle_text (n 40) | 37.5 | 30.0 | 17.5 | +7.5 | +20.0 | -12.5 | -166.7% | [+2.5, +37.5] | 0.8606 | no |
| Ornith-1.5-35B-A3B | Gemini 4 Argon | musr (n 22) | 100.0 | 95.5 | 86.4 | +4.5 | +13.6 | -9.1 | -200.0% | [+0.0, +27.3] | 1.0000 | no |
| Ornith-1.5-35B-A3B | Gemini 4 Argon | cruxeval_o (n 19) | 100.0 | 84.2 | 84.2 | +15.8 | +15.8 | +0.0 | 0.0% | [+0.0, +31.6] | 1.0000 | no |

### 7E.3 Retrieval recall on the test items and accuracy split by it

Found = the normalized reference answer (lower-case, accents and punctuation removed) appears as whole words in the retrieved passages (title + text) — the same rule as on the dev set. For SimpleQA and HLE exact-match items the reference answer is the target; for GPQA and HLE multiple-choice the text of the correct option is used (indicative only: long option texts rarely appear verbatim, short ones such as numbers can match by chance). LiveCodeBench, MuSR and CRUXEval have no answer string to look for.

| benchmark | target | n with target | found | recall |
|---|---|---|---|---|
| simpleqa_verified | reference answer | 40 | 18 | 45.0% |
| hle_text | reference answer | 26 | 1 | 3.8% |
| hle_text | correct option text | 14 | 1 | 7.1% |
| gpqa_diamond | correct option text | 98 | 8 | 8.2% |

Dev-set recall of the frozen setup (100 separate SimpleQA questions): 48.0%.

Accuracy split by whether retrieval found the answer (SimpleQA + HLE exact-match items; with = with retrieval, without = panel). If accuracy WITH retrieval is low where the answer WAS found, the model failed to read it (reading failure); where it was not found, retrieval failed.

| model | answer found in passages? | n | correct without | correct with | change |
|---|---|---|---|---|---|
| Qwen3.8-27B | yes | 19 | 3 (15.8%) | 18 (94.7%) | +15 |
| Qwen3.8-27B | no | 47 | 9 (19.1%) | 8 (17.0%) | -1 |
| Ornith-1.5-35B-A3B | yes | 19 | 4 (21.1%) | 18 (94.7%) | +14 |
| Ornith-1.5-35B-A3B | no | 47 | 11 (23.4%) | 11 (23.4%) | +0 |

SimpleQA only, items where the answer was in the passages: Qwen3.8-27B 17/18 correct with retrieval; Ornith-1.5-35B-A3B 17/18 correct with retrieval.
Retrieval failures (answer not in passages) cap what retrieval can add; reading failures (answer present, model still wrong) show how well the model uses the passages.

### 7E.4 Where retrieval hurt (and helped)

right→wrong = correct without retrieval, wrong with it; wrong→right = the reverse. Part of both is sampling noise: the two runs use the same seed but a different prompt, so even with no real effect some items flip.

| model | benchmark | n | right→wrong | wrong→right | net |
|---|---|---|---|---|---|
| Qwen3.8-27B | gpqa_diamond | 98 | 0 | 6 | +6 |
| Qwen3.8-27B | livecodebench | 30 | 3 | 0 | -3 |
| Qwen3.8-27B | simpleqa_verified | 40 | 2 | 20 | +18 |
| Qwen3.8-27B | hle_text | 40 | 6 | 2 | -4 |
| Qwen3.8-27B | musr | 22 | 0 | 0 | +0 |
| Qwen3.8-27B | cruxeval_o | 20 | 0 | 0 | +0 |
| Qwen3.8-27B | **all** | 250 | 11 | 28 | +17 |
| Ornith-1.5-35B-A3B | gpqa_diamond | 98 | 6 | 5 | -1 |
| Ornith-1.5-35B-A3B | livecodebench | 30 | 1 | 1 | +0 |
| Ornith-1.5-35B-A3B | simpleqa_verified | 40 | 2 | 19 | +17 |
| Ornith-1.5-35B-A3B | hle_text | 40 | 5 | 0 | -5 |
| Ornith-1.5-35B-A3B | musr | 22 | 2 | 0 | -2 |
| Ornith-1.5-35B-A3B | cruxeval_o | 20 | 0 | 1 | +1 |
| Ornith-1.5-35B-A3B | **all** | 250 | 16 | 26 | +10 |

Benchmarks where Wikipedia should not matter (GPQA, LiveCodeBench, MuSR, CRUXEval; 170 items): Qwen3.8-27B 3 right→wrong vs 6 wrong→right; Ornith-1.5-35B-A3B 9 right→wrong vs 7 wrong→right.

### 7E.5 Cost

**Retrieval itself** (one query at a time, CPU BM25 + no reranker): mean 0.20 s, median 0.10 s, 95th percentile 0.83 s, max 1.20 s per question. Index: 16.2 GB on disk, plus the 20.6 GB passage collection it was built from (which can be deleted; the index stores the passages); building took 8 min on this 96-thread CPU. Searching runs in a Java process (JDK 21) on CPU; no GPU is needed for retrieval.

**Effect on the model's work** (paired per item, with − without; prompt tokens from the server):

| model | benchmark | n | extra prompt tokens (mean) | thinking tokens without → with (mean) | change | seconds/item without → with (mean) | forced conclusions without → with |
|---|---|---|---|---|---|---|---|
| Qwen3.8-27B | gpqa_diamond | 98 | 742 | 8700 → 8695 | -5 (-0%) | 422 → 424 | 30 → 30 |
| Qwen3.8-27B | livecodebench | 30 | 768 | 11157 → 11891 | +734 (+7%) | 551 → 587 | 14 → 16 |
| Qwen3.8-27B | simpleqa_verified | 40 | 632 | 6680 → 2837 | -3843 (-58%) | 314 → 135 | 6 → 3 |
| Qwen3.8-27B | hle_text | 40 | 704 | 14068 → 14614 | +545 (+4%) | 684 → 711 | 30 → 30 |
| Qwen3.8-27B | musr | 22 | 547 | 4836 → 3760 | -1076 (-22%) | 248 → 197 | 1 → 0 |
| Qwen3.8-27B | cruxeval_o | 20 | 800 | 1379 → 1005 | -374 (-27%) | 69 → 51 | 0 → 0 |
| Qwen3.8-27B | **all** | 250 | 710 | 8605 → 8039 | -566 (-7%) | 419 → 394 | 81 → 79 |
| Ornith-1.5-35B-A3B | gpqa_diamond | 98 | 744 | 6089 → 5809 | -280 (-5%) | 58 → 56 | 20 → 15 |
| Ornith-1.5-35B-A3B | livecodebench | 30 | 779 | 10937 → 10494 | -443 (-4%) | 105 → 102 | 14 → 17 |
| Ornith-1.5-35B-A3B | simpleqa_verified | 40 | 637 | 367 → 238 | -129 (-35%) | 4 → 3 | 0 → 0 |
| Ornith-1.5-35B-A3B | hle_text | 40 | 705 | 11699 → 12084 | +385 (+3%) | 109 → 112 | 21 → 23 |
| Ornith-1.5-35B-A3B | musr | 22 | 547 | 4947 → 3541 | -1407 (-28%) | 48 → 36 | 2 → 1 |
| Ornith-1.5-35B-A3B | cruxeval_o | 20 | 804 | 1224 → 718 | -506 (-41%) | 13 → 9 | 0 → 0 |
| Ornith-1.5-35B-A3B | **all** | 250 | 711 | 6163 → 5877 | -286 (-5%) | 59 → 57 | 57 → 56 |

Forced conclusions = items where thinking hit the 16,384-token budget and the forced-conclusion message was injected (scorer flag). Qwen's without-retrieval seconds come from the Stage 2B run on the same GPU and settings (October 2026).

### 7E.6 Judge agreement (SimpleQA + HLE short answers, with retrieval)

| answers by | n judged by both | agreement | Cohen's κ | gpt-oss-20b says correct | Qwen3.8-27B says correct |
|---|---|---|---|---|---|
| Qwen3.8-27B | 66 | 100.0% | 1.00 | 26 | 26 |
| Ornith-1.5-35B-A3B | 65 | 96.9% | 0.94 | 29 | 31 |

Qwen3.8-27B also judges its own answers here (as in the panel); the primary verdict is always gpt-oss-20b's.

### 7E.7 Run health

Statuses with retrieval: Qwen3.8-27B SCORABLE 250; Ornith-1.5-35B-A3B BUDGET_TRUNCATED 4, SCORABLE 246. Any non-SCORABLE status counts as wrong, as in the panel.

### 7E.8 Caveats

- **Snapshot date.** Wikipedia as of 1 November 2023. Facts that changed or appeared later are missing; the benchmarks themselves (HLE, January 2025; SimpleQA Verified, 2025) post-date the dump, so the questions and answer keys cannot be in it, but SimpleQA questions were written FROM Wikipedia pages, which is why retrieval can help so much there.
- **BM25 limits.** Lexical matching only: paraphrased questions, multi-hop questions and questions whose key term is rare in the answer passage are missed. A dense or hybrid retriever, query rewriting by the model, or more passages (limited here by the 4,992-token prompt room of the frozen context) could find more.
- **Small per-benchmark samples** (20–98 items); per-benchmark differences are noisy, read the paired tests. Some right→wrong/wrong→right flips are sampling noise because the prompt changed.
- **Closed models ran without retrieval.** The comparison is "open model + local Wikipedia" vs "closed model alone"; the closed models would likely gain from retrieval too. Claude's CRUXEval items were refused.
- **Two runs, one sample each.** Without-retrieval answers are the panel's (Qwen's from Stage 2B, October 2026); with-retrieval answers are new. Same seeds, but the different prompt makes them different samples.
- **Recall measure** is string matching; an answer phrased differently in the passage counts as not found, and short numeric answers can match by chance.

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

Model panel and closed-model changes (panel `DEVIATIONS.md`, `DECISIONS.md`):

18. **Newer llama.cpp for K2-Horizon only.** The frozen build (b11349) does not support K2-Horizon's architecture,
    so K2-Horizon ran on build b11454 (commit `4625240437`), the oldest release that supports it, built separately
    with the same options. Every other model used the frozen b11349. K2-Horizon also did not fit fully on the GPU,
    so by the Stage 1 placement rule about 1.1 GB of its expert weights ran from CPU memory.
19. **Gemini thinking setting changed after the pilot** (2026-11-01). The plan used a 16,384-token thinking budget,
    but Gemini 4 Argon has no token budget: in the pilot, small budgets gave no thinking at all and 16,384 did not
    cap it. It was switched to thinking level "high" with the same 18,560-token total limit. This matches the open
    models' "high" reasoning effort and gave the same results on all 12 pilot items.
20. **Per-model API budget cap** (2026-11-01). A `--max-usd-per-model` limit was added so each closed model has its
    own spending cap, on top of the shared budget. Actual spend was $16.08 (section 7C.10).

Stage 2C changes (Stage 2C `DECISIONS.md`; the Stage 2C archive has no `DEVIATIONS.md`):

21. **Stage 2 items scored on the lab server, except the student items.** The answer key and scorers were
    available on the server, so 266 of 284 items were scored there with the laptop's scorer unchanged. It
    reproduced the laptop's Qwen, Gemma and gpt-oss scores on all 798 non-student rows (0 disagreements). The 18
    student items need the laptop (the app grader and Docker exist only there) and are pending.
22. **Own runner lock and port.** The Stage 2 approval gate and runner lock are tied to the Qwen/Gemma freeze, so
    Stage 2C used a copy of the Stage 2 run loop with its own lock (in /data/stage2c) and port 8185. No Stage 2
    file was edited.
23. **Per-item time limit from Ornith's panel speed.** The watchdog limit (2,117 s) used Ornith's slowest long
    panel item (109.9 tok/s) instead of a Stage 2 speed probe, which Ornith never had.

Stage 2D changes (Stage 2D `DEVIATIONS.md`, `DECISIONS.md`):

24. **Only intended change: a block of Wikipedia passages at the start of each prompt.** Everything else (model
    files, llama.cpp b11349, templates, sampling, seeds, 16,384 + 2,048 tokens, n_ctx 23,552) is the panel /
    Stage 2B setting. Mean +~700 prompt tokens; the longest prompt (4,544 tokens) fits the 4,992-token room.
25. **Pyserini (Lucene) instead of bm25s** for the BM25 search, with a portable JDK 21. bm25s builds its index in
    memory and 19 million passages would not fit.
26. **Passage budget of 3,000 characters instead of a fixed number of passages.** Every fixed top-k setup
    overflowed the prompt room on 1 to 30 test items (long chemistry-name lists), so a character budget was
    added and tuned on the 100 dev questions. Only test prompt lengths were checked, never answers.
27. **No reranker.** A cross-encoder reranker (ms-marco-MiniLM-L-6-v2) was tested on the dev questions but found
    the answer less often than plain BM25 order at every size.
28. **Search done once before generation.** The search is deterministic, so passages for all 250 questions were
    computed and frozen before the model runs.
29. **Baselines and timing from earlier runs.** "Without search" scores and times are the panel's (Qwen's from
    its Stage 2B run, 2026-10-24 to 28; Ornith's from the panel, 2026-10-29), same GPU and settings. Port 8186;
    run order Ornith then Qwen.

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

### 10.2 Stage 2C, local retrieval, then better search

The Claude and Gemini comparison is done (section 7C). Stage 2C (section 7D) and Stage 2D, the local Wikipedia
search (section 7E), are done. Next:

1. **Stage 2C laptop step:** score Ornith's 18 student items on the laptop (app grader + Docker), to get its
   official 284-item Stage 2 score. This cannot change the Qwen vs Ornith result.
2. **Stage 2E: improved search (running).** Stage 2D showed that when the search found the answer, both models
   were right 94.7% of the time, but it found the answer on only 45.0% of SimpleQA questions. Stage 2E tries
   meaning-based (dense) search, reranking, more passages, query rewriting, and searching only when the question
   needs facts.
3. **Stage 2F:** faster answers (multi-token prediction, less thinking on easy questions), code self-testing, and
   one combined setup that routes each question to the right model and tools.
4. **Write-up** of the whole project.

### 10.3 Grading checks for Stage 2B

- Independent re-judge with gpt-oss-20b: **done**. It agreed with the first judge on all 257 answers and no score
  changed (section 7B.6).
- Human spot-check of 40 judged items: planned.

### 10.4 Still open from Stage 2

- Policy B forced-item reruns for Qwen3.8-27B and Gemma 4 31B have not been run. `run_forced_rerun.py` currently
  accepts only the gpt-oss selection, so it needs a small reviewed change and approval first
  (`MORGAN_HANDOFF.md` section 8). These reruns cannot change the official scores.

---

## Open questions

These were marked TODO in earlier versions of the README.

- **Step-D selection rule** (section 4.2): the rule used to pick the 7 local models at step D, including why
  Ministral 3 14B Reasoning was added from outside the pool. **Partly answered (2026-11-02):** no rule was written
  down at the time. The README (section 4) now says what the 7 have in common, which candidates were too large and
  which 10 would have fit but were never tested. Still open: why Ministral 3 14B Reasoning was chosen over the
  in-pool models that fit, and the size of the 8 candidates marked "not stated in our sources" in section 4.3.
- **Stage 2C start date** (section 2): **answered (2026-11-04):** generation ran 2026-11-02 13:57 to 16:23 UTC
  (Stage 2C `HANDOFF.md`).
- **Ornith's license file** (section 7D.4): Ornith's model card says MIT but links to a LICENSE file that does
  not exist in its repo. Ask ornith-ai to add it before deploying Ornith.

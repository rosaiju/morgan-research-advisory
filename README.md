# Choosing an open-weight LLM for the Morgan lab server

Last updated 2026-11-02. Author: Rohan Sainju (rosai2@morgan.edu).

Every number here comes from a file in this repository, from the run logs (`local/runs/`, not tracked by git), or
from the Stage 2B and model-panel results archives (kept outside git). **No benchmark questions, answer keys or
model answers appear in this README or anywhere in git.**

---

## Key findings

- **Qwen3.8-27B is the strongest open model that fits our 24 GB GPU**, across Stage 2 (82.7%), Stage 2B (65.6%)
  and the 8-model panel (65.6%). Its lead over Gemma 4 31B is small and not significant.
- **Ornith-1.5-35B-A3B is statistically tied with Qwen** (64.0% vs 65.6%) **and about 7 times faster** (59 s vs
  419 s per question).
- **Top closed models (Claude Opus 5.5, Gemini 4 Argon) are about 18 to 21 points ahead overall**, and the gap is
  significant.
- **Most of that gap is factual knowledge** (about 60 points on SimpleQA). On science, coding and multi-step
  reasoning the gap is 3 to 13 points and not significant. Claude's lead on Humanity's Last Exam (+37.5) is the
  other significant gap.
- **Moving from the home computer to the lab server made runs about 7 to 11 times faster.**
- **Next step:** add local retrieval (search over an offline copy of Wikipedia) to close the knowledge gap.

---

## 1. What this project is

We are testing open-weight large language models to find the strongest one to run on the Morgan lab GPU server
for students. So far, we run the models as released (inference) and score their answers on fixed benchmarks; we
have not trained or fine-tuned any model. Our next step, adding a search over an offline copy of Wikipedia, also
leaves the models unchanged: it gives them relevant text to read along with each question.

---

## 2. Status at a glance

| Stage | Dates | What was done | Main result | Status |
|---|---|---|---|---|
| Model selection | 2026-09-29 to 10-02 | 35 candidates narrowed to 7 local models | 7 models for Stage 1 | Done |
| Stage 1 (home computer) | 2026-10-02 to 10-05 | 7 models x 22 items | Qwen, Gemma 21/22, gpt-oss 20/22 went on | Done |
| Stage 2 (home + lab server) | 2026-10-05 to 10-19 | 3 models x 284 items | Qwen 82.7%, Gemma 82.0% (tied), gpt-oss 69.7% | Done |
| Stage 2B (expanded benchmarks) | 2026-10-23 to 10-28 | Qwen and Gemma x 503 items, 6 benchmarks | Qwen 65.6%, Gemma 62.4% (not significant) | Done |
| Model panel (open models) | 2026-10-29 to 11-01 | 4 more open models x 250 Stage 2B items | Qwen still best; Ornith tied and about 7x faster | Done |
| Closed-model comparison | 2026-11-01 | Claude Opus 5.5 and Gemini 4 Argon, same 250 items | Closed models about 18 to 21 points ahead | Done |
| Stage 2C: Ornith on Stage 2 items and license check | | Ornith on the 284 Stage 2 items; license check | | Running |

Full table with exact dates and notes: [DETAILS.md, section 2](docs/DETAILS.md#2-status-at-a-glance).

---

## 3. Setup

| Item | Value |
|---|---|
| Lab server GPU | NVIDIA RTX 4500 Ada Generation, 24 GB (24,570 MiB), GPU index 1 |
| Lab server other GPUs | 2 x NVIDIA T1000 (8 GB each), not used for the runs |
| Lab server CPU | 48 physical / 96 logical cores |
| Lab server RAM | 123.2 GB |
| Lab server storage | Separate `/data` volume, about 10.6 TB |
| Lab server OS | Ubuntu 26.04 LTS |
| Home computer | NVIDIA GeForce RTX 4060, 8 GB; Intel Core i7-14700F (20 cores / 28 threads); 32 GB RAM |
| llama.cpp | build b11349, commit `fb4b2737a` (K2-Horizon only: b11454, see section 6) |
| Models | 4-bit `Q4_K_M` GGUF files (gpt-oss-20b: its native MXFP4) |
| Token limits (Stage 2 onward) | 16,384 thinking + 2,048 answer tokens (Stage 1: 6,144 + 1,536) |

**Speed-up:** a full Stage 2 run was projected at 122.2 h (5.1 days) for Qwen and 166.5 h (6.9 days) for Gemma on
the home computer, but measured 16.29 h and 15.76 h on the lab server: **about 7 to 11 times faster per model**
(7.5x and 10.6x). On the same item, the server was 6.8x (Qwen) and 7.3x (Gemma) faster in tokens per second.

Software versions, per-model memory and speed, and the full run-time breakdown:
[DETAILS.md, sections 5 and 6](docs/DETAILS.md#5-system-setup).

---

## 4. How we chose the models

- **35 candidates** were collected from publisher pages and independent evaluators (Artificial Analysis, Epoch).
- They were first narrowed to 6 very large models to run through paid APIs. **We switched to local runs** because,
  after we calculated the cost, running the models through APIs came out too high and was not worth it. The later
  closed-model comparison (section 5.1) used APIs only for 2 models on 250 questions, which cost about $17.
- **7 smaller models** were run locally in Stage 1; the **top 3** (Qwen3.8-27B, Gemma 4 31B, gpt-oss-20b) went on
  to Stage 2.
- **October 2026 pool update:** we checked independent rankings and recent releases and added the newest models
  that fit a 24 GB GPU: **Ornith-1.5-35B-A3B, K2-Horizon-MoVA-36B-A4B and Nanbeige4.3-33B**, plus gpt-oss-20b
  as a reference (4 models in the panel). They were released after the original 35-model pool was built.

The full 35-candidate table and each narrowing step:
[DETAILS.md, section 4](docs/DETAILS.md#4-how-we-chose-the-models-35-to-7-to-3).

---

## 5. Results (newest first)

### 5.1 Model panel and closed models (250 questions)

**Setup:** 250 of the 503 frozen Stage 2B questions (GPQA Diamond 98, LiveCodeBench 30, SimpleQA Verified 40,
Humanity's Last Exam 40, MuSR 22, CRUXEval 20). Open models on the lab server with the same settings; Claude Opus
5.5 and Gemini 4 Argon through their APIs with the same prompts. Gemini has 249 scored items (one API call failed).

**Leaderboard.** Accuracy = percent fully correct; brackets are 95% confidence intervals. "Excl. CRUXEval" leaves
out the 20 CRUXEval questions for every model (230 questions), because Anthropic's safety filter blocked all of
Claude's CRUXEval prompts. That column is the fairer comparison with Claude.

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

**Per benchmark** (accuracy %; number of questions in the header):

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

**Open models vs Qwen** (same 250 questions; paired McNemar test, corrected for 5 comparisons with Holm):

| Model | Difference from Qwen (points) | 95% CI | Corrected p | Significant? |
|---|---|---|---|---|
| Ornith-1.5-35B-A3B | -1.6 | [-6.0, +2.8] | 0.60 | No |
| Gemma 4 31B | -3.2 | [-7.6, +1.2] | 0.46 | No |
| Nanbeige4.3-33B | -6.4 | [-11.2, -1.6] | 0.042 | **Yes, worse** |
| K2-Horizon-MoVA-36B-A4B | -9.2 | [-14.0, -4.8] | 0.0008 | **Yes, worse** |
| gpt-oss-20b | -23.2 | [-29.6, -17.2] | < 0.0001 | **Yes, worse** |

- **Qwen3.8-27B is still the best open model that fits our GPU**, but not by much.
- **Ornith and Gemma are statistically tied with Qwen.** Ornith is weaker on coding (LiveCodeBench 63.3% vs
  83.3%), but that is only 30 questions and was not tested on its own.
- **Nanbeige, K2-Horizon and gpt-oss-20b are clearly worse than Qwen.**

**Gap to the closed models.** Gap = closed minus open (points). All four overall gaps are significant after
correction.

| Open model | Closed model | Gap, all 250 [95% CI] | Gap, excl. CRUXEval [95% CI] |
|---|---|---|---|
| Qwen3.8-27B | Claude Opus 5.5 | +11.6 [+4.8, +18.4] | **+20.9** [+15.2, +27.0] |
| Qwen3.8-27B | Gemini 4 Argon | +17.3 [+12.0, +22.9] | **+18.3** [+12.6, +23.9] |
| Ornith-1.5-35B-A3B | Claude Opus 5.5 | +13.2 [+6.4, +20.0] | **+21.3** [+15.2, +27.4] |
| Ornith-1.5-35B-A3B | Gemini 4 Argon | +18.5 [+12.9, +24.1] | **+18.7** [+12.6, +24.8] |

Qwen's gap by benchmark (points; "yes" = significant after correcting for 24 comparisons):

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

**Speed and efficiency** (same GPU and token limits; Qwen and Gemma times come from their Stage 2B run):

| Model | Score (all 250) | Mean time per question | Total time (250) | Speed vs Qwen | Decode speed | Peak GPU memory |
|---|---|---|---|---|---|---|
| Qwen3.8-27B | 65.6% | 419 s | 29.1 h | 1.0x | 21 tok/s | 17,126 MiB |
| **Ornith-1.5-35B-A3B** | **64.0%** | **59 s** | **4.1 h** | **7.1x faster** | 117 tok/s | 20,632 MiB |
| Gemma 4 31B | 62.4% | 289 s | 20.1 h | 1.4x faster | 18 tok/s | 20,858 MiB |
| Nanbeige4.3-33B | 59.2% | 438 s | 30.4 h | about the same | 18 tok/s | 22,186 MiB |
| K2-Horizon-MoVA-36B-A4B | 56.4% | 129 s | 8.9 h | 3.3x faster | 53 tok/s | 23,128 MiB |
| gpt-oss-20b | 42.4% | 104 s | 7.2 h | 4.0x faster | 99 tok/s | 11,630 MiB |

**Ornith is statistically tied with Qwen but about 7 times faster.** K2-Horizon's speed is not fully comparable,
because part of it ran from CPU memory.

**Caveats:**

- Anthropic's safety filter blocked all 20 of Claude's CRUXEval prompts and 3 GPQA prompts (counted wrong).
- Closed models can't be force-stopped at the thinking limit; Gemini ran out on 13 of 40 Humanity's Last Exam
  questions, Claude on 1 of 40. This can only lower their scores.
- Closed models may have seen these public questions in training. This could raise their scores.
- Per-benchmark results rest on 20 to 98 questions and are noisy.
- If answers given after hitting the thinking limit count as wrong, Qwen drops to 50.0% and Gemma stays at 62.4%.

**Grading:** two independent judges agreed on 98.4% of the 503 judged answers.
**Cost:** $16.08 for the full API run, plus $1.30 for the pilot.
Model choice, setup, grading and cost details: [DETAILS.md, section 7C](docs/DETAILS.md#7c-model-panel-and-closed-model-comparison-250-questions).

### 5.2 Stage 2B: Qwen vs Gemma on 503 new questions

| Benchmark | Items | Qwen3.8-27B | Gemma 4 31B |
|---|---|---|---|
| GPQA Diamond | 198 | 87.4% [82.0, 91.3] | 87.4% [82.0, 91.3] |
| LiveCodeBench | 60 | 83.3% [72.0, 90.7] | 73.3% [61.0, 82.9] |
| SimpleQA Verified | 80 | 13.8% [7.9, 23.0] | 11.2% [6.0, 20.0] |
| Humanity's Last Exam | 80 | 17.5% [10.7, 27.3] | 20.0% [12.7, 30.0] |
| MuSR | 45 | 95.6% [85.2, 98.8] | 84.4% [71.2, 92.3] |
| CRUXEval | 40 | 97.5% [87.1, 99.6] | 85.0% [70.9, 92.9] |
| **Overall** | **503** | **65.6% [61.4, 69.6]** | **62.4% [58.1, 66.5]** |

- **Qwen is slightly ahead (65.6% vs 62.4%), but not significantly** (p = 0.068).
- **They tied on GPQA** (87.4% each). Qwen's leads are on coding and reasoning (LiveCodeBench +10, CRUXEval +12.5,
  MuSR +11.1); none is significant on its own.
- **Qwen overthinks:** it uses about twice as many thinking tokens (8,632 vs 4,406 per item), takes about 1.5 times
  as long (420 s vs 284 s), and hit the 16,384-token thinking limit on 168 of 503 questions (Gemma: 1). If those
  forced answers count as wrong, Qwen drops to 50.7% and Gemma stays at 62.4%.

**Stage 2 and Stage 2B together:**

| Set | Items | Qwen3.8-27B | Gemma 4 31B | Qwen - Gemma (points) | 95% CI | McNemar p |
|---|---|---|---|---|---|---|
| Stage 2 | 284 | 82.7% [77.9, 86.7] | 82.0% [77.2, 86.1] | +0.7 | [-3.2, +4.6] | 0.86 |
| Stage 2B | 503 | 65.6% [61.4, 69.6] | 62.4% [58.1, 66.5] | +3.2 | [+0.0, +6.4] | 0.068 |
| **Combined** | **787** | **71.8% [68.5, 74.8]** | **69.5% [66.2, 72.6]** | **+2.3** | **[-0.1, +4.7]** | **0.089** |

Benchmarks, per-benchmark paired tests, memory and grading (including the independent re-judge):
[DETAILS.md, section 7B](docs/DETAILS.md#7b-stage-2b-results-expanded-benchmarks).

### 5.3 Stage 2: three finalists on 284 questions

Benchmarks: MMLU-Pro, MATH-500, BBEH, IFEval and a student-style suite. Brackets are 95% Wilson confidence
intervals.

| Model | Overall | MMLU-Pro | MATH-500 | BBEH | IFEval | Student |
|---|---|---|---|---|---|---|
| Qwen3.8-27B | **235/284 = 82.7%** [77.9, 86.7] | 46/61 = 75.4% | 56/58 = 96.6% | 42/67 = 62.7% | 74/80 = 92.5% | 17/18 = 94.4% |
| Gemma 4 31B | **233/284 = 82.0%** [77.2, 86.1] | 49/61 = 80.3% | 56/58 = 96.6% | 38/67 = 56.7% | 75/80 = 93.8% | 15/18 = 83.3% |
| gpt-oss-20b | **198/284 = 69.7%** [64.1, 74.8] | 41/61 = 67.2% | 51/58 = 87.9% | 22/67 = 32.8% | 68/80 = 85.0% | 16/18 = 88.9% |

Paired tests (same items; 3 comparisons, so a strict Bonferroni cut-off is p < 0.0167):

| Pair | Only A right | Only B right | McNemar p | Difference A - B (95% CI) | Significant? |
|---|---|---|---|---|---|
| Qwen vs Gemma | 17 | 15 | 0.86 | +0.7 points [-3.2, +4.6] | **No** |
| Qwen vs gpt-oss | 44 | 7 | 1.2 x 10^-7 | +13.0 points [+8.5, +17.6] | **Yes** |
| Gemma vs gpt-oss | 49 | 14 | 1.1 x 10^-5 | +12.3 points [+7.0, +17.6] | **Yes** |

- **Qwen3.8-27B and Gemma 4 31B are tied.**
- **Both are clearly better than gpt-oss-20b**, by about 12 to 13 points.

Failed items, the gpt-oss-20b bigger-budget check and Stage 1 results:
[DETAILS.md, section 7](docs/DETAILS.md#7-benchmarks-and-results).

---

## 6. Most important changes from the plan

- **Paid hosted APIs replaced by local runs**, because the API cost was too high.
- **Stage 2 split across two machines:** Dr. Wang approved moving Qwen and Gemma to the lab server (2026-10-08).
- **Stage 2B ran Tier 1 only** (503 items); the full set projected to about 133 hours against a 66-hour target.
- **LongBench v2 skipped:** no item fits the Stage 2 context size.
- **Judge re-run:** Qwen first judged its own short answers, so gpt-oss-20b re-judged all 257; they agreed on all
  257 and no score changed.
- **Gemini thinking setting changed:** Gemini 4 Argon has no token thinking budget, so it used thinking level
  "high" with the same 18,560-token total limit.

Full list of 20 changes: [DETAILS.md, section 8](docs/DETAILS.md#8-changes-from-the-original-plan).

---

## 7. What's next

- **Stage 2C (running):** Ornith-1.5-35B-A3B on the 284 Stage 2 items, plus a license check.
- **Local retrieval:** give Qwen and Ornith an offline Wikipedia search on the lab server and re-test them, to see
  how much of the knowledge gap to the closed models it closes.
- **Rest of Stage 2B:** 6 more benchmarks are ready to run (about 12 hours).
- **Human spot-check** of 40 judged items: planned.
- **Open from Stage 2:** Policy B forced-item reruns for Qwen and Gemma (need a small reviewed change and approval;
  they cannot change the official scores).

---

Full details, all tables, reproduction steps and earlier reports: [docs/DETAILS.md](docs/DETAILS.md)

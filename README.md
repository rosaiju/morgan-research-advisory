# Choosing an open-weight LLM for the Morgan lab server

Last updated 2026-11-04. Author: Rohan Sainju (rosai2@morgan.edu).

Every number here comes from a file in this repository, from the run logs (`local/runs/`, not tracked by git), or
from the Stage 2B, model-panel, Stage 2C and Stage 2D results archives (kept outside git). **No benchmark
questions, answer keys or model answers appear in this README or anywhere in git.**

---

## Key findings

- **Recommendation: Qwen3.8-27B for the student tool, with Ornith-1.5-35B-A3B as a fast option for simple
  questions.** Qwen is the strongest open model that fits our 24 GB GPU, across Stage 2 (82.7%), Stage 2B (65.6%)
  and the 8-model panel (65.6%). Its lead over Gemma 4 31B is small and not significant.
- **Ornith is not tied with Qwen overall.** It tied on the 250-question panel (64.0% vs 65.6%, not significant),
  but it is **significantly worse on the Stage 2 items: 72.9% vs 82.0%** on the 266 items scored so far (Holm
  p 0.001). The 18 student items are still waiting for laptop scoring and cannot reverse this. Ornith is about 7
  times faster (59 s vs 419 s per panel question).
- **Top closed models (Claude Opus 5.5, Gemini 4 Argon) are about 18 to 21 points ahead overall**, and the gap is
  significant.
- **Most of that gap is factual knowledge** (about 60 points on SimpleQA). On science, coding and multi-step
  reasoning the gap is 3 to 13 points and not significant. Claude's lead on Humanity's Last Exam (+37.5) is the
  other significant gap.
- **An offline Wikipedia search fixes much of the fact gap, but not the rest.** Fact accuracy (SimpleQA) rose from
  12.5% to 57.5% for Qwen and from 17.5% to 60.0% for Ornith, closing 72.0% to 73.9% of the fact gap. Overall
  it closes 5.7 points, 29% of the gap to the closed models on average (excluding CRUXEval). When the search found
  the answer, both models were right 94.7% of the time; it found the answer only 45.0% of the time on SimpleQA.
- **Licenses are not a blocker.** All five models we might deploy (Qwen, Gemma 4, Nanbeige and K2 under Apache
  2.0; Ornith under MIT) can be served free to students, with no user limits. Ornith's LICENSE file is missing from
  its repo (minor; ask the publisher to add it).
- **Moving from the home computer to the lab server made runs about 7 to 11 times faster.**
- **Next step:** Stage 2E (running) tries a better search, because the search itself is now the bottleneck.

---

## 1. What this project is

We are testing open-weight large language models to find the strongest one to run on the Morgan lab GPU server
for students. So far, we run the models as released (inference) and score their answers on fixed benchmarks; we
have not trained or fine-tuned any model. Stage 2D added a search over an offline copy of Wikipedia. This also
leaves the models unchanged: it gives them relevant text to read along with each question.

---

## 2. Status at a glance

| Stage | Dates | What was done | Main result | Status |
|---|---|---|---|---|
| Model selection | 2026-09-29 to 10-02 | 35 candidates narrowed to 7 local models | 7 models for Stage 1 | Done |
| Stage 1 (home computer) | 2026-10-02 to 10-05 | 7 models x 22 items | Qwen, Gemma 21/22, gpt-oss 20/22 went on | Done |
| Stage 2 (home + lab server) | 2026-10-05 to 10-19 | 3 models x 284 items | Qwen 82.7%, Gemma 82.0% (tied), gpt-oss 69.7% | Done |
| Stage 2B (expanded benchmarks) | 2026-10-23 to 10-28 | Qwen and Gemma x 503 items, 6 benchmarks | Qwen 65.6%, Gemma 62.4% (not significant) | Done |
| Model panel (open models) | 2026-10-29 to 11-01 | 4 more open models x 250 Stage 2B items | Qwen still best; Ornith tied on these items and about 7x faster | Done |
| Closed-model comparison | 2026-11-01 | Claude Opus 5.5 and Gemini 4 Argon, same 250 items | Closed models about 18 to 21 points ahead | Done |
| Stage 2C: Ornith on Stage 2 items and license check | 2026-11-02 | Ornith on the 284 Stage 2 items; license check | Ornith 72.9% vs Qwen 82.0% on 266 scored items (significantly worse); all licenses allow free student use | Done (18 student items: laptop scoring pending) |
| Stage 2D: local Wikipedia search | 2026-11-02 to 11-04 | Qwen and Ornith + offline Wikipedia search, same 250 items | Qwen 65.6% to 72.4% (significant), Ornith 64.0% to 68.0% (not significant) | Done |
| Stage 2E: improved search | | Better search for Qwen and Ornith | | Running |

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
| Wikipedia search (Stage 2D) | English Wikipedia snapshot of 1 Nov 2023, 18,940,032 passages; BM25 search on CPU (Pyserini/Lucene); 16.2 GB index |

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
  closed-model comparison (section 5.3) used APIs only for 2 models on 250 questions, which cost about $17.
- **7 smaller models** were run locally in Stage 1; the **top 3** (Qwen3.8-27B, Gemma 4 31B, gpt-oss-20b) went on
  to Stage 2.

**How the 7 local models were picked (step D).** When we switched to local runs, 19 of the 35 candidates were too
large for local hardware. 11 of them have stated sizes of 117B parameters or more (for example gpt-oss-120b,
Mistral-Medium-3.5-128B, GLM-5.3-Flash at 320B and Qwen3.8-2.4T). The other 8 (including GLM-5.3, Kimi-K3 and two
DeepSeek-V4 models) have no size in our sources and were treated as too large. Of the 16 that would have fit
(35B or smaller), we ran 6. The other 10 were not picked: Qwen3.5-9B, Qwen3.6-35B-A3B, Gemma 4 12B, Gemma 4
26B-A4B, Nemotron 3 Nano 30B-A3B, Granite 4.2 8B, Phi-4-reasoning-plus, DeepSeek-R1-Distill-Qwen-32B, Olmo 3.1 32B
and EXAONE 4.5 33B. We added a 7th model from outside the pool (Ministral 3 14B Reasoning). **The rule for
choosing the 7 was not written down at the time.** What they have in common: 8B to 31B parameters, a reasoning
mode, llama.cpp support, and one model per maker (Alibaba, Google, OpenAI, Zhipu, DeepSeek, Meta, Mistral). The
later model panel (section 5.3) tested newer alternatives on the same questions, and Qwen3.8-27B stayed on top.
But we never tested the 10 unpicked models that would have fit. This is a known gap (see section 7).
- **October 2026 pool update:** we checked independent rankings and recent releases and added the newest models
  that fit a 24 GB GPU: **Ornith-1.5-35B-A3B, K2-Horizon-MoVA-36B-A4B and Nanbeige4.3-33B**, plus gpt-oss-20b
  as a reference (4 models in the panel). They were released after the original 35-model pool was built.

The full 35-candidate table and each narrowing step:
[DETAILS.md, section 4](docs/DETAILS.md#4-how-we-chose-the-models-35-to-7-to-3).

---

## 5. Results (newest first)

### 5.1 Stage 2D: local Wikipedia search

**Why.** The gap to the closed models was mostly factual knowledge (section 5.3). So we gave Qwen3.8-27B and
Ornith-1.5-35B-A3B an offline Wikipedia search, without changing the models.

**Setup in plain words.**

- An offline copy of English Wikipedia (snapshot of 1 November 2023), cut into 18,940,032 short passages (up to
  200 words each).
- For each question, a BM25 keyword search picks the top passages (up to 10, within 3,000 characters; 2.33 per
  question on average). They are added to the start of the prompt.
- The search was tuned on 100 separate SimpleQA questions, then frozen before the test. No test question was used
  to tune it.
- Same 250 questions and the same settings as the panel (section 5.3). Same graders. Claude and Gemini ran
  without search.

**With vs without search** (accuracy %; significance after correction for multiple tests):

| Model | Questions | Without search | With search | Change (points) | 95% CI | Significant? |
|---|---|---|---|---|---|---|
| Qwen3.8-27B | All 250 | 65.6 | 72.4 | +6.8 | [+2.0, +11.6] | **Yes** (Holm p 0.0379) |
| Qwen3.8-27B | Excl. CRUXEval (230) | 63.0 | 70.4 | +7.4 | [+2.2, +12.6] | **Yes** (Holm p 0.0379) |
| Ornith-1.5-35B-A3B | All 250 | 64.0 | 68.0 | +4.0 | [-1.2, +9.2] | No (Holm p 0.3283) |
| Ornith-1.5-35B-A3B | Excl. CRUXEval (230) | 62.6 | 66.5 | +3.9 | [-1.7, +9.6] | No (Holm p 0.3283) |

**Per benchmark** (accuracy %, without search to with search):

| Benchmark | Qwen3.8-27B | Ornith-1.5-35B-A3B |
|---|---|---|
| GPQA Diamond (98) | 87.8 to 93.9 | 86.7 to 85.7 |
| LiveCodeBench (30) | 83.3 to 73.3 | 63.3 to 63.3 |
| SimpleQA Verified (40) | **12.5 to 57.5 (significant)** | **17.5 to 60.0 (significant)** |
| Humanity's Last Exam (40) | 22.5 to 12.5 | 30.0 to 17.5 |
| MuSR (22) | 90.9 to 90.9 | 95.5 to 86.4 |
| CRUXEval (20) | 95.0 to 95.0 | 80.0 to 85.0 |

In plain words: **the search helps a lot on fact questions** (SimpleQA, significant for both models, Holm p 0.0015
for Qwen and 0.0024 for Ornith). **On every other benchmark the change is not significant.** For Qwen, the overall
gain is significant; for Ornith it is not.

**Gap to Claude and Gemini, before and after search** (gap = closed minus open, in points; the closed models ran
without search):

| Open model | Closed model | Excl. CRUXEval (230): before to after | Share closed | Still significant? | All 250: before to after | Share closed |
|---|---|---|---|---|---|---|
| Qwen3.8-27B | Claude Opus 5.5 | +20.9 to +13.5 | 35.4% | Yes | +11.6 to +4.8 | 58.6% (no longer significant) |
| Qwen3.8-27B | Gemini 4 Argon | +18.3 to +10.9 | 40.5% | Yes | +17.3 to +10.4 | 39.5% |
| Ornith-1.5-35B-A3B | Claude Opus 5.5 | +21.3 to +17.4 | 18.4% | Yes | +13.2 to +9.2 | 30.3% |
| Ornith-1.5-35B-A3B | Gemini 4 Argon | +18.7 to +14.8 | 20.9% | Yes | +18.5 to +14.9 | 19.6% |

- **On average the search closes 5.7 points, 29% of the gap** (excluding CRUXEval, the fairer comparison because
  Claude's CRUXEval prompts were all blocked). The gap is still significant in all four comparisons.
- **On SimpleQA alone it closes 72.0% (Qwen) and 73.9% (Ornith) of the gap** to both closed models.
- Gemini has 249 items in the "All 250" column.

**Key finding: the search itself is the bottleneck, not the models' reading.**

- **When the search found the answer, both models were right 94.7% of the time** (18 of 19 SimpleQA and Humanity's
  Last Exam short-answer questions, for each model). Without the search they got only 3 (Qwen) and 4 (Ornith) of
  those 19 right.
- **When it did not find the answer, the search did not help** (Qwen 17.0%, Ornith 23.4% right, about the same as
  without search).
- **The search found the answer on only 18 of 40 SimpleQA questions (45.0%)** (48.0% on the 100 tuning questions).
  On Humanity's Last Exam and GPQA it almost never found it (3.8% to 8.2%).

**Where the search hurt.** On Humanity's Last Exam (expert questions) scores dropped: Qwen 22.5% to 12.5%,
Ornith 30.0% to 17.5%. These drops are not significant after correction, and some changes are sampling noise. But
Wikipedia rarely has the answers to these questions. **So the search should be used for factual questions, not
for everything.**

**Cost.** About **0.2 seconds per search** (mean 0.20 s, median 0.10 s, slowest 1.20 s), on the CPU, fully offline:
no GPU and no internet needed. The index is **16.2 GB** on disk. The passages add about 710 prompt tokens per
question, but the total time per question did not go up (Qwen 419 s to 394 s, Ornith 59 s to 57 s on average),
because the models think less when the answer is in front of them.

**Main caveats:**

- Wikipedia is from 1 November 2023, so newer facts are missing. SimpleQA questions were written from Wikipedia
  pages, which is why the search helps so much there.
- BM25 matches words, not meaning. It misses reworded and multi-step questions.
- Each benchmark has only 20 to 98 questions, so per-benchmark changes are noisy.
- Claude and Gemini ran without search. They would likely gain from it too.
- One run per setting. The "without search" answers are the panel's earlier answers.
- "Found the answer" is checked by matching the answer text, so it is approximate.

Full tables (all paired tests, per-benchmark gaps, run cost, judge agreement):
[DETAILS.md, section 7E](docs/DETAILS.md#7e-stage-2d-local-wikipedia-search-250-questions).

### 5.2 Stage 2C: Ornith on the Stage 2 items, and licenses

**Why.** Ornith tied with Qwen on the 250-question panel and is about 7 times faster. We ran it on the 284 Stage
2 items, with the same frozen Stage 2 settings, to see if the tie holds on a second, different set of questions.

**Scoring status: 266 of 284 items are scored.** The 18 student items are pending scoring on the laptop (their
grader and Docker sandbox exist only there). The other four benchmarks are final; the server's scorer reproduced
the earlier Qwen, Gemma and gpt-oss scores exactly.

**Stage 2 scores** (truncated answers count as wrong):

| Model | BBEH | IFEval | MATH-500 | MMLU-Pro | Student | Overall (266 items) | Official overall (284) |
|---|---|---|---|---|---|---|---|
| Ornith-1.5-35B-A3B | 29/67 = 43.3% | 64/80 = 80.0% | 55/58 = 94.8% | 46/61 = 75.4% | pending | **194/266 = 72.9%** | pending |
| Qwen3.8-27B | 42/67 = 62.7% | 74/80 = 92.5% | 56/58 = 96.6% | 46/61 = 75.4% | 17/18 = 94.4% | **218/266 = 82.0%** | 235/284 = 82.7% |
| Gemma 4 31B | 38/67 = 56.7% | 75/80 = 93.8% | 56/58 = 96.6% | 49/61 = 80.3% | 15/18 = 83.3% | **218/266 = 82.0%** | 233/284 = 82.0% |
| gpt-oss-20b | 22/67 = 32.8% | 68/80 = 85.0% | 51/58 = 87.9% | 41/61 = 67.2% | 16/18 = 88.9% | **182/266 = 68.4%** | 198/284 = 69.7% |

**Paired tests** (same 266 items; Holm correction across the 3 comparisons):

| Ornith vs | Difference (points) | 95% CI | Holm p | Significant? |
|---|---|---|---|---|
| Qwen3.8-27B | -9.0 | [-13.9, -4.5] | 0.00116 | **Yes, Ornith worse** |
| Gemma 4 31B | -9.0 | [-13.9, -4.1] | 0.00116 | **Yes, Ornith worse** |
| gpt-oss-20b | +4.5 | [-0.8, +9.8] | 0.119 | No |

**Qwen vs Ornith on everything both have run** (same GPU, same settings):

| Set | Items | Qwen | Ornith | Difference | Holm p | Significant? | Time per item, Qwen vs Ornith |
|---|---|---|---|---|---|---|---|
| Stage 2 | 266 | 82.0% | 72.9% | -9.0 | 0.000776 | **Yes** | 206 s vs 31 s (6.7x faster) |
| Panel | 250 | 65.6% | 64.0% | -1.6 | 0.597 | No | 419 s vs 59 s (7.1x faster) |

- Ornith's biggest losses: BBEH multi-step reasoning (-19.4), IFEval instruction following (-12.5),
  LiveCodeBench coding (-20.0) and CRUXEval (-15.0). None is significant on its own with so few items.
- **Ornith is never significantly better than Qwen on any benchmark.**
- Ornith decodes about 117 vs 22 tokens per second, but needs more GPU memory (20,616 vs 17,126 MiB peak on Stage 2).

**Licenses** (official Hugging Face model cards, read 2026-11-02):

| Model | License | Free to serve to students at a university? | Notes |
|---|---|---|---|
| Qwen3.8-27B | Apache 2.0 | Yes | LICENSE file in the repo |
| Ornith-1.5-35B-A3B | MIT | Yes, on the stated terms | **The LICENSE file is missing from its repo** (the card's link returns 404). Ask the publisher to add it |
| Gemma 4 31B | Apache 2.0 | Yes | Unlike Gemma 1 to 3, no prohibited-use policy |
| Nanbeige4.3-33B | Apache 2.0 | Yes | License only in the card metadata; no LICENSE file in the repo |
| K2-Horizon-MoVA-36B-A4B | Apache 2.0 | Yes | License only in the card metadata; no LICENSE file in the repo |

None of the five licenses limits the number of users or has an acceptable-use policy. The university still needs
its own usage, privacy and safety review. (Not legal advice; the university's counsel should confirm.)

**Conclusion (plain language).** Qwen3.8-27B is the better choice for a student-facing tool. Ornith is the faster
one. On the 266 Stage 2 questions scored so far, Ornith got 72.9% right and Qwen got 82.0%; that 9-point gap is
clearly real (Holm p = 0.001). Even if Ornith answered all 18 student questions correctly, it would still be about
8 points behind Qwen. **Recommendation:** use Qwen3.8-27B as the default model for students. Ornith is worth
considering only where response time matters more than accuracy, for example a fast hint mode for simple
questions or a heavily loaded server, after checking its instruction-following on real student tasks.

Per-benchmark paired tests, the full "everything" table, speed and memory, and the full license notes:
[DETAILS.md, section 7D](docs/DETAILS.md#7d-stage-2c-ornith-on-the-stage-2-items-and-licenses).

### 5.3 Model panel and closed models (250 questions)

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
- **Ornith and Gemma are statistically tied with Qwen on these 250 questions.** Ornith is weaker on coding
  (LiveCodeBench 63.3% vs 83.3%), but that is only 30 questions and was not tested on its own. **On the Stage 2
  items Ornith is significantly worse than Qwen** (section 5.2).
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

**Ornith is statistically tied with Qwen on these 250 questions but about 7 times faster** (on the Stage 2 items
it is significantly worse; section 5.2). K2-Horizon's speed is not fully comparable,
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

### 5.4 Stage 2B: Qwen vs Gemma on 503 new questions

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

### 5.5 Stage 2: three finalists on 284 questions

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
- **Stage 2C student items not scored on the server:** their grader and Docker sandbox exist only on the laptop,
  so 266 of 284 items were scored on the server (with the laptop's scorer unchanged) and 18 are pending.
- **Stage 2D search tool:** Pyserini (Lucene) instead of bm25s, because bm25s could not build an index of 19
  million passages in memory.
- **Stage 2D passage limit:** up to 3,000 characters of passages instead of a fixed number, because a fixed number
  overflowed the prompt room on some questions (long chemistry-name lists).
- **Stage 2D reranker not used:** it was tested on the tuning questions but found the answer less often than plain
  BM25.
- **Stage 2D "without search" scores reused** from the panel and Stage 2B runs (same GPU and settings).

Full list of 29 changes: [DETAILS.md, section 8](docs/DETAILS.md#8-changes-from-the-original-plan).

---

## 7. What's next

1. **Stage 2E: better search (running).** The search found the answer less than half the time, so we are improving
   it: meaning-based search, reranking, more passages, query rewriting, and searching only when a question needs
   facts.
2. **Stage 2F: faster and smarter answers.** Faster answers with multi-token prediction and less thinking on easy
   questions, code self-testing, and one combined setup that routes each question to the right model and tools.
3. **Write-up** of the whole project.

Also open:

- **Stage 2C laptop step:** score Ornith's 18 student items on the laptop (cannot change the Qwen vs Ornith result).
- **Rest of Stage 2B:** 6 more benchmarks are ready to run (about 12 hours).
- **Human spot-check** of 40 judged items: planned.
- **Open from Stage 2:** Policy B forced-item reruns for Qwen and Gemma (need a small reviewed change and approval;
  they cannot change the official scores).
- **Optional check:** test some of the 10 candidates that fit our hardware but were never picked or run
  (section 4), to close that gap in the model selection.

---

Full details, all tables, reproduction steps and earlier reports: [docs/DETAILS.md](docs/DETAILS.md)

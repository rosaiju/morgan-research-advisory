# Local evaluation handoff (unattended run started 2026-10-02 ~15:40 EDT)

**Stage 1 is BLOCKED.** `run_local.py stage1` refuses unless `config_local.json` has `calibrated=true` and the
user has written `local/STAGE1_APPROVED.json`. No unattended job creates either.

## What runs without Claude (detached processes, all resumable)

| Job | Script | Log | Behaviour |
|---|---|---|---|
| Downloads A: gpt-oss → Ministral → Muse | `local/fetch_supervisor.sh fetchA …` | `local/runs/fetchA.log` | curl resume + SHA-256 verify; retries up to 50× |
| Downloads B: GLM → Qwen3.8 → Gemma | `local/fetch_supervisor.sh fetchB …` | `local/runs/fetchB.log` | same |
| Calibration, 7 models in order | `local/calibrate_all.sh` | `local/runs/calibrate_all.log` | starts each model once its weights are verified; skips models already done |
| Post-calibration | `local/post_calibration.sh` | `local/runs/calibration-20261002/post_calibration.log` | after `ALL DONE`: scoring, C1 candidate, quiet speed re-check, Stage 1 projection, `CALIBRATION_REPORT.md` |

## Check status (any time, from Git Bash)

```
bash /c/Users/rohan/morgan-research-advisory/local/status.sh
```

## Resume after an interruption (reboot, crash, killed process)

All steps are idempotent; completed downloads/models are skipped.

```
cd /c/Users/rohan/morgan-research-advisory
# downloads (only if not all VERIFIED)
"/c/Program Files/Git/bin/bash.exe" local/fetch_supervisor.sh fetchA gpt-oss-20b ministral-3-14b-reasoning muse-glimmer-30b &
"/c/Program Files/Git/bin/bash.exe" local/fetch_supervisor.sh fetchB glm-4.7-flash qwen3.8-27b gemma-4-31b &
# calibration: a model whose model_<m>.json exists is skipped. If a model was interrupted mid-run, move its
# partial attempts_<m>.jsonl aside first (do not delete it), then:
"/c/Program Files/Git/bin/bash.exe" local/calibrate_all.sh > local/runs/calibrate_all.log 2>&1 &
"/c/Program Files/Git/bin/bash.exe" local/post_calibration.sh &
```

If `calibrate_all.log` already says `ALL DONE` but post-calibration did not finish:
`local\.venv\Scripts\python.exe local\post_calibration.py local\runs\calibration-20261002`

## Next action requiring the user's approval

Review `local/runs/calibration-20261002/CALIBRATION_REPORT.md` (C1 candidate, measured speeds, RAM/VRAM/offload,
truncation/loops, projected Stage 1 runtime). Stage 1 starts only after explicit approval.

## Results so far (interim, 2026-10-02 18:55 EDT; report file is authoritative once written)

**All seven downloads verified by 19:11 EDT** (SHA-256 match to the pinned LFS hashes).

| Model | Integration | Load s | GPU weights (layers) @29.4K ctx | tg256 probe | Decode during dev items | Dev attempts (tokens; L = hit 24,576) |
|---|---|---|---|---|---|---|
| R1-0528-Qwen3-8B | pass (template exact) | 5.5 | 0.81 (32/37) | 32.1 | 32 → 8 tok/s with depth | 10,121 · L · L · 23,624 · 3,837 · 495 |
| gpt-oss-20b | pass (exact) | 8.1 | 0.47 (25/25, experts split) | — | ~37 tok/s flat | 3,030 · L · L · L · 1,726 · 10,172 |
| GLM-4.7-Flash | pass (exact; gating=sigmoid) | 17 | 0.28 (48/48, experts on CPU) | 32.4 | ~26-30 tok/s | 14,756 · L · 991 · L · 10,563 · 18,654 |

C1 candidate after 3 models: **16,384** (12,288 fails: GLM has 2 natural completions above it).
Caveat for the user: ~half of development attempts so far end at the 24,576 dev ceiling (both MATH L5 items for
every model); the pre-registered rule ignores those censored attempts. See "would truncate" table in the report.
No thermal throttling observed (flags: idle 0x1, SW power cap 0x4; max 69 C).

Harness fixes made during the run: log verbosity for offload parsing, KV double count, token-accounting tolerance
for hidden reasoning delimiters, rendered-prompt lock separation, depth-aware runtime projection, RAM baseline,
detached download supervisor, fixed run id.

### Important timing finding (19:55 EDT)

Decode speed collapses with context depth on partially offloaded dense models: Ministral 10.3 tok/s at start ->
3.1 tok/s at 18K generated tokens (R1: 32 -> 8). The three ~30B dense models start near 3-4 tok/s, so a single
development attempt that runs to 24,576 tokens may take 5-7 h. Expected calibration time: Ministral ~4-5 h; Muse,
Qwen3.8, Gemma possibly ~8-12 h EACH. Calibration will therefore continue for a long time after the user returns.
The calibration watchdog backstop was raised (floor 0.75 tok/s, ~14 h per attempt) before the dense models start so
that genuine long attempts are not mislabelled as infrastructure failures; hangs are still caught by the 600 s
no-token rule. This depth effect is also why the projected Stage 1 runtime for the dense models will be far above
the plan's estimate; the user will need to decide how to proceed (see report).

### Interim status at 22:55 EDT (user's expected return)

Calibration done: R1-8B, gpt-oss-20b, GLM-4.7-Flash. Ministral: 5th of 6 items running (~4 h so far).
Not yet started: Muse Glimmer 30B, Qwen3.8-27B, Gemma 4 31B (run automatically next; likely 8-12 h each).

Ministral items so far: geometry 20,104 (natural, 68 min) · counting L (24,576, 97 min) · mmlu/50 1,650 ·
zebra 10,809 (natural). Decode 10.3 tok/s fresh -> ~3-4 tok/s at 15-18K depth.

**C1 = 24,576 is already determined** (top rung; later models cannot lower it): natural completions above L
(R1, gpt-oss, GLM, Ministral): 8K 2/1/3/2 (fail) · 12K 1/0/2/1 (fail) · 16K 1/0/1/1 = 3 > 2 (fail) · 24K 0 (pass).
Descriptive: development attempts not finishing naturally at L: 8K 73% · 12K 55% · 16K 50% · 24K 36%.

Interim Stage 1 projection at C1 = 24,576 (conservative: MATH costed at level-5 token use, student items at the
model's MMLU-Pro mean): R1 8.3 h core + 2.4 reserve; gpt-oss 3.7 + 1.1; GLM 6.0 + 1.7. Ministral likely ~20+ h core;
the three dense ~30B models will be several times slower than Ministral. **Stage 1 will far exceed the approved
24-48 h budget and the pre-registered "core > 40 h -> stop and report" rule applies.** This needs the user's decision.

To stop the remaining calibration (e.g. if the user decides not to measure the dense models now):
  PowerShell: Get-CimInstance Win32_Process | ? { $_.CommandLine -match 'calibrate_all|post_calibration' } |
              % { Stop-Process -Id $_.ProcessId -Force }; Stop-Process -Name llama-server -Force
(completed results in local/runs/calibration-20261002 are kept; rerunning calibrate_all.sh skips finished models)

### Queue stopped at the user's request (2026-10-02 23:15 EDT)

calibrate_all.sh and post_calibration.sh were stopped; Ministral was allowed to finish (done 23:19). Muse Glimmer,
Qwen3.8-27B and Gemma 4 31B were NOT calibrated. No jobs are running. Four-model analysis:
`calibration_report_4models.json`, `scored_4models.jsonl`, `budget_scenarios.json` (earlier files untouched).
Revised methodology awaiting approval: `local/REVISED_PROPOSAL_2026-10-02.md`. Stage 1 remains blocked.
Do NOT restart calibrate_all.sh unless the user asks (it would start Muse).

---
## Overnight session 2026-10-03 (approved: placement rule, 6,144 + 1,536 budget, ~24 h panel, dense probes)

**Stage 1 still NOT approved and NOT started.** No STAGE1_APPROVED.json exists; `run_local.py stage1` refuses.

Running (detached, resumable): `local/probe_all.sh` -> log `local/runs/probe_all.log`, results
`local/runs/probe-20261003/probe_<model>.json` (order: Muse, Qwen3.8, Gemma, gpt-oss, GLM, Ministral; R1 done).
Check: `tail -20 /c/Users/rohan/morgan-research-advisory/local/runs/probe_all.log`
Resume (skips models already probed):
  "/c/Program Files/Git/bin/bash.exe" local/probe_all.sh >> local/runs/probe_all.log 2>&1 &
After probes: `local\.venv\Scripts\python.exe local\project_stage1.py` (writes runs/probe-20261003/stage1_projection.json)
Stage 1 readiness (read-only): `local\.venv\Scripts\python.exe local\preflight.py`
Stage 1 dry run (no generation): `local\.venv\Scripts\python.exe local\run_local.py stage1 --dry-run`

### Overnight progress at ~02:30 EDT (detached jobs keep running without Claude)

Probe results so far (approved placement, Stage 1 context ~10.5K, budget 6,144 + 1,536):

| Model | Integration | tok/s fresh / 8K | old --fit split fresh / 8K | GPU weight share | VRAM / RAM added | Forced conclusion |
|---|---|---|---|---|---|---|
| R1-8B | pass (exact) | 47.3 / 39.6 | 47.0 / 39.6 (fits fully) | 93% | 5.5 GB / 0.8 GB | server OK (6,164 + 180) |
| Muse Glimmer 30B | pass (BOS-only) | 3.63 / 3.61 | 3.78 / 3.50 | 34% (FFN of 45/52 layers on CPU) | 6.0 / 11.6 GB | server FAILED (7,805 reasoning, no message) -> harness mechanism; re-validation runs after probes |
| Qwen3.8-27B | pass (exact) | 3.40 / 3.29 | 3.54 / 3.15 | 30% (all FFN on CPU + 55/65 layers; step 2) | 5.7 / 12.1 GB | server OK (6,164 + 530) |
| Gemma 4 31B | pass (BOS-only) | 2.61 / 2.50 | 2.90 / 2.37 | 24% (all FFN on CPU + 40/61 layers; step 2) | 5.9 / 15.9 GB | running |

Still to run automatically: Gemma forced/natural items, then gpt-oss, GLM, Ministral probes (probe_all.sh), then Muse
harness forced re-validation + projection (probe_followup.sh -> local/runs/probe_followup.log).
After both finish: `local\.venv\Scripts\python.exe local\summarize_probes.py` (writes PROBE_REPORT.md),
`local\.venv\Scripts\python.exe local\preflight.py`. Freezing (`local/freeze_stage1.py`) is a preparation step only;
Stage 1 still needs the user's STAGE1_APPROVED.json.

### Probe results — all seven measured (03:25 EDT, 2026-10-03)

Full tables: `local/runs/probe-20261003/PROBE_REPORT.md` (regenerate: `local\.venv\Scripts\python.exe local\summarize_probes.py`).

| Model | tok/s fresh / 8K deep | prompt tok/s | GPU weight share | VRAM / RAM added | load s | forced 6,144+1,536 |
|---|---|---|---|---|---|---|
| R1-8B | 47.3 / 39.6 | 2,351 | 93% (all on GPU) | 5.5 GB / 0.8 GB | 2-6 | server OK (6,164 + 180) |
| gpt-oss-20b | 42.2 / 40.5 | 925 | 49% | 6.2 / 6.4 GB | 7 | server OK (6,164 + 771) |
| GLM-4.7-Flash | 34.4 / 30.4 | 542 | 32% | 6.2 / 12.6 GB | 16 | server OK (6,164 + 1,302) |
| Ministral 14B | 13.4 / 12.9 (old split 14.5 / 9.1) | 878 | 62% (FFN 18/40 on CPU) | 6.0 / 3.4 GB | 3-6 | server OK (6,164 + 540*) |
| Muse Glimmer 30B | 3.63 / 3.61 (old 3.78 / 3.50) | 261 | 34% (FFN 45/52 on CPU) | 6.0 / 11.6 GB | 13 | server FAILED -> harness re-validation (see below) |
| Qwen3.8-27B | 3.40 / 3.29 (old 3.54 / 3.15) | 223 | 30% (step 2: all FFN + 10 layers on CPU) | 5.8 / 12.3 GB | 12-16 (one 72) | server OK (6,164 + 530) |
| Gemma 4 31B | 2.61 / 2.50 (old 2.90 / 2.37) | 189 | 24% (step 2: all FFN + 20 layers on CPU) | 5.9 / 15.9 GB | 16-19 | server OK (6,164 + 926) |

*Ministral counts re-derived after a transient tokenize failure (bug fixed; raw record kept). All 7 passed integration
(templates exact or BOS-only), all 7 confirmed in maximum reasoning mode, no crashes, no loops, no malformed output in
the probes, max GPU 69 C, no thermal throttling (flags: idle / software power cap only).

Stage 1 v2 projection from measured speeds: **central 23.5 h** (student items costed at IFEval length) / **conservative
31.4 h** (student items at MMLU-Pro length; MATH at level-5 token use; dense models use pooled token use).
Per model (central / conservative h): R1 0.4/0.6, gpt-oss 0.6/0.7, GLM 0.8/1.1, Ministral 1.5/1.9, Muse 5.8/7.8,
Qwen3.8 6.3/8.4, Gemma 8.2/11.0. Files: runs/probe-20261003/stage1_projection*.json.

## FINAL OVERNIGHT HANDOFF (2026-10-03 ~04:00 EDT)

**Nothing is running. Stage 1 has NOT been started.** Gate verified: `run_local.py stage1` -> "REFUSED: Stage 1 requires
the user's explicit approval file local/STAGE1_APPROVED.json" (exit 1); no stage1 run directory exists.

1. **All seven models**: downloaded, full SHA-256 re-hash MATCH (1.5 min, 2026-10-03), integration passed, maximum
   reasoning mode confirmed in the rendered prompt (Qwen "Reasoning effort is set to xhigh", Muse "Reasoning strength:
   xhigh", gpt-oss "Reasoning: high", Gemma `<|think|>`, GLM/Qwen `<think>`, R1/Ministral always on).
2. **Forced conclusion (6,144 + 1,536) validated end-to-end for all seven** on a development item that exceeds the
   budget: reasoning stops at the budget, the fixed message is injected, the model writes a real answer
   (180-1,302 tokens), the ANSWER line is extracted and scored, items are flagged `forced_conclusion`. Natural-length
   item unaffected for all seven. Six use llama-server's `--reasoning-budget`; **Muse needs the harness two-phase
   mechanism** (server forcing did not act on its ATEM channel; harness: reasoning exactly 6,144 + 347-token answer,
   EOS stop). No hard truncation without an answer occurred.
3. **Placement rule**: removes the depth penalty where attention can stay on the GPU (Ministral 8K-deep 9.1 -> 12.9
   tok/s; Muse 3.50 -> 3.61) at a 4-7% fresh-speed cost. Qwen3.8 and Gemma cannot keep all attention on the GPU
   (step 2: all FFN plus 10 / 20 whole layers on CPU); for Gemma the rule is roughly neutral (fresh 2.90 -> 2.61,
   deep 2.37 -> 2.50). Stage 1 uses the exact placement recorded in each probe (free VRAM varies by ~1 layer).
4. **Projected Stage 1 v2 runtime (measured speeds): central 23.5 h, conservative 31.4 h.** The ~24 h target is
   realistic (dense ~30B models = 86% of the time). Projection for dense models uses pooled token use from the four
   calibrated models (assumption).
5. **Stage 1 prepared**: panel v2 locked (22 items/model, no overlap with calibration or probe items), rendered
   prompts locked, scorers 45/45, harness tests 29/29, verify_all 14/14, config frozen
   (`items/stage1_v2_freeze.json`), preflight 36/37 (only the user's approval file missing), dry run clean,
   resumable (completed items skipped; tested).

Bugs found and fixed tonight: llama-fit-params summary line sometimes missing (fallback + retry, tested); llama.cpp
`--fit` refuses when tensor overrides are set (own step-2 search); Muse server-side forcing unsupported (harness
mechanism); post-attempt token counts silently None (retry + recorded error, tested); placement recomputation
non-deterministic by ~1 layer (Stage 1 uses frozen probe placement); a shell escape corrupted one handoff line (fixed).
Known non-issues: IFEval probe item carries the descriptive `loop_suspected` flag because the prompt requires
repeating the request verbatim; one Qwen load took 72 s (others 12-16 s); Docker is not running, so the one
student programming item in panel v2 (prog_word_count) will be graded "skipped" unless Docker Desktop is started.

Status / inspection commands (Git Bash):
  bash /c/Users/rohan/morgan-research-advisory/local/status.sh
  cat /c/Users/rohan/morgan-research-advisory/local/runs/probe-20261003/PROBE_REPORT.md
  /c/Users/rohan/morgan-research-advisory/local/.venv/Scripts/python.exe local/preflight.py
  /c/Users/rohan/morgan-research-advisory/local/.venv/Scripts/python.exe local/run_local.py stage1 --dry-run

**Exact Stage 1 command (only after the user writes local/STAGE1_APPROVED.json):**
  cd /c/Users/rohan/morgan-research-advisory
  "/c/Program Files/Git/bin/bash.exe" -c "local/.venv/Scripts/python.exe local/run_local.py stage1 > local/runs/stage1_v2.log 2>&1" &
  (resumable: rerun the same command after any interruption; then score with
   .venv-scoring\Scripts\python.exe local\score_local.py local\runs\stage1-v2)

**Single next decision for the user:** approve (or not) the official Stage 1 run with the frozen v2 configuration
(~24 h central, ~31 h conservative), including whether to start Docker Desktop first so the programming item is graded.

---
## Session 2026-10-03 (15 h unattended; Stage 1 still NOT approved, NOT started)

Interim status (written ~12:00 UTC / 08:00 EDT; the final summary below supersedes this when present).

- Docker programming grader implemented: `scoring/docker_code.py` (tests `scoring/test_docker_code.py`, 37 pass).
  `student/prog_word_count` is now graded in a pinned, network-less, read-only, unprivileged container (was SKIPPED).
- Harness hardening (run_local / llm_server / client), 38 offline tests pass. Re-frozen; old freezes in
  `local/items/history/`. Commit 9fa8d17. Reproducibility record: `local/REPRODUCIBILITY.md`.
- RUNNING (detached, resumable): endurance/recovery suite, NOT Stage 1, development + synthetic items only.
  Status:  tail -20 /c/Users/rohan/morgan-research-advisory/local/runs/endurance-20261003/endurance.log
           local\.venv\Scripts\python.exe local\endurance.py status
  Resume (skips passed steps): "/c/Program Files/Git/bin/bash.exe" local/endurance_all.sh &
  Stop: Get-CimInstance Win32_Process | ? { $_.CommandLine -match 'endurance' } | % { Stop-Process -Id $_.ProcessId -Force };
        Stop-Process -Name llama-server -Force

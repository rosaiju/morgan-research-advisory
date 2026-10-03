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

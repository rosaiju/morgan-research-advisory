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

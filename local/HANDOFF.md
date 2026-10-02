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

## Results so far

(updated by Claude as work completes; see the report file for the authoritative numbers)

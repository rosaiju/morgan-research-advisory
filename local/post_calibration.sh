#!/usr/bin/env bash
# Detached: wait until calibrate_all.sh finishes, then run post_calibration.py (scoring, C1 candidate,
# quiet speed re-check, Stage 1 projection, report). Never starts Stage 1.
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
RUN=local/runs/${MORGAN_RUN_ID:-calibration-20261002}
until grep -q "ALL DONE" local/runs/calibrate_all.log 2>/dev/null; do sleep 120; done
local/.venv/Scripts/python.exe local/post_calibration.py "$RUN" >> local/runs/post_calibration_stdout.log 2>&1
echo "post_calibration exit $? $(date -Is)" >> local/runs/post_calibration_stdout.log

#!/usr/bin/env bash
# Detached: after probe_all.sh finishes, re-validate forced conclusion for harness-forced models (Muse) at the real
# budget, then recompute the Stage 1 projection. Never runs Stage 1.
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8 MORGAN_PROBE_ID="${MORGAN_PROBE_ID:-probe-20261003}"
until grep -q "PROBES DONE" local/runs/probe_all.log 2>/dev/null; do sleep 60; done
local/.venv/Scripts/python.exe local/probe_local.py --forced-only muse-glimmer-30b
local/.venv/Scripts/python.exe local/project_stage1.py > local/runs/$MORGAN_PROBE_ID/stage1_projection.txt 2>&1
echo "FOLLOWUP DONE $(date -Is)"

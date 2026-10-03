#!/usr/bin/env bash
# Detached, resumable: approved short probes (dense first). Models already probed are skipped. Never runs Stage 1.
set -u
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8 MORGAN_PROBE_ID="${MORGAN_PROBE_ID:-probe-20261003}"
local/.venv/Scripts/python.exe local/probe_local.py muse-glimmer-30b qwen3.8-27b gemma-4-31b gpt-oss-20b glm-4.7-flash ministral-3-14b-reasoning r1-0528-qwen3-8b
echo "PROBES DONE $(date -Is)"

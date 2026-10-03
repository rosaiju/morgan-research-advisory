#!/usr/bin/env bash
# Detached, resumable endurance/recovery suite (NOT Stage 1). Finished steps are skipped on rerun.
#   "/c/Program Files/Git/bin/bash.exe" local/endurance_all.sh
cd /c/Users/rohan/morgan-research-advisory || exit 1
mkdir -p local/runs/endurance-20261003
echo "$$" > local/runs/endurance-20261003/driver.pid
local/.venv/Scripts/python.exe local/endurance.py all >> local/runs/endurance-20261003/endurance.log 2>&1
echo "$(date -u +%FT%TZ) endurance_all.sh exit=$?" >> local/runs/endurance-20261003/endurance.log

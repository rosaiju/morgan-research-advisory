#!/usr/bin/env bash
# Calibrate all seven models in a fixed order (fast first). Each model starts only after its weights are
# downloaded AND hash-verified (.sha256 sidecar written by fetch_models.py). Never starts Stage 1.
set -u
cd "$(dirname "$0")/.."
export MORGAN_RUN_ID="${MORGAN_RUN_ID:-calibration-20261002}"
export PYTHONIOENCODING=utf-8
PY=local/.venv/Scripts/python.exe
MODELS="r1-0528-qwen3-8b gpt-oss-20b glm-4.7-flash ministral-3-14b-reasoning muse-glimmer-30b qwen3.8-27b gemma-4-31b"
for m in $MODELS; do
  f=$($PY -c "import json;print(json.load(open('local/gguf_pins.json'))['$m']['file'])")
  until [ -f "/c/llm/models/${f}.sha256" ]; do sleep 60; done
  if [ -f "local/runs/$MORGAN_RUN_ID/model_$m.json" ]; then echo "[$m] already calibrated, skipping"; continue; fi
  echo "[$m] start $(date -Is)"
  $PY local/run_local.py calibrate "$m" || echo "[$m] FAILED with exit $? $(date -Is)"
done
echo "ALL DONE $(date -Is)"

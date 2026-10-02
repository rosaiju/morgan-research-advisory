#!/usr/bin/env bash
# One-shot status of unattended local work.   bash local/status.sh
cd "$(dirname "$0")/.."
R=local/runs
echo "== $(date -Is)"
echo "== downloads (verified = .sha256 sidecar present)"
python - <<'EOF'
import json, os
pins = json.load(open("local/gguf_pins.json"))
for k, p in pins.items():
    f = os.path.join(r"C:\llm\models", p["file"])
    have = os.path.getsize(f) if os.path.exists(f) else 0
    ok = os.path.exists(f + ".sha256")
    print(f"  {k:28s} {have/1e9:6.2f}/{p['size']/1e9:6.2f} GB  {'VERIFIED' if ok else ''}")
EOF
tail -n 2 $R/fetchA.log $R/fetchB.log 2>/dev/null
echo "== calibration (calibrate_all.log)"
tail -n 15 $R/calibrate_all.log 2>/dev/null
echo "== post-calibration"
tail -n 8 $R/calibration-20261002/post_calibration.log 2>/dev/null || echo "  (not started: waits for ALL DONE)"
echo "== processes"
tasklist | grep -iE "llama-server|curl" || echo "  none"
[ -f $R/calibration-20261002/CALIBRATION_REPORT.md ] && echo "== REPORT READY: $R/calibration-20261002/CALIBRATION_REPORT.md"
[ -f local/STAGE1_APPROVED.json ] && echo "!! STAGE1_APPROVED.json exists" || echo "== Stage 1 blocked (no local/STAGE1_APPROVED.json)"

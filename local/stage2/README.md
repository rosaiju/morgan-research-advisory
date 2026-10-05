# Stage 2 (finalists: Qwen3.8-27B, Gemma 4 31B, gpt-oss-20b) — preparation

Plan (approved 2026-10-05): full 284-item fresh panel, 16,384 reasoning + 2,048 answer tokens, scoring rules unchanged.
gpt-oss-20b runs locally (host `local-rtx4060`); Qwen3.8-27B and Gemma 4 31B on the Morgan GPU server (host
`morgan-gpu`). **No official Stage 2 generation has run.** Finalist decision: `../STAGE2_FINALISTS.md`.

| File | Role |
|---|---|
| `select_stage2.py` → `items/stage2_panel.json`, `stage2_probe_items.json`, `stage2_items_lock.json`, `SELECTION_AUDIT.md` | deterministic fresh panel (seeded), exclusion of every previously selected/run item, composition audit |
| `render_stage2.py` → `items/stage2_rendered.json` (+ lock) | exact prompts with the locked Stage 1 templates (run with `.venv-scoring`) |
| `config_stage2.json` | Stage 2 budget, hosts, rules; model settings inherited unchanged from `../config_local.json` |
| `common.py` | runtime host setup (llama.cpp/model dirs, GPU index) — Stage 1 modules reused unchanged |
| `probe_stage2.py` | development-only probe at the Stage 2 context/budget (placement, loads, 8K/16K depth speed, forced + natural dev items) |
| `freeze_stage2.py` → `items/stage2_freeze_<host>.json` | per-host freeze (needs a complete probe of that host's models) |
| `preflight_stage2.py`, `test_stage2.py` | readiness checks / offline tests (the gate is tested without launching the runner) |
| `run_stage2.py` | generation; refuses unless `STAGE2_APPROVED_<host>.json` holds that host's freeze hash and preflight is green |
| `make_morgan_bundle.py`, `MORGAN_HANDOFF.md`, `MODELS.sha256` | Morgan server bundle (no answer keys) and operator instructions |

## Open decisions (must be recorded before any Stage 2 result is inspected)

**Forced-item rerun policy** (`config_stage2.json → forced_rerun_policy`, status NOT YET PRE-REGISTERED):
- **A:** rerun every forced-conclusion item unforced at 24,576 tokens, if GPU time is practical;
- **B:** otherwise, for the dense finalists, a fixed pre-registered random subsample of forced items (size and seed
  recorded in advance); gpt-oss reruns all.

## Local gpt-oss commands (Git Bash, repo root)

```
MORGAN_HOST=local-rtx4060 local/.venv/Scripts/python.exe local/stage2/preflight_stage2.py
MORGAN_HOST=local-rtx4060 local/.venv/Scripts/python.exe local/stage2/run_stage2.py --dry-run
# only after the user writes local/stage2/STAGE2_APPROVED_local-rtx4060.json (freeze hash inside):
"/c/Program Files/Git/bin/bash.exe" -c "MORGAN_HOST=local-rtx4060 local/.venv/Scripts/python.exe local/stage2/run_stage2.py >> local/runs/stage2_local.log 2>&1" &
# status / resume (same command) / score
tail -5 local/runs/stage2_local.log
.venv-scoring/Scripts/python.exe local/score_local.py local/runs/stage2-local-rtx4060
```

# Local evaluation harness (llama.cpp, RTX 4060 8 GB + 32 GB RAM)

Two-stage local plan approved 2026-10-02 (see [../22-local-evaluation-plan.md](../22-local-evaluation-plan.md)).
No paid APIs; the only network traffic during runs is to `127.0.0.1`.

| File | Role |
|---|---|
| `config_local.json` | frozen configuration: backend build + hashes, common server flags, per-model template/kwargs/sampling with sources, loop rule, watchdog, calibration rule, `calibrated`/`C1` |
| `gguf_pins.json` | exact GGUF repo, revision, file, size and SHA-256 for the seven models |
| `official/` | publisher chat templates, tokenizer/generation configs, READMEs at pinned revisions (`official-lock.json`) |
| `fetch_models.py` | resumable download + size/SHA-256 verification (writes `<file>.sha256` sidecar) |
| `select_items.py` | deterministic Stage 1 panel (core 44 + reserve 12) and 6 calibration items → `items/` + `items_lock.json` |
| `render_prompts.py` | exact user-message text from the locked templates and sources → `items/rendered_prompts.json` + `rendered_lock.json` (run with `.venv-scoring`) |
| `llm_server.py` | starts llama-server with the frozen flags, times the load, parses fit/offload/KV from the log |
| `client.py` | streaming client: loop early-stop (12-gram ≥ 20× in last 2048 tokens) and watchdog |
| `telemetry.py` | 1 s GPU (nvidia-smi) + RAM (psutil) sampler |
| `run_local.py` | `threads`, `calibrate`; `stage1` is refused unless calibrated and `STAGE1_APPROVED.json` exists |
| `score_local.py` | the only local reader of answer keys; morgan status precedence + locked scorers (run with `.venv-scoring`) |
| `analyze_calibration.py` | applies the pre-registered C1 rule and projects Stage 1 runtime |
| `calibrate_all.sh` | calibrates all seven in fixed order once each model's weights are verified |
| `test_local.py` | offline tests (loop rule, statuses, log parsing, C1 rule, manifests, reproducibility, Stage 1 refusal, Stage 1 loop failure modes with a fake server: exceptions, load failures, resume, torn lines, disk guard, port/lock) |
| `preflight.py` / `freeze_stage1.py` | Stage 1 v2 readiness checks (read-only) / freeze record of every Stage 1 input (`items/stage1_v2_freeze.json`; history in `items/history/`) |
| `../scoring/docker_code.py` | Docker sandbox for the student programming item (no network, read-only, unprivileged, pinned image); tests `../scoring/test_docker_code.py` |
| `endurance.py`, `endurance_all.sh` | non-Stage-1 endurance/recovery suite (development + synthetic items only) |
| `REPRODUCIBILITY.md` | everything needed to reproduce Stage 1 v2 (versions, hashes, settings, sandbox, procedures) |

Environments: `local/.venv` (system Python 3.13 + psutil 7.1.0 + jinja2 3.1.6; `requirements-local-lock.txt`) runs the harness;
`.venv-scoring` (Python 3.14.4, exact `scoring/requirements-lock.txt`) renders prompts and scores.
Outputs: `local/runs/<run_id>/` (git-ignored).

```
local\.venv\Scripts\python.exe local\test_local.py
python local\fetch_models.py --all
bash local/calibrate_all.sh
local\.venv\Scripts\python.exe local\analyze_calibration.py local\runs\calibration-20261002
.venv-scoring\Scripts\python.exe local\score_local.py local\runs\calibration-20261002
```

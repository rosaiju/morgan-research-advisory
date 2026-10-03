# Stage 1 v2 — reproducibility record

Everything another researcher needs to rerun Stage 1 v2 and get the same inputs, the same configuration and the
same scoring. Facts verified on 2026-10-03. Where a value lives in a frozen file, that file is authoritative; this
page only points to it. Nothing here changes the methodology.

## 1. Freeze

| | |
|---|---|
| Freeze record | `local/items/stage1_v2_freeze.json` (SHA-256 of 31 files + 8 probe records + 7 GGUFs + app grader + Docker sandbox) |
| Previous freezes | `local/items/history/` (each new record links its predecessor under `previous_freeze`) |
| Check | `local\.venv\Scripts\python.exe local\preflight.py [--full-hash]`; any changed frozen file fails preflight |
| Re-freeze | `local\.venv\Scripts\python.exe local\freeze_stage1.py` (archives the old record first) |

## 2. Hardware and system (the machine the timings come from)

| | |
|---|---|
| GPU | NVIDIA GeForce RTX 4060, 8 GB (8,188 MiB), VBIOS 95.07.36.40.2c, driver 591.86 (driver CUDA 13.1) |
| CPU | Intel Core i7-14700F, 20 cores / 28 threads |
| RAM | 32 GB (2 × 16 GB DDR5 @ 4400 MT/s) |
| Disk | Kingston SNV3S1000G NVMe SSD (models in `C:\llm\models`) |
| OS | Windows 11 Home 10.0.26200; power plan Balanced, AC sleep = never; the runner also requests "system required" while it runs |
| Docker | Docker Desktop, Engine 28.5.1, linux/amd64 (WSL2 kernel 6.6.87.2) — scoring of the programming item only |

Speeds are hardware-specific. Other hardware reproduces the *outputs* (same weights, seeds, settings) only up to
GPU/CPU floating-point nondeterminism; it does not reproduce the timings.

## 3. Inference backend

| | |
|---|---|
| llama.cpp | build b11349, commit `fb4b2737a` (`llama-server --version`: 0.5.0-dev, Clang 20.1.8, Windows x86_64) |
| Binaries | `llama-b11349-bin-win-cuda-12.4-x64.zip` SHA-256 `1084a0a4…eaf14`; `cudart-llama-bin-win-cuda-12.4-x64.zip` SHA-256 `8c79a9b2…1d6` (full hashes in `config_local.json` → `backend`) |
| CUDA runtime | 12.4 (bundled cudart), running on driver CUDA 13.1 |
| Common flags | `config_local.json` → `backend.common_server_args`: `--jinja -np 1 -fa on -ctk q8_0 -ctv q8_0 --fit on -fitt 1024 --load-mode none -cram 0 --reasoning-format deepseek --reasoning-budget <6144> --no-context-shift --metrics --host 127.0.0.1 -lv 4` |
| Threads | `-t 8` (P-core count; llama-bench evidence in `runs/threads_r1-0528-qwen3-8b.json`) |
| Not used | speculative decoding, MTP, vision projectors, prompt cache, context shift |

## 4. Models

Exact GGUFs: `local/gguf_pins.json` (repo, revision, file, size, SHA-256); all Q4_K_M except gpt-oss-20b (native
MXFP4). Source checkpoints with revisions, chat-template kwargs, sampling values and their published sources:
`local/config_local.json` → `models`. Official publisher templates and tokenizer configs at pinned revisions:
`local/official/` (`official-lock.json`).

| Model (Stage 1 order) | Reasoning setting | Sampling (T / top_p / top_k / min_p) | Forcing |
|---|---|---|---|
| R1-0528-Qwen3-8B | always on | 0.6 / 0.95 / 0 / 0 | server |
| gpt-oss-20b | `reasoning_effort: high` | 1.0 / 1.0 / 0 / 0 | server |
| GLM-4.7-Flash | `enable_thinking: true` | 1.0 / 0.95 / 0 / 0 | server |
| Ministral-3-14B-Reasoning | always on | 1.0 / 1.0 / 0 / 0 | server |
| Muse-Glimmer-30B | `reasoning_strength: xhigh` | 1.0 / 0.95 / 64 / 0 | harness two-phase |
| Qwen3.8-27B | `enable_thinking: true, reasoning_effort: xhigh` | 1.0 / 0.95 / 20 / 0 | server |
| Gemma-4-31B-it | `enable_thinking: true` | 1.0 / 0.95 / 64 / 0 | server |

Every other sampler is set explicitly to neutral (`common_request`); seeds: `int(sha256("Morgan-2026-09-29|"+item_id)[:8],16) & 0x7fffffff`,
identical across models. One user message, no study system prompt.

## 5. Budget, context, placement, watchdog

| | |
|---|---|
| Budget | 6,144 reasoning + 1,536 final-answer tokens; `max_tokens` 7,808 (+128 for the injected message/delimiters) |
| Forcing message | `config_local.json` → `stage1_v2.budget_message` ("Time is up. I must stop thinking now and give my final answer in the required format.") |
| Server forcing | `--reasoning-budget 6144 --reasoning-budget-message <msg>`; the harness stops an answer > 1,536 tokens (`answer_allowance_exceeded`) |
| Harness forcing (Muse) | phase 1 streams until 6,144 reasoning tokens; phase 2 continues from the official-template rendering of that reasoning + message with `n_predict` 1,536 |
| Context | `n_ctx` 10,496 for every model (from the probe records: `max_tokens` + longest v2 prompt in that tokenizer + 1,024, rounded up to 256) |
| Placement | taken verbatim from the frozen probe record of each model (`runs/probe-20261003/probe_<m>.json` → `placement.args`, hashed in the freeze); see table below |
| Watchdog | first token 1,800 s; stall 600 s; total per attempt `1.5 × 7,808 / max(0.5, 0.8 × probe tok/s at 8K depth) + 1,800` s (R1 2,170 · gpt-oss 2,161 · GLM 2,282 · Ministral 2,938 · Muse 5,855 · Qwen3.8 6,250 · Gemma 7,656). *Note:* `config_local.json` → `watchdog.total_s_rule` still describes the earlier calibration-p10 wording; the code (`run_local.run_items`) and these numbers are what Stage 1 v2 uses. |
| Loop stop | 12-token n-gram ≥ 20 times in the last 2,048 tokens, checked every 64 tokens → `loop_terminated` |
| Reruns | an infrastructure failure (transport error, harness exception, first-token/stall/total timeout) is rerun identically up to 2 times; the 3rd attempt is final whatever happens; the count survives resumes |

| Model | Placement args (frozen) | Note |
|---|---|---|
| R1-8B | `-ngl 999` | everything on GPU |
| gpt-oss-20b | *(none: `--fit on` places experts)* | MoE: `--fit` chooses the CPU/GPU expert split at load time from free VRAM (1 GiB margin). The split actually used is logged per load (`server_ready` records + server logs). |
| GLM-4.7-Flash | *(none: `--fit on`)* | as gpt-oss. Observed 2026-10-03: probe 5,674 MiB of weights on GPU, endurance rotation 5,571 MiB (free VRAM differed); gpt-oss matched its probe exactly (5,691 MiB). Speed was unaffected (33.8 vs 34.4 tok/s fresh). Placement changes only *where* experts run, not the model, but CPU and GPU kernels can differ in the last bits, so a token-identical rerun of GLM is not guaranteed. |
| Ministral 14B | `-ngl 999 -ot blk.(0–17).ffn_(up\|down\|gate).*=CPU` | FFN of 18/40 layers on CPU |
| Muse 30B | `-ngl 999 -ot blk.(0–44).ffn_…=CPU` | FFN of 45/52 layers on CPU |
| Qwen3.8-27B | `-ngl 55 -ot blk.(0–63).ffn_…=CPU` | all FFN on CPU; 55 of 65 offloadable layers on GPU (10 whole layers on CPU) |
| Gemma-4-31B | `-ngl 41 -ot blk.(0–59).ffn_…=CPU` | all FFN on CPU; 41 of 61 offloadable layers on GPU (20 whole layers on CPU) |

## 6. Items, prompts, answer keys

| | |
|---|---|
| Panel | `local/items/stage1_panel_v2.json` (22 items, same for every model; lock `stage1_v2_lock.json`, derived from locked v1 `stage1_panel.json`) |
| Composition | IFEval 6 · student suite 6 · MMLU-Pro 5 · MATH-500 3 · BBEH-mini 2 |
| Order | per model, `random.Random("20260929|stage1-v2|<model>").shuffle(panel)` |
| Prompts | `local/items/rendered_prompts.json` (lock `rendered_lock.json`) |
| Answer keys | `manifest/items/answer_key_final.json`, `answer_key_dev.json` (git-ignored; hashes in `item_manifest_lock.json`) |
| Separation | no Stage 1 item is a calibration item (id and content hash) or a probe item (preflight checks both); the endurance test refuses Stage 1 items |
| Student suite | external repo `C:\Users\rohan\open-source-ai-model` @ `3c415c4a`; `app/evaluation/graders.py` and `suite.py` hashed in the freeze |

## 7. Software environments

| Environment | Use | Lock |
|---|---|---|
| `local/.venv` | harness (generation, preflight, endurance) — Python 3.13.7 | `local/requirements-local-lock.txt` (Jinja2 3.1.6, MarkupSafe 3.0.3, psutil 7.1.0) |
| `.venv-scoring` | prompt rendering and scoring — Python 3.14.4 | `scoring/requirements-lock.txt`; vendored scorer code `scoring/vendor/vendor-lock.json` |

## 8. Scoring

`.venv-scoring\Scripts\python.exe local\score_local.py local\runs\stage1-v2` → `scored.jsonl` (one row per attempt;
analyse the row with `final_attempt: true` per model × item). Status precedence: `local/score_local.py` docstring
(morgan 16 §4 + local additions). Only the final channel is scored. Forced items carry `forced_conclusion`.
Scoring is deterministic (checked by the endurance step `score_twice`: two independent scorings of the same run must be byte-identical) and can be rerun
any time without touching generation results.

**Programming item (`student/prog_word_count`)** — executed only inside Docker (`scoring/docker_code.py`), never on
the host. Same harness, report parsing and partial credit as the app's `_check_code`; 15 s limit.

| Sandbox control | Value |
|---|---|
| Image | `python@sha256:0741d101873c12ab927e6f8653feb8862b9bd58771177acb1b885b95141f91b4` (`python:3.14-slim`, linux/amd64; Python 3.14.8); `--pull never` |
| Network | `--network none` (loopback only) |
| Filesystem | `--read-only` root; writable only `/tmp` (16 MiB) and `/out` (4 MiB) tmpfs, both `noexec,nosuid,nodev`; no host mounts; no Docker socket |
| Identity | `--user 65534:65534`, `--cap-drop ALL`, `--security-opt no-new-privileges`, `--ipc none` |
| Resources | `--memory 256m --memory-swap 256m`, `--cpus 1`, `--pids-limit 32`, `nproc 32`, `nofile 64` |
| Time | in-container `timeout -k 2 15`; host backstop +60 s removes the container and raises |
| Output | stdout capped at 1 MiB, stderr at 64 KiB |
| Failure handling | daemon down / image missing / sandbox hang → `SandboxError`; scoring stops, nothing is recorded as a wrong answer |

Setup on a new machine: install Docker Desktop, then `docker pull python@sha256:0741d101873c12ab927e6f8653feb8862b9bd58771177acb1b885b95141f91b4`.

## 9. Telemetry

`local/telemetry.py`: 1 s samples of nvidia-smi (memory used/total, utilisation, temperature, SM clock, power,
throttle reasons) and psutil (system RAM in use; llama-server RSS and private bytes) to
`runs/stage1-v2/telemetry_<model>.jsonl`. GPU memory is the device total (includes the Windows desktop). Each
attempt record carries prompt/completion/reasoning/final token counts, wall time, TTFT, client and server tok/s.

## 10. Running, resuming, status

```
# Git Bash, from C:/Users/rohan/morgan-research-advisory
# launch (only after the user has written local/STAGE1_APPROVED.json); append-mode log so resumes keep history
"/c/Program Files/Git/bin/bash.exe" -c "local/.venv/Scripts/python.exe local/run_local.py stage1 >> local/runs/stage1_v2.log 2>&1" &
# status
tail -5 local/runs/stage1_v2.log
# resume after any interruption (reboot, crash, kill): run the same launch command again
# score (after generation finishes; Docker Desktop running)
.venv-scoring/Scripts/python.exe local/score_local.py local/runs/stage1-v2
```

Resume semantics: items with a recorded final attempt are skipped; attempt numbers and the 3-attempt cap continue;
a torn last line from a crash is ignored and the next record starts on a fresh line; an orphaned llama-server left
by a killed runner is removed before the next start; only one runner may hold the port lock at a time.

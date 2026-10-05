# Morgan GPU server — Stage 2 handoff (Qwen3.8-27B and Gemma 4 31B)

**For:** Dr. Wang, or whoever provides GPU access. **From:** Rohan Sainju (rosai2@morgan.edu).
**What we need:** one NVIDIA GPU for about one week (realistic estimate; see section 6) to generate answers from two
open-weight language models on a fixed, pre-registered question set. No internet access is needed during the run;
nothing is sent anywhere. No training, no paid APIs. Scoring happens later on our own machine.

## 1. What the server will do

Run `llama.cpp`'s `llama-server` on 127.0.0.1, load one model at a time, and ask it 284 fixed questions (the Stage 2
panel), one at a time, writing every raw response to a JSONL file. The same frozen harness already completed
Stage 1 locally (154/154 items, no infrastructure failures). The third finalist (gpt-oss-20b) runs on our local machine
with the identical harness, panel, prompts and budget.

## 2. Information we need from Morgan before anything is run (please fill in)

| Needed | Why |
|---|---|
| GPU model(s) and VRAM per GPU; how many GPUs we may use | placement (whole model on GPU needs about 18–22 GB free; less works with CPU offload, much slower) |
| NVIDIA driver version and CUDA toolkit version (`nvidia-smi`, `nvcc --version`) | building llama.cpp with CUDA |
| CPU model / cores, system RAM | CPU offload if the GPU is smaller than ~24 GB |
| OS / distribution; do we have a compiler (gcc/g++ ≥ 11), cmake ≥ 3.21, git, Python ≥ 3.10 | build and harness |
| Free disk space for us (need ≥ 60 GB: 37 GB of model files + build + outputs) | model files |
| Can the server download from huggingface.co and github.com once (setup only)? If not, we bring the files | setup |
| Scheduler/policy: interactive shell, `tmux`/`screen`/`nohup` allowed, or a batch system (Slurm etc.)? Maximum job length? | the run is ~5–7 days per model and is resumable if interrupted |
| Is the GPU shared with other jobs during our run? | speed and memory stability; we record it |
| Any port restrictions on 127.0.0.1 (we use 8181; configurable) | local server |

## 3. Exact experiment (frozen; must not be changed on the server)

| Item | Value |
|---|---|
| Inference engine | llama.cpp commit `fb4b2737a` (build b11349), CUDA build, `llama-server` + `llama-fit-params` |
| Qwen3.8-27B | GGUF `bartowski/Qwen3.8-27B-GGUF` rev `0c92138c51f112d2f0dc84d5f6d1ebe4b9912b9a`, file `Qwen3.8-27B-Q4_K_M.gguf`, 17,442,399,968 bytes, SHA-256 `880a52af8317974f7b4b064a6bc29ff49e188b91aa218e08eea3078b6b1cc673`; from checkpoint `Qwen/Qwen3.8-27B@1d4bf0f2…`; `enable_thinking: true, reasoning_effort: xhigh`; T 1.0, top_p 0.95, top_k 20, min_p 0 |
| Gemma 4 31B | GGUF `bartowski/google_gemma-4-31B-it-GGUF` rev `619aca7589c72be65dd968de8602ad23d68b5c14`, file `google_gemma-4-31B-it-Q4_K_M.gguf`, 19,598,489,952 bytes, SHA-256 `2959c1b0a4f792493bb0092846ea06aec54547e47be979c282634d938d501b75`; from checkpoint `google/gemma-4-31B-it@842da379…`; `enable_thinking: true`; T 1.0, top_p 0.95, top_k 64, min_p 0 |
| Quantization | Q4_K_M for both (identical to Stage 1, even if the server could hold higher precision); KV cache q8_0 |
| Chat templates | the publishers' official templates, shipped in the bundle (`local/official/`, hash-locked) |
| Prompts | `local/stage2/items/stage2_rendered.json` (284 items + 2 development probe items; hash-locked) |
| Budget | 16,384 reasoning tokens + 2,048 answer tokens (`max_tokens` 18,560); at the reasoning budget the server injects "Time is up. I must stop thinking now and give my final answer in the required format." |
| Context | ≈ 23–24K tokens (computed per model by the probe) |
| Other sampling | every other sampler neutral and explicit; seed per item from the item id (same for all models); prompt cache off; one request at a time |
| Server flags | `local/config_local.json` → `backend.common_server_args` (identical to Stage 1) |
| Placement | the approved rule (attention + KV on GPU first) computed on the server's GPU by the probe and then frozen |
| Retries | infrastructure failures rerun identically up to 2 times; the run resumes after any interruption without repeating finished items |

## 4. Setup on the server (Linux shell)

```bash
# 0. unpack the bundle we send (morgan-stage2-bundle.tar.gz) and check it
tar xzf morgan-stage2-bundle.tar.gz && cd morgan-stage2 && sha256sum -c SHA256SUMS.txt

# 1. build llama.cpp at the frozen commit (CUDA)
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp && git checkout fb4b2737a
cmake -B build -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j --target llama-server llama-fit-params
./build/bin/llama-server --version          # must show fb4b2737a
cd ..

# 2. Python environment for the harness (no ML libraries needed)
python3 -m venv .venv && .venv/bin/pip install -r local/requirements-local-lock.txt

# 3. model files (or copy them from us), then verify
export MODELS=$PWD/models && mkdir -p $MODELS
curl -L -o $MODELS/Qwen3.8-27B-Q4_K_M.gguf \
  https://huggingface.co/bartowski/Qwen3.8-27B-GGUF/resolve/0c92138c51f112d2f0dc84d5f6d1ebe4b9912b9a/Qwen3.8-27B-Q4_K_M.gguf
curl -L -o $MODELS/google_gemma-4-31B-it-Q4_K_M.gguf \
  https://huggingface.co/bartowski/google_gemma-4-31B-it-GGUF/resolve/619aca7589c72be65dd968de8602ad23d68b5c14/google_gemma-4-31B-it-Q4_K_M.gguf
(cd $MODELS && sha256sum -c ../local/stage2/MODELS.sha256)

# 4. environment for every following command (pick ONE GPU)
export MORGAN_HOST=morgan-gpu MORGAN_LLAMA_DIR=$PWD/llama.cpp/build/bin MORGAN_MODEL_DIR=$MODELS
export CUDA_VISIBLE_DEVICES=0 MORGAN_GPU_INDEX=0     # the same physical GPU in both
```

## 5. Run order

```bash
# A. offline tests and preflight (expect only "probe", "freeze" and "approval" to fail at this point)
.venv/bin/python local/stage2/test_stage2.py
.venv/bin/python local/stage2/preflight_stage2.py

# B. development probe (NOT the evaluation; development items only; ~2-6 h depending on the GPU)
mkdir -p local/runs/stage2-probe-morgan-gpu
nohup .venv/bin/python local/stage2/probe_stage2.py qwen3.8-27b gemma-4-31b >> local/runs/stage2-probe-morgan-gpu/probe.log 2>&1 &

# C. freeze, then SEND US: local/stage2/items/stage2_freeze_morgan-gpu.json + local/runs/stage2-probe-morgan-gpu/
.venv/bin/python local/stage2/freeze_stage2.py

# D. WAIT for Rohan's approval file local/stage2/STAGE2_APPROVED_morgan-gpu.json (it contains the freeze hash).
#    Without it the runner refuses. Then:
.venv/bin/python local/stage2/run_stage2.py --dry-run
nohup .venv/bin/python local/stage2/run_stage2.py >> local/runs/stage2_morgan.log 2>&1 &

# status at any time
tail -5 local/runs/stage2_morgan.log
# resume after ANY interruption (reboot, job limit, crash): first make sure no old server is left, then rerun D
pkill -f "llama-server.*--port 8181" ; nohup .venv/bin/python local/stage2/run_stage2.py >> local/runs/stage2_morgan.log 2>&1 &

# E. when finished, SEND US the whole output directory
tar czf stage2-morgan-gpu-results.tar.gz local/runs/stage2-morgan-gpu local/runs/stage2-probe-morgan-gpu local/runs/stage2_morgan.log
```

## 6. Expected duration (projection from Stage 1 data; replaced by the probe's measured speeds)

On our 8 GB laptop GPU (heavy CPU offload): Qwen3.8 ~122 h, Gemma ~167 h (realistic). On a GPU that holds the whole
model (≥ 24 GB), generation is typically several times faster; the probe measures the real number before the run.

## 7. Output format

`local/runs/stage2-morgan-gpu/attempts_<model>.jsonl`: one JSON object per line: `server_start`/`server_ready`
records, then one `item` record per attempt with `item_id`, `benchmark`, `attempt`, `final_attempt`, seed, token counts,
timings, `finish_reason`, `abort`, `error`, full `reasoning_text` and `final_text`. Also `telemetry_<model>.jsonl`
(1 s GPU/RAM samples), `server_<model>_*.log` (llama.cpp load logs), `RUN_INFO.json` (host facts, freeze hash).
No answer keys are on the server; scoring is done afterwards on our machine with the frozen scorer.

## 8. Notes for the operator

- Only one runner may use the port at a time (a lock file enforces it). Do not start two runs.
- If the GPU is shared, please tell us; it changes speed but not results.
- Nothing in the bundle needs root, and nothing listens on a public interface.

# Morgan GPU computer — Stage 2 handoff (Qwen3.8-27B and Gemma 4 31B)

**Revised 2026-10-08** (supersedes the 2026-10-05 version; same experiment, corrected and completed instructions).
**Approval to move the runs:** Dr. Wang approved running the remaining Stage 2 evaluations on a Morgan computer
(reported by Rohan Sainju, 2026-10-08). **Expected hardware:** possibly an NVIDIA RTX 4500 Ada (24 GB); hardware and
operating system **not yet confirmed**. **From:** Rohan Sainju (rosai2@morgan.edu).

Nothing in this file changes the frozen experiment. Section 3 is unchanged from 2026-10-05.

What changed on 2026-10-08:
- Added a Windows route that uses the identical llama.cpp release binaries already used for Stage 1 and gpt-oss.
- Linux: llama.cpp must be built from a **git clone**, because preflight checks the commit hash in `--version`.
- Resuming now uses `resume_stage2.py`. `run_stage2.py` refuses to resume once its own attempts exist; see section 5.
- Backup, checksum and return steps are written out.
- The bundle checksum file is now LF-only, so `sha256sum -c` works on Linux.
- Python wheels are provided for an offline install.

## 1. What the computer will do

Run `llama.cpp`'s `llama-server` on 127.0.0.1, load one model at a time, and send it 284 fixed questions (the Stage 2
panel), one at a time. Every raw response is written to a JSONL file. The same frozen harness completed Stage 1 locally
and the official gpt-oss-20b Stage 2 run (284/284 items, all on the first attempt). Answer keys are not needed on the
Morgan computer and must not be copied there; scoring is done afterwards on the home machine.

## 2. Check first on the Morgan computer (≈ 5 minutes, nothing is run)

| Check | Command (Linux / Windows PowerShell) | Need |
|---|---|---|
| GPU, VRAM, driver | `nvidia-smi` | note GPU name, memory, driver, "CUDA Version" (≥ 12.4 for the Windows binaries) |
| Is the GPU busy? | `nvidia-smi` process list | ideally idle; if it is shared, record that |
| OS | `cat /etc/os-release` / `winver` | decides the route in section 4 |
| CPU / RAM | `lscpu; free -g` / `Get-CimInstance Win32_Processor,Win32_ComputerSystem` | RAM ≥ 32 GB if a model must partly use the CPU |
| Disk | `df -h .` / `Get-PSDrive` | ≥ 60 GB free (37 GB models + build + outputs) |
| Python | `python3 --version` / `py -0` | 3.10–3.13 (home: 3.13.7) |
| Linux build tools | `git --version; cmake --version; gcc --version; nvcc --version` | git, cmake ≥ 3.21, gcc ≥ 11, CUDA toolkit (nvcc) ≥ 12.0 |
| Network | `curl -sI https://huggingface.co` | if blocked, bring the models on a drive (see the handoff's START_HERE.md) |
| Policy | ask the lab | may a job run for 2–3+ days? Will the machine reboot, sleep or log you off? `tmux` allowed? |

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

Host name for every command: `MORGAN_HOST=morgan-gpu` (already in `config_stage2.json`; do not edit that file — it
is hashed in the freeze). Its outputs go to separate directories: `local/runs/stage2-probe-morgan-gpu/` and
`local/runs/stage2-morgan-gpu/`. CPU threads stay at the frozen 8 (`config_local.json`).

## 4. Setup

### 4a. Unpack and verify the bundle (both systems)

```bash
# Linux
mkdir -p ~/morgan && cd ~/morgan && tar xzf /path/to/morgan-stage2-bundle.tar.gz && cd morgan-stage2
sha256sum -c SHA256SUMS.txt                 # every line must say OK
```
```powershell
# Windows (PowerShell; tar.exe ships with Windows 10/11)
mkdir C:\morgan; cd C:\morgan; tar -xzf <path>\morgan-stage2-bundle.tar.gz; cd morgan-stage2
Get-Content SHA256SUMS.txt | % { $h,$f = $_ -split '  ',2; if ((Get-FileHash $f -A SHA256).Hash.ToLower() -ne $h) { "MISMATCH $f" } }   # no output = all match
```

### 4b. llama.cpp b11349 / `fb4b2737a`

**Windows. Preferred, because these are the identical binaries used for Stage 1 and gpt-oss.** Download both zips
and check their SHA-256 values; the values are also in `config_local.json` → `backend`. Then unpack both zips into
one folder.
```powershell
mkdir C:\llm\llama.cpp\b11349 -Force; cd C:\llm\llama.cpp
curl.exe -L -O https://github.com/ggml-org/llama.cpp/releases/download/b11349/llama-b11349-bin-win-cuda-12.4-x64.zip
curl.exe -L -O https://github.com/ggml-org/llama.cpp/releases/download/b11349/cudart-llama-bin-win-cuda-12.4-x64.zip
(Get-FileHash llama-b11349-bin-win-cuda-12.4-x64.zip).Hash   # 1084A0A4C6567511C7F67D8C4DB71979F837170ED22B2FCB72C0D8637A4EAF14
(Get-FileHash cudart-llama-bin-win-cuda-12.4-x64.zip).Hash   # 8C79A9B226DE4B3CACFD1F83D24F962D0773BE79F1E7B75C6AF4DED7E32AE1D6
tar -xf llama-b11349-bin-win-cuda-12.4-x64.zip -C b11349; tar -xf cudart-llama-bin-win-cuda-12.4-x64.zip -C b11349
.\b11349\llama-server.exe --version          # must show: build 11349, commit fb4b2737a
```

**Linux. Build from source.** No official Linux CUDA binary was used, so this route has not been run for this
project yet.
```bash
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp
git checkout fb4b2737a808a3fb7c2117a498f43815dc9be53e      # = tag b11349 (verified against GitHub 2026-10-08)
# must be a git clone (NOT a source tarball): --version reports the commit from git, and preflight checks it
cmake -B build -DGGML_CUDA=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_ARCHITECTURES=89   # 89 = Ada (RTX 4500 Ada); use the real GPU's value
cmake --build build --config Release -j --target llama-server llama-fit-params
./build/bin/llama-server --version          # must show: build 11349, commit fb4b2737a
cd ..
```
If cmake stops on a missing optional dependency, such as CURL, add `-DLLAMA_CURL=OFF`. Model download through
llama.cpp is not used. **[Check on Morgan's computer]**

### 4c. Python environment for the harness (no ML libraries)

```bash
python3 -m venv .venv && .venv/bin/pip install -r local/requirements-local-lock.txt
# offline: .venv/bin/pip install --no-index --find-links <handoff>/python-wheels/linux-py3XX -r local/requirements-local-lock.txt
```
```powershell
py -3.13 -m venv .venv; .\.venv\Scripts\pip install -r local\requirements-local-lock.txt
# offline: add  --no-index --find-links <handoff>\python-wheels\win-py313
```

### 4d. Model files (37.0 GB; download at Morgan, or copy from a drive), then verify

```bash
export MODELS=$PWD/models && mkdir -p $MODELS
curl -L -C - -o $MODELS/Qwen3.8-27B-Q4_K_M.gguf \
  https://huggingface.co/bartowski/Qwen3.8-27B-GGUF/resolve/0c92138c51f112d2f0dc84d5f6d1ebe4b9912b9a/Qwen3.8-27B-Q4_K_M.gguf
curl -L -C - -o $MODELS/google_gemma-4-31B-it-Q4_K_M.gguf \
  https://huggingface.co/bartowski/google_gemma-4-31B-it-GGUF/resolve/619aca7589c72be65dd968de8602ad23d68b5c14/google_gemma-4-31B-it-Q4_K_M.gguf
(cd $MODELS && sha256sum -c ../local/stage2/MODELS.sha256)
```
```powershell
mkdir C:\llm\models -Force; cd C:\llm\models
curl.exe -L -C - -O https://huggingface.co/bartowski/Qwen3.8-27B-GGUF/resolve/0c92138c51f112d2f0dc84d5f6d1ebe4b9912b9a/Qwen3.8-27B-Q4_K_M.gguf
curl.exe -L -C - -O https://huggingface.co/bartowski/google_gemma-4-31B-it-GGUF/resolve/619aca7589c72be65dd968de8602ad23d68b5c14/google_gemma-4-31B-it-Q4_K_M.gguf
Get-FileHash *.gguf -A SHA256        # compare with local\stage2\MODELS.sha256
```
On 2026-10-08 both URLs answered without a login, with exactly the pinned byte sizes. `-C -` resumes a broken
download. Preflight also re-checks size and hash.

### 4e. Environment for every following command (one GPU only)

```bash
export MORGAN_HOST=morgan-gpu MORGAN_LLAMA_DIR=$PWD/llama.cpp/build/bin MORGAN_MODEL_DIR=$MODELS
export CUDA_VISIBLE_DEVICES=0 MORGAN_GPU_INDEX=0     # the same physical GPU in both
```
```powershell
$env:MORGAN_HOST="morgan-gpu"; $env:MORGAN_LLAMA_DIR="C:\llm\llama.cpp\b11349"; $env:MORGAN_MODEL_DIR="C:\llm\models"
$env:CUDA_VISIBLE_DEVICES="0"; $env:MORGAN_GPU_INDEX="0"
```
Below, `PY` means `.venv/bin/python` (Linux) or `.\.venv\Scripts\python.exe` (Windows). Run every command from
the `morgan-stage2` folder.

## 5. Run order

```bash
# A. offline tests + preflight (≈ 1 min). Expected at this point: 15/19, failing ONLY the two "Stage 2 probe passed"
#    checks, "freeze record" and "approval" (verified on the unpacked bundle 2026-10-08). Run B-E inside tmux on Linux.
PY local/stage2/test_stage2.py
PY local/stage2/preflight_stage2.py --full-hash        # --full-hash re-hashes both GGUFs (a few minutes)

# B. DEVELOPMENT-ONLY GPU/speed check = the Stage 2 probe. It uses the 2 development items only and NO Stage 2 item.
#    It records: placement on this GPU, n_ctx, load VRAM/RAM, integration checks, speed fresh / 8K / 16K deep, one forced
#    conclusion at 16,384 + 2,048 and one natural item. Estimate on a 24 GB GPU: about 0.5–1 h per model.
mkdir -p local/runs/stage2-probe-morgan-gpu
PY local/stage2/probe_stage2.py qwen3.8-27b gemma-4-31b 2>&1 | tee -a local/runs/stage2-probe-morgan-gpu/probe.log
#    Look at: probe_<model>.json -> placement, speed_deep_16k.tg_tok_s_at_depth, forced_conclusion_ok, integration.passed
#    A failed model leaves probe_<model>.FAILED.txt; fix the cause, then rerun B (finished models are skipped).

# C. freeze (prints the freeze SHA-256)
PY local/stage2/freeze_stage2.py

# D. APPROVAL by Rohan only, after reviewing the probe: create local/stage2/STAGE2_APPROVED_morgan-gpu.json
#    (template in section 9; it must contain the freeze SHA-256 from C). Without it the runner refuses.
PY local/stage2/run_stage2.py --dry-run                 # expect 0 blocking failures and "qwen3.8-27b (284 items), gemma-4-31b (284 items)"

# E. FIRST official launch (runs Qwen, then Gemma, in one process)
#    Linux: inside tmux (tmux new -s stage2) so logging out does not stop it
PY local/stage2/run_stage2.py >> local/runs/stage2_morgan.log 2>&1
#    Windows: survives closing the window (not logging off); one log file per launch because Start-Process overwrites
#    Start-Process -FilePath .\.venv\Scripts\python.exe -ArgumentList "local\stage2\run_stage2.py" -WindowStyle Hidden `
#      -RedirectStandardOutput local\runs\stage2_morgan_1.log -RedirectStandardError local\runs\stage2_morgan_1.err

# status at any time
tail -5 local/runs/stage2_morgan.log                    # Windows: Get-Content local\runs\stage2_morgan_1.log -Tail 5
grep -c '"final_attempt": true' local/runs/stage2-morgan-gpu/attempts_qwen3.8-27b.jsonl   # items finished (of 284)

# F. RESUME after ANY interruption (reboot, logoff, crash, job limit) — or to start Gemma separately after Qwen.
#    Do NOT rerun run_stage2.py: its pre-run freshness check fails once its own attempts exist (by construction).
#    resume_stage2.py runs the same gate/loop with only that check re-done excluding this host's own Stage 2 outputs.
pkill -f "llama-server.*--port 8181"                    # Linux only (Windows: the harness reaps its own orphans)
PY local/stage2/resume_stage2.py --dry-run              # expect 0 blocking failures; prints items still to generate
PY local/stage2/resume_stage2.py >> local/runs/stage2_morgan.log 2>&1      # (Windows: Start-Process as in E, new log name)
```

**Backups while it runs.** Copy the run folder outside `local/runs`, for example once a day or before any planned
reboot. Never put a copy inside `local/runs` under any name other than `stage2-morgan-gpu.raw-backup`: any other
copy there counts as a "previous run" and blocks resuming.
```bash
rsync -a local/runs/stage2-morgan-gpu/ ~/stage2-backup/stage2-morgan-gpu/
```
```powershell
robocopy local\runs\stage2-morgan-gpu D:\stage2-backup\stage2-morgan-gpu /E /R:1 /W:1
```

## 6. Expected duration

At home (8 GB GPU, heavy CPU offload) the projection was Qwen3.8 ~122 h and Gemma ~167 h (realistic), with
≈ 1.4M generated tokens per model. On a 24 GB card the speed is limited mainly by memory bandwidth (RTX 4500 Ada:
432 GB/s).

Rough estimate, not measured: Qwen3.8 fits whole on the GPU at about 15–20 tok/s, which is ≈ 1 day. Gemma (19.6 GB
of weights) may need part of its FFN on the CPU, at about 8–14 tok/s, which is ≈ 1.5–2 days. **The probe (step B)
measures the real speed; use its `speed_deep_16k` value.**

## 7. Finishing and returning results

```bash
cd local/runs
sha256sum -b stage2-morgan-gpu/* > stage2-morgan-gpu.SHA256SUMS          # same " *" format as the home manifests
tar czf ../../stage2-morgan-gpu-results.tar.gz stage2-morgan-gpu stage2-probe-morgan-gpu stage2-morgan-gpu.SHA256SUMS stage2_morgan*.log \
    ../stage2/items/stage2_freeze_morgan-gpu.json ../stage2/STAGE2_APPROVED_morgan-gpu.json
```
On Windows, use the same commands in Git Bash, or `tar -czf` in PowerShell. Bring the archive home and unpack it
into the home `local/` folder. Verify it with `sha256sum -c` from `local/runs`, then score at home only:
`.venv-scoring\Scripts\python.exe local\score_local.py local\runs\stage2-morgan-gpu`. Scoring uses the answer
keys and a Docker sandbox for the programming items, so it does not run on the Morgan computer.

## 8. Policy B forced-item reruns (later; not part of today)

Policy B is binding for Qwen3.8 and Gemma too (`FORCED_RERUN_POLICY.json`). After each model's generation is
complete, its forced items get selected with the pre-registered seed, and up to 20 are rerun at 24,576 tokens as a
sensitivity analysis only.

`run_forced_rerun.py` currently accepts only the committed gpt-oss selection. It also checks that the selection file
is committed in git, and the bundle is not a git checkout. Running Policy B on `morgan-gpu` therefore needs a small,
reviewed addition: the selection hash and a non-git check. That change and the user's approval come before any
rerun. Nothing about it changes the official runs.

## 9. Approval template (Rohan writes this; never generated automatically)

```json
{
 "approval": "I approve proceeding with the official Stage 2 Qwen3.8-27B and Gemma 4 31B runs on the Morgan GPU computer.",
 "approved_by": "Rohan Sainju (rosai2@morgan.edu)",
 "approved_at": "<UTC time>",
 "host": "morgan-gpu",
 "freeze_record": "local/stage2/items/stage2_freeze_morgan-gpu.json",
 "freeze_sha256": "<the SHA-256 printed by freeze_stage2.py>",
 "forced_rerun_policy": "local/stage2/FORCED_RERUN_POLICY.json (Policy B, committed 6a0602e before generation)",
 "scope": {"models": ["qwen3.8-27b", "gemma-4-31b"], "items": 284, "thinking_budget": 16384, "answer_allowance": 2048,
           "placement": "frozen Stage 2 probe placement on morgan-gpu"},
 "conditions": [
  "no changes to benchmark, prompts, model settings, token budget, scorer, frozen files or methodology",
  "no scoring or analysis of partial results; no forced-item reruns before the user approves them",
  "recoverable infrastructure stops: resume only with local/stage2/resume_stage2.py (same plan, same settings)"
 ]
}
```

## 10. Notes for the operator

- Only one runner may use port 8181 at a time; a lock file enforces this. Do not start two runs.
- If the GPU is shared, record that. It changes speed but not results.
- Nothing needs root or administrator rights. Nothing listens on a public interface.
- Linux: the harness's automatic cleanup of a leftover `llama-server` only recognises `llama-server.exe`, so run
  the `pkill` line in step F before every resume. The Windows keep-awake call does nothing on Linux, so make sure
  the machine will not suspend.
- Windows: the runner asks Windows to stay awake while it runs. A logoff, or an update reboot, stops it; resume
  with step F.

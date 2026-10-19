# Stage 2 (morgan-gpu) infrastructure deviations
- 2026-10-14: local/llm_server.py port_in_use(): on non-Windows, set SO_REUSEADDR before the bind test.
  Reason: Linux TIME_WAIT on 127.0.0.1:8181 after the tokenize server stopped made the check refuse to start
  (probe failed twice). Windows path unchanged. No effect on prompts, models, sampling, budgets or scoring.
  Original saved at /data/llm_server.py.orig. Applied before freeze; approved by Rohan Sainju.
- Build: llama.cpp b11349 / fb4b2737a built from git, CUDA 12.4 with gcc-13 host compiler, Python 3.13.16 (uv).
- GPU: RTX 4500 Ada selected with CUDA_DEVICE_ORDER=PCI_BUS_ID, CUDA_VISIBLE_DEVICES=1, MORGAN_GPU_INDEX=1.

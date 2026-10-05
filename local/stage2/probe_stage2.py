"""Stage 2 development probe (NOT Stage 2): validates one finalist on THIS host at the Stage 2 context and budget,
using development items only (local/stage2/items/stage2_probe_items.json; never Stage 2 items).

    MORGAN_HOST=<host> python local/stage2/probe_stage2.py <model> [--skip-long]

Per model, writes local/runs/stage2-probe-<host>/probe_<model>.json (+ attempts, server logs, telemetry):
  0. host facts (GPU, driver/CUDA, CPU, RAM, llama.cpp version) and weight verification
  1. n_ctx = 18,560 + longest Stage 2 prompt in this model's tokenizer (panel + probe items) + 1,024
  2. placement under the approved rule at that context, on this host's GPU
  3. two timed loads with the Stage 2 budget: offload, KV, VRAM and RAM added
  4. integration checks (template fidelity, reasoning setting, sanity question, truncation, token accounting)
  5. speed: pp512/tg128 fresh, tg128 after 8K and after 16K prefilled tokens (context stability at Stage 2 depth)
  6. unless --skip-long: forced conclusion at 16,384 + 2,048 on a development item that ran past 24K unforced
  7. a natural-length development item
Resumable: a model with an existing probe_<model>.json is skipped (delete it to re-probe).
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402  (host setup first)

import psutil  # noqa: E402

import placement  # noqa: E402
import run_local as R  # noqa: E402
from llm_server import CONFIG, PINS, MODEL_DIR, Server  # noqa: E402
from probe_local import depth_probe, fresh_probe  # noqa: E402
from telemetry import Sampler  # noqa: E402

FORCE_ITEM, NATURAL_ITEM = C.PROBE_ITEMS
MARK = "Time is up. I must stop thinking now"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sys_ram_mib() -> float:
    vm = psutil.virtual_memory()
    return round((vm.total - vm.available) / 2**20, 1)


def make_server(model, n_ctx, log, pargs):
    return Server(model, n_ctx, log, threads=C.server_threads(), extra_args=pargs,
                  reasoning_budget=C.CONFIG2["thinking_budget"], budget_message=C.CONFIG2["budget_message"])


def probe(model: str, skip_long: bool) -> None:
    d = C.PROBE_DIR
    d.mkdir(parents=True, exist_ok=True)
    out_path = d / f"probe_{model}.json"
    if out_path.exists():
        print(f"[{model}] already probed on {C.HOST}, skipping", flush=True)
        return
    ok, how = C.weights_ok(model)
    res = {"model": model, "host": C.host_info(), "started": now(), "gguf": PINS[model], "weights_verified": ok,
           "weights_check": how, "config_stage2_sha256": C.sha(C.HERE / "config_stage2.json"),
           "config_local_sha256": C.sha(C.LOCAL / "config_local.json"), "skip_long": skip_long}
    if not ok:
        raise SystemExit(f"{model}: weights not verified ({how})")
    attempts = d / f"attempts_{model}.jsonl"
    kw = CONFIG["models"][model]["chat_template_kwargs"]

    tok = Server(model, 4096, d / f"server_{model}_tokenize.log", threads=C.server_threads())
    tok.start()
    try:
        lens = {iid: len(tok.tokenize(tok.apply_template([{"role": "user", "content": v["text"]}], kw)))
                for iid, v in C.RENDERED2.items()}
    finally:
        tok.stop()
    s2 = C.CONFIG2
    n_ctx = R.round_up(s2["max_tokens"] + max(lens.values()) + 1024)
    longest = max(lens, key=lens.get)
    res.update(n_ctx=n_ctx, prompt_tokens={"max": lens[longest], "max_item": longest,
                                           "mean_panel": round(sum(lens[p["item_id"]] for p in C.PANEL2) / len(C.PANEL2))})
    print(f"[{model}] n_ctx={n_ctx} (longest prompt {lens[longest]} tokens: {longest})", flush=True)

    pargs, pinfo = placement.placement_args(model, MODEL_DIR / PINS[model]["file"], n_ctx)
    res["placement"] = {"args": pargs, **pinfo}
    print(f"[{model}] placement {pinfo}", flush=True)

    loads, srv = [], None
    for i in range(2):
        ram0, vram0 = sys_ram_mib(), C.telemetry.gpu_snapshot()["gpu_mem_used_mib"]
        srv = make_server(model, n_ctx, d / f"server_{model}_load{i + 1}.log", pargs)
        li = srv.start()
        time.sleep(2)
        loads.append({"load_seconds": li.load_seconds, "layers_offloaded": li.layers_offloaded,
                      "gpu_weight_fraction": li.gpu_weight_fraction, "gpu_model_mib": li.gpu_model_mib,
                      "cpu_model_mib": li.cpu_model_mib, "kv_mib": li.kv_mib, "compute_gpu_mib": li.compute_gpu_mib,
                      "n_ctx_reported": li.n_ctx, "sys_ram_added_mib": round(sys_ram_mib() - ram0, 1),
                      "sys_ram_used_mib": sys_ram_mib(),
                      "vram_added_mib": round(C.telemetry.gpu_snapshot()["gpu_mem_used_mib"] - vram0, 1),
                      "vram_used_mib": C.telemetry.gpu_snapshot()["gpu_mem_used_mib"]})
        if i == 0:
            srv.stop()
            time.sleep(3)
    res["loads"] = loads
    print(f"[{model}] loads {loads}", flush=True)
    sampler = Sampler(d / f"telemetry_{model}.jsonl", srv.pid()).start()
    try:
        res["integration"], recs = R.integration(srv, model)
        for r in recs:
            R.append_jsonl(attempts, r)
        print(f"[{model}] integration passed={res['integration']['passed']}", flush=True)
        res["speed_fresh"] = fresh_probe(srv)
        res["speed_deep_8k"] = depth_probe(srv, 8192)
        res["speed_deep_16k"] = depth_probe(srv, 16384)
        res["context_stable_16k"] = bool(res["speed_deep_16k"].get("tg_tok_s_at_depth"))
        print(f"[{model}] fresh {res['speed_fresh']} 8K {res['speed_deep_8k']} 16K {res['speed_deep_16k']}", flush=True)
        items = ([] if skip_long else [FORCE_ITEM]) + [NATURAL_ITEM]
        res["items"] = {}
        for iid in items:
            r = R.run_attempt(srv, model, iid, C.RENDERED2[iid]["text"], s2["max_tokens"], 12 * 3600, "stage2-probe",
                              answer_cap=s2["answer_allowance"])
            r["attempt"], r["final_attempt"], r["benchmark"] = 1, True, C.RENDERED2[iid]["benchmark"]
            R.append_jsonl(attempts, r)
            res["items"][iid] = {k: r.get(k) for k in ("finish_reason", "abort", "error", "completion_tokens",
                                                        "reasoning_tokens", "final_tokens", "wall_s", "client_gen_tok_s")}
            res["items"][iid].update(forced=MARK in (r["reasoning_text"] or ""), final_nonempty=bool(r["final_text"].strip()),
                                     final_tail=r["final_text"][-300:])
            print(f"[{model}] {iid} {res['items'][iid]}", flush=True)
            R.wait_idle(srv)
        if not skip_long:
            f = res["items"][FORCE_ITEM]
            res["forced_conclusion_ok"] = bool(f["final_nonempty"] and (f["forced"] or f["finish_reason"] == "stop")
                                               and (f["reasoning_tokens"] or 0) <= s2["thinking_budget"] + 64)
    except Exception as e:  # noqa: BLE001
        res["error"] = repr(e)
        print(f"[{model}] ERROR {e!r}", flush=True)
    finally:
        res["telemetry"] = sampler.stop()
        srv.stop()
    res["finished"] = now()
    out_path.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[{model}] stage 2 probe done on {C.HOST}", flush=True)


if __name__ == "__main__":
    skip = "--skip-long" in sys.argv
    models = [a for a in sys.argv[1:] if not a.startswith("--")]
    lock = C.llm_server.acquire_runner_lock(f"stage2 probe {C.HOST}")
    C.llm_server.keep_awake(True)
    try:
        for m in models:
            if m not in C.CONFIG2["finalists"]:
                raise SystemExit(f"{m} is not a Stage 2 finalist")
            try:
                probe(m, skip)
            except Exception as e:  # noqa: BLE001  one model failing must not stop the others
                print(f"[{m}] PROBE FAILED {e!r}", flush=True)
                (C.PROBE_DIR / f"probe_{m}.FAILED.txt").write_text(f"{now()} {e!r}\n", encoding="utf-8")
    finally:
        C.llm_server.keep_awake(False)
        C.llm_server.release_runner_lock(lock)

"""Approved short compatibility / speed probe under the Stage 1 v2 configuration (no long development questions).

    python local/probe_local.py <model> [<model> ...]       (run id: $MORGAN_PROBE_ID or probe-20261003)

Per model (writes local/runs/<probe id>/probe_<model>.json + attempts_<model>.jsonl + logs + telemetry):
  1. placement under the approved rule (local/placement.py) at the Stage 1 v2 context
  2. baseline comparison: plain --fit layer split, fresh and 8K-deep decode (dense models only)
  3. three timed loads with the approved placement + 6,144 reasoning budget; offload, KV, VRAM, RAM delta
  4. template fidelity and reasoning-setting render checks; sanity question; 32-token truncation / accounting
  5. speed: pp512 + tg128 fresh (2 reps) and tg128 after an ~8K-token prefilled context
  6. forced-conclusion end-to-end at the real budget (6,144 + 1,536) on one development item known to exceed it
     (math500 geometry/880, development set) and one natural-length development item (ifeval/1012)
A model already probed (probe_<model>.json exists) is skipped, so the job is resumable.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import psutil  # noqa: E402

import placement  # noqa: E402
import run_local as R  # noqa: E402
from llm_server import CONFIG, PINS, MODEL_DIR, Server  # noqa: E402
from telemetry import Sampler, gpu_snapshot  # noqa: E402

S1 = CONFIG["stage1_v2"]
PANEL_V2 = json.loads((HERE / "items/stage1_panel_v2.json").read_text(encoding="utf-8"))
FORCE_ITEM, NATURAL_ITEM = "math500/test/geometry/880.json", "ifeval/1012"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sys_ram_mib() -> float:
    vm = psutil.virtual_memory()
    return round((vm.total - vm.available) / 2**20, 1)


def depth_probe(srv: Server, depth: int = 8192, n_predict: int = 128) -> dict:
    filler = " ".join(["The quick brown fox jumps over the lazy dog near the quiet river bank."] * 1200)
    toks = srv.tokenize(filler)[:depth]
    r = srv.post("/completion", {"prompt": toks, "n_predict": n_predict, "ignore_eos": True, "cache_prompt": False,
                                 "temperature": 1.0, "top_k": 0, "top_p": 1.0, "min_p": 0.0, "seed": 1}, timeout=7200)
    t = r["timings"]
    return {"depth_tokens": len(toks), "prefill_tok_s": round(t["prompt_per_second"], 2),
            "tg_tok_s_at_depth": round(t["predicted_per_second"], 2)}


def fresh_probe(srv: Server, reps: int = 2, n_predict: int = 128) -> dict:
    filler = " ".join(["The quick brown fox jumps over the lazy dog."] * 200)
    toks = srv.tokenize(filler)[:512]
    pp, tg = [], []
    for _ in range(reps):
        r = srv.post("/completion", {"prompt": toks, "n_predict": n_predict, "ignore_eos": True, "cache_prompt": False,
                                     "temperature": 1.0, "top_k": 0, "top_p": 1.0, "min_p": 0.0, "seed": 1}, timeout=7200)
        pp.append(r["timings"]["prompt_per_second"])
        tg.append(r["timings"]["predicted_per_second"])
    return {"pp512_tok_s": round(statistics.median(pp), 2), "tg_fresh_tok_s": round(statistics.median(tg), 2),
            "pp_all": [round(x, 2) for x in pp], "tg_all": [round(x, 2) for x in tg]}


def probe(model: str, run_dir: Path) -> None:
    out_path = run_dir / f"probe_{model}.json"
    if out_path.exists():
        print(f"[{model}] already probed, skipping", flush=True)
        return
    gguf = MODEL_DIR / PINS[model]["file"]
    side = gguf.with_suffix(".gguf.sha256")
    res = {"model": model, "started": now(), "gguf": PINS[model],
           "gguf_verified": side.exists() and side.read_text().strip() == PINS[model]["sha256"],
           "config_sha256": __import__("hashlib").sha256((HERE / "config_local.json").read_bytes()).hexdigest()}
    attempts = run_dir / f"attempts_{model}.jsonl"

    def log_attempt(r):
        with attempts.open("a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # context: longest Stage 1 v2 prompt in THIS model's tokenizer (also the forced/natural probe items)
    tok_srv = Server(model, 4096, run_dir / f"server_{model}_tokenize.log")
    tok_srv.start()
    try:
        kw = CONFIG["models"][model]["chat_template_kwargs"]
        lens = {}
        for iid in [p["item_id"] for p in PANEL_V2] + [FORCE_ITEM, NATURAL_ITEM]:
            lens[iid] = len(tok_srv.tokenize(tok_srv.apply_template([{"role": "user", "content": R.RENDERED[iid]["text"]}], kw)))
    finally:
        tok_srv.stop()
    n_ctx = R.round_up(S1["max_tokens"] + max(lens.values()) + 1024)
    res["prompt_tokens_v2"] = lens
    res["n_ctx"] = n_ctx
    print(f"[{model}] n_ctx={n_ctx}", flush=True)

    # 1) placement
    pargs, pinfo = placement.placement_args(model, gguf, n_ctx)
    res["placement"] = {"args": pargs, **pinfo}
    print(f"[{model}] placement {pinfo}", flush=True)

    # 2) baseline: plain --fit layer split (dense only), for the placement comparison
    if model not in placement.MOE:
        try:
            b = Server(model, n_ctx, run_dir / f"server_{model}_baseline_fit.log")
            bi = b.start()
            try:
                res["baseline_fit"] = {"layers_offloaded": bi.layers_offloaded, "gpu_weight_fraction": bi.gpu_weight_fraction,
                                       "load_seconds": bi.load_seconds, **fresh_probe(b, reps=1), "deep": depth_probe(b)}
            finally:
                b.stop()
            print(f"[{model}] baseline fit {res['baseline_fit']}", flush=True)
        except Exception as e:
            res["baseline_fit"] = {"error": repr(e)}
        time.sleep(3)

    # 3) three timed loads with the approved configuration; keep the third
    loads, srv = [], None
    for i in range(3):
        ram0, vram0 = sys_ram_mib(), gpu_snapshot()["gpu_mem_used_mib"]
        srv = Server(model, n_ctx, run_dir / f"server_{model}_load{i + 1}.log", extra_args=pargs,
                     reasoning_budget=S1["thinking_budget"], budget_message=S1["budget_message"])
        li = srv.start()
        time.sleep(2)
        loads.append({"load_seconds": li.load_seconds, "layers_offloaded": li.layers_offloaded,
                      "gpu_weight_fraction": li.gpu_weight_fraction, "gpu_model_mib": li.gpu_model_mib,
                      "cpu_model_mib": li.cpu_model_mib, "kv_mib": li.kv_mib, "compute_gpu_mib": li.compute_gpu_mib,
                      "sys_ram_before_mib": ram0, "sys_ram_added_mib": round(sys_ram_mib() - ram0, 1),
                      "vram_before_mib": vram0, "vram_added_mib": round(gpu_snapshot()["gpu_mem_used_mib"] - vram0, 1),
                      "proc_working_set_mib": round(psutil.Process(srv.pid()).memory_info().rss / 2**20, 1)})
        if i < 2:
            srv.stop()
            time.sleep(3)
    res["loads"] = loads
    print(f"[{model}] loads {[(l['load_seconds'], l['gpu_weight_fraction'], l['vram_added_mib'], l['sys_ram_added_mib']) for l in loads]}", flush=True)
    sampler = Sampler(run_dir / f"telemetry_{model}.jsonl", srv.pid()).start()
    try:
        # 4) integration checks (template render, effort control, sanity, truncation, accounting)
        res["integration"], recs = R.integration(srv, model)
        for r in recs:
            log_attempt(r)
        print(f"[{model}] integration passed={res['integration']['passed']} fidelity={res['integration']['template_fidelity']}", flush=True)
        # 5) speed
        res["speed_fresh"] = fresh_probe(srv)
        res["speed_deep"] = depth_probe(srv)
        print(f"[{model}] fresh {res['speed_fresh']} deep {res['speed_deep']}", flush=True)
        # 6) forced conclusion at the real budget, then a natural-length item
        mt, cap = S1["max_tokens"], S1["answer_allowance"]
        out = {}
        for iid in (FORCE_ITEM, NATURAL_ITEM):
            r = R.run_attempt(srv, model, iid, R.RENDERED[iid]["text"], mt, 6 * 3600, "probe", answer_cap=cap)
            r["attempt"] = 1
            log_attempt(r)
            forced = "Time is up. I must stop thinking now" in r["reasoning_text"]
            out[iid] = {"finish_reason": r["finish_reason"], "abort": r["abort"], "completion_tokens": r["completion_tokens"],
                        "reasoning_tokens": r["reasoning_tokens"], "final_tokens": r["final_tokens"],
                        "n_final_pieces": r["n_final_pieces"], "forced_message_seen": forced,
                        "final_nonempty": bool(r["final_text"].strip()), "wall_s": r["wall_s"],
                        "gen_tok_s": r["client_gen_tok_s"], "final_tail": r["final_text"][-300:]}
            print(f"[{model}] {iid} {out[iid]['finish_reason']} abort={r['abort']} tokens={r['completion_tokens']} "
                  f"reasoning={r['reasoning_tokens']} final={r['final_tokens']} forced={forced} wall={r['wall_s']}s", flush=True)
            R.wait_idle(srv)
        f = out[FORCE_ITEM]
        res["forced_conclusion"] = out
        res["forced_conclusion_ok"] = bool(f["forced_message_seen"] and f["final_nonempty"]
                                           and (f["reasoning_tokens"] or 0) <= S1["thinking_budget"] + 64)
    except Exception as e:
        res["error"] = repr(e)
        print(f"[{model}] ERROR {e!r}", flush=True)
    finally:
        res["telemetry"] = sampler.stop()
        srv.stop()
    res["finished"] = now()
    out_path.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[{model}] probe done", flush=True)


if __name__ == "__main__":
    run_dir = HERE / "runs" / os.environ.get("MORGAN_PROBE_ID", "probe-20261003")
    run_dir.mkdir(parents=True, exist_ok=True)
    for m in sys.argv[1:]:
        try:
            probe(m, run_dir)
        except Exception as e:  # one model failing must not stop the others
            print(f"[{m}] PROBE FAILED {e!r}", flush=True)
            (run_dir / f"probe_{m}.FAILED.txt").write_text(f"{now()} {e!r}\n", encoding="utf-8")

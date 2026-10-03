"""Local evaluation runner (llama.cpp). No paid APIs, no network except 127.0.0.1.

    python local/run_local.py threads <model>                 # one-time llama-bench thread test
    python local/run_local.py calibrate <model> [<model> ...] # integration checks + loads + speed probe + dev items
    python local/run_local.py stage1 ...                      # REFUSED unless calibrated and approved

Outputs go to local/runs/<run_id>/ (git-ignored): attempts_<model>.jsonl (raw records incl. full reasoning
and final text), model_<model>.json (integration, load, offload, telemetry, speed summary), server logs.
"""
from __future__ import annotations

import hashlib
import json
import random
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import client  # noqa: E402
import llm_server  # noqa: E402
from llm_server import CONFIG, PINS, MODEL_DIR, PORT, Server  # noqa: E402
from telemetry import Sampler, gpu_snapshot  # noqa: E402

RUNS = HERE / "runs"
RENDERED = json.loads((HERE / "items/rendered_prompts.json").read_text(encoding="utf-8"))
CAL_ITEMS = json.loads((HERE / "items/calibration_items.json").read_text(encoding="utf-8"))
PANEL = json.loads((HERE / "items/stage1_panel.json").read_text(encoding="utf-8"))

# contrast kwargs used only to prove that the effort/thinking control changes the rendered prompt
CONTRAST = {"qwen3.8-27b": {"enable_thinking": True, "reasoning_effort": "low"},
            "gpt-oss-20b": {"reasoning_effort": "low"},
            "glm-4.7-flash": {"enable_thinking": False},
            "gemma-4-31b": {"enable_thinking": False},
            "muse-glimmer-30b": {"reasoning_strength": "low"}}
SANITY_PROMPT = "What is 17 multiplied by 23? Give a short answer and end with a final line of the form ANSWER: <number>"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def item_seed(item_id: str) -> int:  # morgan 16 section 6
    return int(hashlib.sha256(("Morgan-2026-09-29|" + item_id).encode("utf-8")).hexdigest()[:8], 16) & 0x7FFFFFFF


def round_up(n: int, k: int = 256) -> int:
    return -(-n // k) * k


# ------------------------------------------------------------------ reference template rendering (HF-style)

def reference_render(model: str, messages: list[dict], kwargs: dict) -> str:
    import jinja2
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    m = CONFIG["models"][model]
    tpl = (HERE / m["template_file"]).read_text(encoding="utf-8")
    tok = json.loads((HERE / "official" / f"{model}__tokenizer_config.json").read_text(encoding="utf-8"))

    def special(name):
        v = tok.get(name)
        return v.get("content") if isinstance(v, dict) else (v or "")

    def raise_exception(msg):
        raise jinja2.exceptions.TemplateError(msg)

    env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True, extensions=["jinja2.ext.loopcontrols"])
    env.filters["tojson"] = lambda x, ensure_ascii=False, indent=None, separators=None, sort_keys=False: \
        json.dumps(x, ensure_ascii=ensure_ascii, indent=indent, separators=separators, sort_keys=sort_keys)
    env.globals["raise_exception"] = raise_exception
    env.globals["strftime_now"] = lambda fmt: datetime.now().strftime(fmt)
    return env.from_string(tpl).render(messages=messages, add_generation_prompt=True, bos_token=special("bos_token"),
                                       eos_token=special("eos_token"), unk_token=special("unk_token"),
                                       pad_token=special("pad_token"), **kwargs)


# ------------------------------------------------------------------ one attempt

def run_attempt(srv: Server, model: str, item_id: str, text: str, max_tokens: int, total_s: float,
                stage: str, kind: str = "item", loop_stop: bool = True, answer_cap: int | None = None,
                reasoning_cap: int | None = None) -> dict:
    mcfg = CONFIG["models"][model]
    body = client.build_body(mcfg, CONFIG["common_request"], text, max_tokens, item_seed(item_id))
    wd = CONFIG["watchdog"]
    rec = client.stream_chat(PORT, body, first_token_s=wd["first_token_s"], stall_s=wd["stall_s"],
                             total_s=total_s, loop_stop=loop_stop, answer_cap=answer_cap, reasoning_cap=reasoning_cap)
    usage, timings = rec.get("usage") or {}, rec.get("timings") or {}
    completion = usage.get("completion_tokens") or timings.get("predicted_n")
    if completion is None and rec["abort"]:
        completion = rec["n_pieces"]
    rtoks = ftoks = None
    count_error = None
    for _ in range(3):  # transient failure seen live (Ministral probe, 2026-10-03): wait for idle, retry, record
        try:
            if srv.proc and srv.proc.poll() is None:
                wait_idle(srv, 60)
                rtoks = len(srv.tokenize(rec["reasoning_text"])) if rec["reasoning_text"] else 0
                ftoks = len(srv.tokenize(rec["final_text"])) if rec["final_text"] else 0
                count_error = None
            break
        except Exception as e:
            count_error = repr(e)[:300]
            time.sleep(2)
    gen_s = (rec["wall_s"] - rec["t_first_token_s"]) if rec["t_first_token_s"] is not None else None
    return {"kind": kind, "stage": stage, "model": model, "item_id": item_id,
            "benchmark": RENDERED.get(item_id, {}).get("benchmark"), "timestamp": now(),
            "seed": body["seed"], "max_tokens": max_tokens, "payload_sha256": client.payload_sha256(body),
            "prompt_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "prompt_tokens": usage.get("prompt_tokens") or timings.get("prompt_n"),
            "completion_tokens": completion, "reasoning_tokens": rtoks, "final_tokens": ftoks,
            "token_count_error": count_error,
            "finish_reason": rec["finish_reason"], "abort": rec["abort"], "error": rec["error"],
            "wall_s": rec["wall_s"], "ttft_s": rec["t_first_token_s"], "t_first_final_s": rec["t_first_final_s"],
            "client_gen_tok_s": round(completion / gen_s, 3) if completion and gen_s else None,
            "server_prompt_tok_s": timings.get("prompt_per_second"),
            "server_gen_tok_s": timings.get("predicted_per_second"),
            "n_pieces": rec["n_pieces"], "n_final_pieces": rec.get("n_final_pieces"), "answer_cap": answer_cap,
            "reasoning_budget": srv.reasoning_budget, "usage": usage, "timings": timings,
            "reasoning_text": rec["reasoning_text"], "final_text": rec["final_text"]}


SENTINEL = "⁣ANSWER_SLOT⁣"


def continuation_prompt(model: str, user_text: str, reasoning: str) -> str:
    """Official-template rendering of [user, assistant(reasoning_content=reasoning, content=<slot>)] cut at the slot:
    exactly the text the model would see after closing its reasoning, in its own trained format."""
    kw = CONFIG["models"][model]["chat_template_kwargs"]
    import jinja2  # noqa: F401
    full = reference_render(model, [{"role": "user", "content": user_text},
                                    {"role": "assistant", "reasoning_content": reasoning, "content": SENTINEL}], kw)
    if SENTINEL not in full:
        raise RuntimeError(f"{model}: template does not place assistant content; harness forcing unavailable")
    return full.split(SENTINEL)[0]


def run_attempt_harness_forced(srv: Server, model: str, item_id: str, text: str, total_s: float, stage: str) -> dict:
    """Two-phase forced conclusion for models whose reasoning format llama-server's --reasoning-budget does not
    handle (same budget, same message): phase 1 streams until reasoning reaches the budget; phase 2 continues from the
    official-template rendering of that reasoning + the forcing message, with the answer allowance as n_predict."""
    s1 = CONFIG["stage1_v2"]
    r1 = run_attempt(srv, model, item_id, text, s1["thinking_budget"] + s1["answer_allowance"] + 128, total_s, stage,
                     answer_cap=s1["answer_allowance"], reasoning_cap=s1["thinking_budget"])
    r1["forcing_mechanism"] = "harness_two_phase"
    if r1["abort"] != "reasoning_budget_reached":
        return r1
    wait_idle(srv)
    forced_reasoning = r1["reasoning_text"] + s1["budget_message"]
    prompt = continuation_prompt(model, text, forced_reasoning)
    toks = srv.tokenize(prompt)
    m = CONFIG["models"][model]["sampling"]
    t0 = time.perf_counter()
    out = srv.post("/completion", {"prompt": toks, "n_predict": s1["answer_allowance"], "cache_prompt": False,
                                   "seed": item_seed(item_id), "temperature": m["temperature"], "top_p": m["top_p"],
                                   "top_k": m["top_k"], "min_p": m["min_p"], "repeat_penalty": 1.0,
                                   "presence_penalty": 0.0, "frequency_penalty": 0.0}, timeout=total_s)
    t = out.get("timings") or {}
    final = out.get("content") or ""
    stop_type = out.get("stop_type") or ("eos" if out.get("stopped_eos") else "limit" if out.get("stopped_limit") else None)
    r1.update(reasoning_text=forced_reasoning, final_text=final, abort=None,
              finish_reason="length" if stop_type == "limit" else "stop",
              phase2={"prompt_tokens": len(toks), "predicted_n": t.get("predicted_n"), "stop_type": stop_type,
                      "wall_s": round(time.perf_counter() - t0, 3), "gen_tok_s": t.get("predicted_per_second"),
                      "prompt_tok_s": t.get("prompt_per_second")})
    r1["completion_tokens"] = (r1["completion_tokens"] or 0) + (t.get("predicted_n") or 0)
    r1["final_tokens"] = t.get("predicted_n")
    if stop_type == "limit":
        r1["abort"] = "answer_allowance_exceeded"
    r1["wall_s"] = round(r1["wall_s"] + r1["phase2"]["wall_s"], 3)
    return r1


def wait_idle(srv: Server, timeout_s: float = 120) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            slots = srv.get("/slots")
            if not any(s.get("is_processing") for s in slots):
                return
        except Exception:
            return
        time.sleep(1)


# ------------------------------------------------------------------ integration checks

def integration(srv: Server, model: str) -> dict:
    mcfg = CONFIG["models"][model]
    kw = mcfg["chat_template_kwargs"]
    msgs = [{"role": "user", "content": SANITY_PROMPT}]
    res: dict = {}
    server_txt = srv.apply_template(msgs, kw)
    try:
        ref_txt = reference_render(model, msgs, kw)
        bos = reference_render.__globals__  # noqa: F841 (keep linters quiet)
        exact = server_txt == ref_txt
        tokcfg = json.loads((HERE / "official" / f"{model}__tokenizer_config.json").read_text(encoding="utf-8"))
        b = tokcfg.get("bos_token")
        b = b.get("content") if isinstance(b, dict) else (b or "")
        bos_only = (not exact) and b and (ref_txt == b + server_txt or server_txt == b + ref_txt)
        res["template_fidelity"] = "exact" if exact else ("bos_only_difference" if bos_only else "DIFFERENT")
        if res["template_fidelity"] == "DIFFERENT":
            res["template_server"], res["template_reference"] = server_txt[-1500:], ref_txt[-1500:]
    except Exception as e:
        res["template_fidelity"] = f"reference_render_error: {e!r}"
    res["rendered_tail"] = server_txt[-300:]
    if model in CONTRAST:
        alt = srv.apply_template(msgs, CONTRAST[model])
        res["effort_control_changes_prompt"] = alt != server_txt
    else:
        res["effort_control_changes_prompt"] = "n/a (reasoning always on)"
    # short generation
    g = run_attempt(srv, model, "integration/sanity", SANITY_PROMPT, 4096, 1800, "integration", kind="integration")
    res["sanity"] = {k: g[k] for k in ("finish_reason", "abort", "error", "completion_tokens", "reasoning_tokens",
                                        "final_tokens", "n_pieces", "server_gen_tok_s", "wall_s")}
    res["sanity"]["final_text"] = g["final_text"][-400:]
    res["sanity"]["reasoning_nonempty"] = bool(g["reasoning_text"].strip())
    res["sanity"]["final_has_391"] = "391" in g["final_text"]
    res["sanity"]["markers_in_final"] = [m for m in ("<think>", "</think>", "[THINK]", "[/THINK]", "<|channel|>", "<|message|>")
                                         if m in g["final_text"]]
    # completion_tokens must count reasoning + final; the reasoning parser hides delimiter tokens from the stream,
    # so streamed pieces may trail the server count by a few tokens but never exceed it
    tp = (g["timings"] or {}).get("predicted_n")
    hidden = (g["completion_tokens"] or 0) - g["n_pieces"]
    res["token_accounting"] = {"usage_completion": (g["usage"] or {}).get("completion_tokens"), "predicted_n": tp,
                               "streamed_pieces": g["n_pieces"], "hidden_delimiter_tokens": hidden}
    res["token_accounting_ok"] = tp is not None and (g["usage"] or {}).get("completion_tokens") == tp and 0 <= hidden <= 24
    wait_idle(srv)
    t = run_attempt(srv, model, "integration/truncation", SANITY_PROMPT, 32, 600, "integration", kind="integration")
    res["truncation"] = {"finish_reason": t["finish_reason"], "completion_tokens": t["completion_tokens"]}
    res["truncation_ok"] = t["finish_reason"] == "length" and t["completion_tokens"] == 32
    wait_idle(srv)
    res["passed"] = (res["template_fidelity"] in ("exact", "bos_only_difference")
                     and res["effort_control_changes_prompt"] in (True, "n/a (reasoning always on)")
                     and res["sanity"]["finish_reason"] == "stop" and res["sanity"]["reasoning_nonempty"]
                     and res["sanity"]["final_has_391"] and not res["sanity"]["markers_in_final"]
                     and bool(res["token_accounting_ok"]) and res["truncation_ok"])
    return res, [g, t]


def speed_probe(srv: Server, reps: int = 3) -> dict:
    """Standardised throughput: 512-token prompt, 256 generated tokens (ignore_eos), prompt cache off."""
    filler = " ".join(["The quick brown fox jumps over the lazy dog."] * 200)
    toks = srv.tokenize(filler)[:512]
    pp, tg = [], []
    for _ in range(reps):
        r = srv.post("/completion", {"prompt": toks, "n_predict": 256, "ignore_eos": True, "cache_prompt": False,
                                     "temperature": 1.0, "top_k": 0, "top_p": 1.0, "min_p": 0.0, "seed": 1}, timeout=3600)
        pp.append(r["timings"]["prompt_per_second"])
        tg.append(r["timings"]["predicted_per_second"])
    return {"pp512_tok_s_median": round(statistics.median(pp), 2), "tg256_tok_s_median": round(statistics.median(tg), 2),
            "pp512_all": [round(x, 2) for x in pp], "tg256_all": [round(x, 2) for x in tg]}


# ------------------------------------------------------------------ commands

def cmd_threads(model: str) -> None:
    bench = Path(CONFIG["backend"]["install_dir"]) / "llama-bench.exe"
    out = subprocess.run([str(bench), "-m", str(MODEL_DIR / PINS[model]["file"]), "-ngl", "18", "-fa", "1",
                          "-ctk", "q8_0", "-ctv", "q8_0", "-p", "0", "-n", "64", "-r", "3",
                          "-t", "6,8,12,16,20,28", "-o", "json"], capture_output=True, text=True, timeout=3600)
    rows = json.loads(out.stdout)
    res = [{"threads": r["n_threads"], "tg64_tok_s": round(r["avg_ts"], 2), "stdev": round(r["stddev_ts"], 2)} for r in rows]
    RUNS.mkdir(exist_ok=True)
    (RUNS / f"threads_{model}.json").write_text(json.dumps({"model": model, "ngl": 18, "results": res}, indent=1))
    print(json.dumps(res, indent=1))


def cmd_calibrate(models: list[str], run_id: str) -> None:
    cal = CONFIG["calibration"]
    run_dir = RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    for model in models:
        if not (MODEL_DIR / PINS[model]["file"]).with_suffix(".gguf.sha256").exists():
            raise SystemExit(f"{model}: weights not verified; run fetch_models.py first")
        attempts_path = run_dir / f"attempts_{model}.jsonl"
        summary = {"model": model, "run_id": run_id, "started": now(), "config_sha256":
                   hashlib.sha256((HERE / "config_local.json").read_bytes()).hexdigest(),
                   "gguf": PINS[model], "threads": CONFIG["backend"]["threads"]}

        def log_attempt(r: dict) -> None:
            with attempts_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        # 1) probe server: tokenise every rendered prompt with this model's template + tokenizer
        probe = Server(model, 8192, run_dir / f"server_{model}_probe.log")
        info = probe.start()
        lengths = {}
        try:
            for iid, v in RENDERED.items():
                txt = probe.apply_template([{"role": "user", "content": v["text"]}], CONFIG["models"][model]["chat_template_kwargs"])
                lengths[iid] = len(probe.tokenize(txt))
            summary["integration"], recs = integration(probe, model)
            for r in recs:
                log_attempt(r)
        finally:
            probe.stop()
        summary["probe_load"] = {"load_seconds": info.load_seconds, "n_ctx": 8192}
        summary["prompt_tokens"] = {"max_all": max(lengths.values()),
                                    "max_stage1": max(lengths[p["item_id"]] for p in PANEL),
                                    "max_calibration": max(lengths[c["item_id"]] for c in CAL_ITEMS),
                                    "per_item": lengths}
        n_ctx = round_up(cal["C_dev"] + summary["prompt_tokens"]["max_all"] + 1024)
        summary["n_ctx_calibration"] = n_ctx
        print(f"[{model}] integration passed={summary['integration']['passed']} n_ctx={n_ctx}", flush=True)

        # 2) three timed loads at the calibration context; keep the third one running
        loads = []
        baseline = gpu_snapshot()["gpu_mem_used_mib"]
        summary["gpu_baseline_mib"] = baseline
        import psutil
        vm = psutil.virtual_memory()
        summary["sys_ram_baseline_mib"] = round((vm.total - vm.available) / 2**20, 1)
        for i in range(3):
            srv = Server(model, n_ctx, run_dir / f"server_{model}_load{i + 1}.log")
            li = srv.start()
            loads.append({"load_seconds": li.load_seconds, "gpu_model_mib": li.gpu_model_mib, "cpu_model_mib": li.cpu_model_mib,
                          "gpu_weight_fraction": li.gpu_weight_fraction, "layers_offloaded": li.layers_offloaded,
                          "kv_mib": li.kv_mib, "compute_gpu_mib": li.compute_gpu_mib, "n_ctx_reported": li.n_ctx})
            if i < 2:
                srv.stop()
                time.sleep(3)
        summary["loads"] = loads
        logtxt = (run_dir / f"server_{model}_load3.log").read_text(encoding="utf-8", errors="replace")
        summary["server_info_lines"] = [l.strip() for l in logtxt.splitlines()
                                        if any(k in l for k in ("expert_gating_func", "rope scaling", "n_ctx_orig_yarn", "rope_type",
                                                                "fit", "offloaded", "file type", "model type", "n_swa", "n_expert"))][:60]
        sampler = Sampler(run_dir / f"telemetry_{model}.jsonl", srv.pid()).start()
        try:
            summary["speed_probe"] = speed_probe(srv)
            print(f"[{model}] speed probe {summary['speed_probe']}", flush=True)
            # 3) development items, shuffled per model with seed 20260929
            items = CAL_ITEMS[:]
            random.Random(f"20260929|{model}").shuffle(items)
            for it in items:
                iid = it["item_id"]
                for attempt in range(3):  # 1 + up to 2 infrastructure reruns
                    if srv.proc is None or srv.proc.poll() is not None:
                        srv = Server(model, n_ctx, run_dir / f"server_{model}_restart.log")
                        srv.start()
                        sampler.pid = srv.pid()
                    total_s = 1.5 * cal["C_dev"] / CONFIG["watchdog"]["calibration_floor_tok_s"] + 1800
                    r = run_attempt(srv, model, iid, RENDERED[iid]["text"], cal["C_dev"], total_s, "calibration")
                    r["attempt"] = attempt + 1
                    log_attempt(r)
                    print(f"[{model}] {iid} finish={r['finish_reason']} abort={r['abort']} tokens={r['completion_tokens']} "
                          f"gen={r['client_gen_tok_s']} tok/s wall={r['wall_s']}s", flush=True)
                    wait_idle(srv)
                    infra = r["error"] or r["abort"] in ("first_token_timeout", "stall_timeout", "total_timeout")
                    if not infra:
                        break
        finally:
            summary["telemetry"] = sampler.stop()
            srv.stop()
        summary["finished"] = now()
        (run_dir / f"model_{model}.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"[{model}] done", flush=True)


STAGE1_ORDER = ["r1-0528-qwen3-8b", "gpt-oss-20b", "glm-4.7-flash", "ministral-3-14b-reasoning",
                "muse-glimmer-30b", "qwen3.8-27b", "gemma-4-31b"]


def stage1_plan() -> list[tuple[str, list[str]]]:
    panel = [p["item_id"] for p in json.loads((HERE / "items/stage1_panel_v2.json").read_text(encoding="utf-8"))]
    plan = []
    for m in STAGE1_ORDER:
        order = panel[:]
        random.Random(f"20260929|stage1-v2|{m}").shuffle(order)
        plan.append((m, order))
    return plan


def cmd_stage1(*args):
    """Stage 1 v2. Gate order: (1) the user's approval file, (2) frozen config, (3) full preflight. Resumable:
    items with a recorded final attempt are skipped. Never invoked by any unattended script."""
    dry = "--dry-run" in args
    if not dry and not (HERE / "STAGE1_APPROVED.json").exists():
        raise SystemExit("REFUSED: Stage 1 requires the user's explicit approval file local/STAGE1_APPROVED.json")
    s1 = CONFIG.get("stage1_v2") or {}
    if not dry and s1.get("frozen") is not True:
        raise SystemExit("REFUSED: config_local.json stage1_v2.frozen is not true")
    import preflight
    checks = preflight.run()
    failed = [c for c in checks if not c[1] and not (dry and c[0].startswith("Stage 1 approval file"))]
    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
    plan = stage1_plan()
    print("\nStage 1 v2 plan:", ", ".join(f"{m} ({len(items)} items)" for m, items in plan))
    if dry:
        print(f"DRY RUN: nothing generated. {len(failed)} blocking preflight failure(s).")
        return
    if failed:
        raise SystemExit(f"REFUSED: {len(failed)} preflight check(s) failed")
    import os
    import placement
    probe_dir = HERE / "runs" / os.environ.get("MORGAN_PROBE_ID", "probe-20261003")
    run_dir = HERE / "runs" / os.environ.get("MORGAN_STAGE1_ID", "stage1-v2")
    run_dir.mkdir(parents=True, exist_ok=True)
    for model, items in plan:
        attempts_path = run_dir / f"attempts_{model}.jsonl"
        done = set()
        if attempts_path.exists():
            for line in attempts_path.read_text(encoding="utf-8").splitlines():
                r = json.loads(line)
                if r.get("kind") == "item" and r.get("final_attempt"):
                    done.add(r["item_id"])
        todo = [i for i in items if i not in done]
        if not todo:
            continue
        probe = json.loads((probe_dir / f"probe_{model}.json").read_text(encoding="utf-8"))
        n_ctx = probe["n_ctx"]
        pargs, pinfo = placement.placement_args(model, MODEL_DIR / PINS[model]["file"], n_ctx)
        deep = probe["speed_deep"]["tg_tok_s_at_depth"]
        total_s = 1.5 * s1["max_tokens"] / max(0.5, 0.8 * deep) + 1800
        with attempts_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"kind": "server_start", "model": model, "timestamp": now(), "n_ctx": n_ctx,
                                "placement": pinfo, "placement_args": pargs, "watchdog_total_s": round(total_s)}) + "\n")

        def start():
            s = Server(model, n_ctx, run_dir / f"server_{model}_{int(time.time())}.log", extra_args=pargs,
                       reasoning_budget=s1["thinking_budget"], budget_message=s1["budget_message"])
            s.start()
            return s
        srv = start()
        sampler = Sampler(run_dir / f"telemetry_{model}.jsonl", srv.pid()).start()
        try:
            for iid in todo:
                for attempt in range(3):  # 1 + up to 2 infrastructure reruns
                    if srv.proc is None or srv.proc.poll() is not None:
                        srv = start()
                        sampler.pid = srv.pid()
                    if CONFIG["models"][model].get("forcing") == "harness":
                        r = run_attempt_harness_forced(srv, model, iid, RENDERED[iid]["text"], total_s, "stage1")
                    else:
                        r = run_attempt(srv, model, iid, RENDERED[iid]["text"], s1["max_tokens"], total_s, "stage1",
                                        answer_cap=s1["answer_allowance"])
                    infra = bool(r["error"]) or r["abort"] in ("first_token_timeout", "stall_timeout", "total_timeout")
                    r["attempt"], r["final_attempt"] = attempt + 1, (not infra) or attempt == 2
                    with attempts_path.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")
                    print(f"[stage1 {model}] {iid} finish={r['finish_reason']} abort={r['abort']} "
                          f"tokens={r['completion_tokens']} wall={r['wall_s']}s", flush=True)
                    wait_idle(srv)
                    if not infra:
                        break
        finally:
            sampler.stop()
            srv.stop()
    print(f"STAGE 1 GENERATION COMPLETE; score with: .venv-scoring\\Scripts\\python.exe local/score_local.py {run_dir}",
          flush=True)


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "threads":
        cmd_threads(args[0])
    elif cmd == "calibrate":
        import os
        run_id = os.environ.get("MORGAN_RUN_ID") or "calibration-" + datetime.now().strftime("%Y%m%d")
        cmd_calibrate(args, run_id)
    elif cmd == "stage1":
        cmd_stage1(*args)
    else:
        raise SystemExit(__doc__)

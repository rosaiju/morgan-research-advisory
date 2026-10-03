"""Non-scored endurance / recovery test of the Stage 1 v2 infrastructure (NOT Stage 1; uses no Stage 1 item).

Drives the same generation loop as Stage 1 (run_local.run_items: frozen probe placement and n_ctx, 6,144 + 1,536
budget, forced conclusion, watchdogs, telemetry, resume) with development (calibration/probe) items and synthetic
prompts only. Every step is idempotent: state.json records finished steps and a rerun skips them.

    local\\.venv\\Scripts\\python.exe local\\endurance.py all        # run every unfinished step in order
    local\\.venv\\Scripts\\python.exe local\\endurance.py <step>     # one step
    local\\.venv\\Scripts\\python.exe local\\endurance.py status

Steps: smoke, rotation, kill_server, kill_runner, docker_repeat, score_twice, soak, report.
Outputs: local/runs/endurance-20261003/ (git-ignored); report: ENDURANCE_REPORT.md there.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(HERE), str(ROOT / "scoring")]

import psutil  # noqa: E402

import llm_server  # noqa: E402
import run_local  # noqa: E402
from telemetry import gpu_snapshot  # noqa: E402

OUT = HERE / "runs" / os.environ.get("MORGAN_ENDURANCE_ID", "endurance-20261003")
STATE = OUT / "state.json"
SCORING_PY = ROOT / ".venv-scoring/Scripts/python.exe"
FAST = ["r1-0528-qwen3-8b", "gpt-oss-20b", "glm-4.7-flash", "ministral-3-14b-reasoning"]
DENSE = ["muse-glimmer-30b", "qwen3.8-27b", "gemma-4-31b"]
ALL = FAST + DENSE                                   # = run_local.STAGE1_ORDER
FORCE_ITEM, NATURAL_ITEM = "math500/test/geometry/880.json", "ifeval/1012"   # development (probe) items
SOAK_CYCLES = int(os.environ.get("MORGAN_SOAK_CYCLES", "5"))

PANEL_IDS = {p["item_id"] for n in ("stage1_panel_v2.json", "stage1_panel.json")
             for p in json.loads((HERE / "items" / n).read_text(encoding="utf-8"))}
DEV_IDS = {c["item_id"] for c in json.loads((HERE / "items/calibration_items.json").read_text(encoding="utf-8"))}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def guard(item_ids) -> None:
    bad = set(item_ids) & PANEL_IDS
    if bad:
        raise SystemExit(f"REFUSED: endurance test may not use Stage 1 items: {sorted(bad)}")


def load_state() -> dict:
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"steps": {}}


def save_state(st: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=1), encoding="utf-8")
    os.replace(tmp, STATE)


def log(msg: str) -> None:
    print(f"{now()} {msg}", flush=True)


def llama_procs() -> list[int]:
    return [p.pid for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower() == "llama-server.exe"]


def idle_snapshot() -> dict:
    vm = psutil.virtual_memory()
    g = gpu_snapshot()
    me = psutil.Process()
    snap = {"t": now(), "gpu_mem_used_mib": g["gpu_mem_used_mib"], "gpu_temp_c": g["gpu_temp_c"],
            "sys_used_mib": round((vm.total - vm.available) / 2**20), "llama_servers": llama_procs(),
            "runner_handles": me.num_handles() if hasattr(me, "num_handles") else None,
            "runner_rss_mib": round(me.memory_info().rss / 2**20), "disk_free_gb": round(run_local.free_disk_gb(OUT), 1)}
    try:
        import docker_code  # noqa: F401
        snap["sandbox_containers"] = len(__import__("docker_code").leaked_containers())
    except Exception:  # noqa: BLE001
        snap["sandbox_containers"] = None
    return snap


def synthetic(n: int) -> str:
    return (f"Synthetic endurance prompt {n}. List the three smallest prime numbers greater than {10 * n + 7}. "
            "Keep your reasoning brief. End with a final line of the form ANSWER: <p1>, <p2>, <p3>")


def items_rows(d: Path, model: str) -> list[dict]:
    p = d / f"attempts_{model}.jsonl"
    rows = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"kind": "_corrupt_line"})
    return rows


def summarize_items(d: Path, models) -> dict:
    out = {}
    for m in models:
        rows = items_rows(d, m)
        its = [r for r in rows if r.get("kind") == "item"]
        finals = [r for r in its if r.get("final_attempt")]
        dup = len(finals) - len({r["item_id"] for r in finals})
        out[m] = {"attempts": len(its), "final": len(finals), "duplicate_finals": dup,
                  "server_starts": sum(r.get("kind") == "server_ready" for r in rows),
                  "start_failures": sum(r.get("kind") == "server_start_failed" for r in rows),
                  "corrupt_lines": sum(r.get("kind") == "_corrupt_line" for r in rows),
                  "per_item": [{k: r.get(k) for k in ("item_id", "attempt", "final_attempt", "finish_reason", "abort",
                                                      "error", "completion_tokens", "reasoning_tokens", "final_tokens",
                                                      "wall_s", "client_gen_tok_s", "forcing_mechanism")}
                               | {"forced": run_local.CONFIG["stage1_v2"]["budget_message"].strip()[:30]
                                  in (r.get("reasoning_text") or "")} for r in its]}
    return out


def with_lock(purpose: str, fn):
    lock = llm_server.acquire_runner_lock(purpose)
    llm_server.keep_awake(True)
    try:
        return fn()
    finally:
        llm_server.keep_awake(False)
        llm_server.release_runner_lock(lock)


# ------------------------------------------------------------------ steps

def step_smoke() -> dict:
    """Live check of the changed harness code on the fastest model with one natural-length development item."""
    d = OUT / "smoke"
    guard([NATURAL_ITEM])
    inc = with_lock("endurance smoke", lambda: run_local.run_items([("r1-0528-qwen3-8b", [NATURAL_ITEM])], d, "endurance"))
    s = summarize_items(d, ["r1-0528-qwen3-8b"])
    ok = not inc and s["r1-0528-qwen3-8b"]["final"] == 1 and not llama_procs()
    return {"ok": ok, "incomplete": inc, "items": s, "after": idle_snapshot()}


def step_rotation() -> dict:
    """All seven models in Stage 1 order: load, generate, unload; forced conclusion on every fast model."""
    d = OUT / "rotation"
    plan = [(m, [NATURAL_ITEM, "mmlu_pro/50", FORCE_ITEM]) for m in FAST] + [(m, [NATURAL_ITEM]) for m in DENSE]
    guard(i for _, its in plan for i in its)
    snaps = [idle_snapshot()]

    def go():
        inc = {}
        for m, its in plan:          # one model at a time so the idle state between models can be recorded
            inc |= run_local.run_items([(m, its)], d, "endurance")
            time.sleep(5)
            snaps.append({"after": m, **idle_snapshot()})
        return inc
    inc = with_lock("endurance rotation", go)
    s = summarize_items(d, ALL)
    forced_ok = all(any(x["item_id"] == FORCE_ITEM and x["forced"] and x["finish_reason"] == "stop"
                        for x in s[m]["per_item"]) for m in FAST)
    ok = (not inc and all(s[m]["final"] == len(its) and s[m]["duplicate_finals"] == 0 for m, its in plan)
          and forced_ok and all(not x["llama_servers"] for x in snaps))
    return {"ok": ok, "incomplete": inc, "forced_conclusion_all_fast_models": forced_ok, "idle_snapshots": snaps,
            "items": s}


def step_kill_server() -> dict:
    """Kill llama-server mid-generation: the attempt must be recorded as an infrastructure error, the server restarted
    and the item rerun to a final result."""
    d = OUT / "kill_server"
    model, item = "r1-0528-qwen3-8b", "mmlu_pro/31"
    guard([item])
    killed = {}

    def killer():
        p = d / f"attempts_{model}.jsonl"
        t0 = time.time()
        while time.time() - t0 < 600:
            rows = items_rows(d, model)
            if any(r.get("kind") == "server_ready" for r in rows) and not any(r.get("kind") == "item" for r in rows):
                time.sleep(25)       # well into generation of the first attempt
                pids = llama_procs()
                for pid in pids:
                    psutil.Process(pid).kill()
                killed.update(pids=pids, at=now(), file_lines=len(p.read_text(encoding="utf-8").splitlines()))
                return
            time.sleep(1)
    t = threading.Thread(target=killer, daemon=True)
    t.start()
    inc = with_lock("endurance kill_server", lambda: run_local.run_items([(model, [item])], d, "endurance"))
    t.join(timeout=5)
    s = summarize_items(d, [model])[model]
    its = s["per_item"]
    ok = (bool(killed.get("pids")) and not inc and len(its) >= 2 and its[0]["error"] and not its[0]["final_attempt"]
          and its[-1]["final_attempt"] and not its[-1]["error"] and s["server_starts"] >= 2 and not llama_procs())
    return {"ok": ok, "killed": killed, "incomplete": inc, "items": s}


def step_kill_runner() -> dict:
    """Hard-kill the runner process mid-run (as a crash or reboot would), corrupt the tail of the results file, then
    resume: the orphan server must be reaped, finished items not regenerated, numbering continued, no duplicates."""
    d = OUT / "kill_runner"
    model, its = "ministral-3-14b-reasoning", ["mmlu_pro/50", NATURAL_ITEM, "mmlu_pro/31"]
    guard(its)
    cmd = [sys.executable, str(Path(__file__)), "_child", str(d), model, *its]
    res = {}
    if not (d / "child1.done").exists():
        child = subprocess.Popen(cmd, stdout=(OUT / "kill_runner_child1.log").open("w"), stderr=subprocess.STDOUT)
        t0 = time.time()
        while time.time() - t0 < 3600:      # kill once the first item is final and the second is generating
            rows = items_rows(d, model)
            if sum(r.get("kind") == "item" and r.get("final_attempt") for r in rows) >= 1:
                time.sleep(30)
                break
            if child.poll() is not None:
                break
            time.sleep(2)
        psutil.Process(child.pid).kill()     # the runner only; its llama-server child is left orphaned
        child.wait()
        time.sleep(2)
        res["orphans_after_kill"] = llama_procs()
        res["lines_before_resume"] = len(items_rows(d, model))
        with (d / f"attempts_{model}.jsonl").open("a", encoding="utf-8") as f:
            f.write('{"kind": "item", "item_id": "mmlu_pro/31", "final_att')   # simulated torn write
        (d / "child1.done").write_text(json.dumps(res))
    else:
        res = json.loads((d / "child1.done").read_text())
    p2 = subprocess.run(cmd, stdout=(OUT / "kill_runner_child2.log").open("w"), stderr=subprocess.STDOUT, timeout=7200)
    s = summarize_items(d, [model])[model]
    finals = sorted(x["item_id"] for x in s["per_item"] if x["final_attempt"])
    res.update(resume_exit=p2.returncode, items=s, orphans_after_resume=llama_procs(), finals=finals)
    res["ok"] = (bool(res["orphans_after_kill"]) and p2.returncode == 0 and finals == sorted(its)
                 and s["duplicate_finals"] == 0 and not llama_procs() and s["corrupt_lines"] == 1)
    return res


def _child(d: str, model: str, *its: str) -> None:
    guard(its)
    inc = with_lock("endurance kill_runner child", lambda: run_local.run_items([(model, list(its))], Path(d), "endurance"))
    raise SystemExit(1 if inc else 0)


def step_docker_repeat(n: int = 300) -> dict:
    """The Docker code sandbox, repeatedly, on a synthetic function (not a Stage 1 item)."""
    sys.path.insert(0, str(ROOT / "scoring"))
    code = f"""
import json, sys, time
sys.path[:0] = [r"{ROOT / 'scoring'}", r"C:\\Users\\rohan\\open-source-ai-model"]
import docker_code as D
spec = {{"kind": "code", "function": "add3", "cases": [["add3(1, 2, 3)", "6"], ["add3(-1, 0, 1)", "0"],
        ["add3(0.5, 0.25, 0.25)", "1.0"]]}}
good = "```python\\ndef add3(a, b, c):\\n    return a + b + c\\n```"
bad = "```python\\ndef add3(a, b, c):\\n    return a + b\\n```"
loop = "```python\\ndef add3(a, b, c):\\n    while True: pass\\n```"
res, times = [], []
for i in range({n}):
    reply = loop if i % 50 == 49 else (good if i % 2 == 0 else bad)
    t = time.perf_counter()
    r = D.check_code(spec, reply, timeout=3 if reply is loop else 15)
    times.append(time.perf_counter() - t)
    res.append((i % 2 == 0 and reply is not loop, reply is loop, r.score, r.detail))
expected_ok = all((s == 1.0) if g else s == 0.0 for g, lp, s, _ in res)   # bad add3 fails all 3 cases
print(json.dumps({{"n": len(res), "all_expected": expected_ok, "distinct_results": len({{(s, d) for _, _, s, d in res}}),
                  "median_s": sorted(times)[len(times)//2], "max_s": max(times), "leaked": D.leaked_containers()}}))
"""
    p = subprocess.run([str(SCORING_PY), "-c", code], capture_output=True, text=True, timeout=7200)
    out = json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode == 0 else {"stderr": p.stderr[-2000:]}
    out["ok"] = p.returncode == 0 and out.get("all_expected") and out.get("distinct_results") == 3 and not out.get("leaked")
    return out


def step_score_twice() -> dict:
    """Scorer restart / determinism: score the rotation run twice from scratch; outputs must be byte-identical."""
    d = OUT / "rotation"
    env = {**os.environ, "NLTK_DATA": str(ROOT / "scoring/vendor/nltk_data"), "PYTHONIOENCODING": "utf-8"}
    hashes = []
    for k in (1, 2):
        p = subprocess.run([str(SCORING_PY), str(HERE / "score_local.py"), str(d), f"scored_{k}.jsonl"],
                           capture_output=True, text=True, env=env, timeout=3600)
        if p.returncode != 0:
            return {"ok": False, "stderr": p.stderr[-2000:]}
        hashes.append(hashlib.sha256((d / f"scored_{k}.jsonl").read_bytes()).hexdigest())
    rows = [json.loads(l) for l in (d / "scored_1.jsonl").read_text(encoding="utf-8").splitlines()]
    statuses = {}
    for r in rows:
        statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    return {"ok": hashes[0] == hashes[1], "sha256": hashes, "rows": len(rows), "statuses": statuses}


def step_soak() -> dict:
    """Repeated load / short generation / unload of all seven models (synthetic prompts), recording the idle state
    after every model to expose VRAM, RAM, process, handle or container leaks. Resumable per cycle."""
    d = OUT / "soak"
    st = load_state()
    cyc = st.setdefault("soak_cycles", [])
    with_lock("endurance soak", lambda: None)   # fail early if another runner is active
    for c in range(len(cyc), SOAK_CYCLES):
        iid = f"synthetic/soak-{c + 1}"
        texts = {iid: synthetic(c + 1)}
        snaps = [idle_snapshot()]
        t0 = time.time()

        def go():
            inc = {}
            for m in ALL:
                inc |= run_local.run_items([(m, [iid])], d, "endurance", texts=texts)
                time.sleep(5)
                snaps.append({"after": m, **idle_snapshot()})
            return inc
        inc = with_lock(f"endurance soak cycle {c + 1}", go)
        cyc.append({"cycle": c + 1, "minutes": round((time.time() - t0) / 60, 1), "incomplete": inc, "snapshots": snaps})
        fresh = load_state()          # merge: never overwrite results other steps wrote meanwhile
        fresh["soak_cycles"] = cyc
        save_state(fresh)
        log(f"soak cycle {c + 1}/{SOAK_CYCLES} done in {cyc[-1]['minutes']} min; incomplete={inc}")
    s = summarize_items(d, ALL)
    first, last = cyc[0]["snapshots"][0], cyc[-1]["snapshots"][-1]
    idle_vram = [x["gpu_mem_used_mib"] for c in cyc for x in c["snapshots"]]
    ok = (all(not c["incomplete"] for c in cyc) and all(v["duplicate_finals"] == 0 for v in s.values())
          and all(not x["llama_servers"] for c in cyc for x in c["snapshots"])
          and max(idle_vram) - min(idle_vram) < 512)
    return {"ok": ok, "cycles": len(cyc), "idle_vram_range_mib": [min(idle_vram), max(idle_vram)],
            "sys_used_first_last_mib": [first["sys_used_mib"], last["sys_used_mib"]],
            "runner_handles_first_last": [first["runner_handles"], last["runner_handles"]],
            "items": {m: {k: v[k] for k in ("attempts", "final", "duplicate_finals", "server_starts")} for m, v in s.items()}}


STEPS = {"smoke": step_smoke, "rotation": step_rotation, "kill_server": step_kill_server,
         "kill_runner": step_kill_runner, "docker_repeat": step_docker_repeat, "score_twice": step_score_twice,
         "soak": step_soak}


def run_step(name: str, force: bool = False) -> dict:
    st = load_state()
    if st["steps"].get(name, {}).get("ok") and not force:
        log(f"{name}: already passed, skipped")
        return st["steps"][name]
    log(f"{name}: start")
    t0 = time.time()
    try:
        res = STEPS[name]()
    except Exception as e:  # noqa: BLE001  (record and continue with independent steps)
        import traceback
        res = {"ok": False, "exception": repr(e), "traceback": traceback.format_exc()[-3000:]}
    res["minutes"] = round((time.time() - t0) / 60, 1)
    res["finished"] = now()
    st = load_state()
    st["steps"][name] = res
    save_state(st)
    log(f"{name}: ok={res.get('ok')} ({res['minutes']} min)")
    return res


def report() -> None:
    st = load_state()
    lines = [f"# Endurance / recovery test (NOT Stage 1) — {now()}", "",
             "Development and synthetic items only; no Stage 1 item was used (enforced by `guard`).", "",
             "| Step | Result | Minutes | Finished |", "|---|---|---|---|"]
    for k in STEPS:
        r = st["steps"].get(k)
        lines.append(f"| {k} | {'PASS' if r and r.get('ok') else ('FAIL' if r else 'not run')} | "
                     f"{r.get('minutes') if r else ''} | {r.get('finished') if r else ''} |")
    lines += ["", "Full details: `state.json` in this directory.", ""]
    (OUT / "ENDURANCE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    a = sys.argv[1:]
    OUT.mkdir(parents=True, exist_ok=True)
    if a[0] == "_child":
        _child(*a[1:])
    elif a[0] == "status":
        report()
    elif a[0] == "all":
        for k in STEPS:
            run_step(k)
        report()
    elif a[0] in STEPS:
        run_step(a[0], force="--force" in a)
        report()
    else:
        raise SystemExit(__doc__)

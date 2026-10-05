"""Stage 2 generation for the finalists assigned to THIS host. REFUSED unless approved for this host.

    MORGAN_HOST=<host> python local/stage2/run_stage2.py [--dry-run] [<model> ...]

Gate (in order): local/stage2/STAGE2_APPROVED_<host>.json written by the user, whose freeze_sha256 equals the SHA-256
of local/stage2/items/stage2_freeze_<host>.json; then preflight_stage2 fully green. --dry-run checks everything and
prints the plan without generating.

Same loop as Stage 1 v2 (local/run_local.py run_items), with the Stage 2 budget and panel: frozen probe placement and
n_ctx from local/runs/stage2-probe-<host>/, server forcing at 16,384 + 2,048, 1 + up to 2 infrastructure reruns per item
counted across resumes, durable appends, single runner lock, disk guard. Resumable: rerun the same command.
Outputs: local/runs/stage2-<host>/attempts_<model>.jsonl, telemetry_<model>.jsonl, server logs, RUN_INFO.json.
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

import run_local as R  # noqa: E402
from llm_server import CONFIG, Server  # noqa: E402
from telemetry import Sampler  # noqa: E402

S2 = C.CONFIG2
APPROVAL = C.HERE / f"STAGE2_APPROVED_{C.HOST}.json"
FREEZE = C.HERE / "items" / f"stage2_freeze_{C.HOST}.json"


def plan(models: list[str]) -> list[tuple[str, list[str]]]:
    panel = [p["item_id"] for p in C.PANEL2]
    out = []
    for m in models:
        order = panel[:]
        random.Random(f"20260929|stage2|{m}").shuffle(order)
        out.append((m, order))
    return out


def approval_ok(approval: Path = APPROVAL, freeze: Path = FREEZE) -> tuple[bool, str]:
    if not approval.exists():
        return False, f"missing {approval.name} (written by the user)"
    if not freeze.exists():
        return False, f"missing {freeze.name}"
    a = json.loads(approval.read_text(encoding="utf-8"))
    h = C.sha(freeze)
    return (a.get("freeze_sha256") == h and a.get("host") == C.HOST,
            f"approval freeze_sha256 {'matches' if a.get('freeze_sha256') == h else 'DOES NOT match'} {h[:16]}…, host {a.get('host')}")


def run_items(plan_: list[tuple[str, list[str]]], run_dir: Path, start_retries: int = 3) -> dict[str, str]:
    run_dir.mkdir(parents=True, exist_ok=True)
    incomplete: dict[str, str] = {}
    for model, items in plan_:
        attempts_path = run_dir / f"attempts_{model}.jsonl"
        done, used = R.completed_items(attempts_path), R.attempts_used(attempts_path)
        todo = [i for i in items if i not in done]
        if not todo:
            continue
        if R.free_disk_gb(run_dir) < R.MIN_FREE_DISK_GB:
            incomplete[model] = f"free disk below {R.MIN_FREE_DISK_GB} GB"
            break
        probe = json.loads((C.PROBE_DIR / f"probe_{model}.json").read_text(encoding="utf-8"))
        n_ctx, pargs = probe["n_ctx"], probe["placement"]["args"]
        pinfo = {k: v for k, v in probe["placement"].items() if k != "args"} | {"source": "Stage 2 probe record (frozen)"}
        deep = probe["speed_deep_16k"]["tg_tok_s_at_depth"]
        total_s = 1.5 * S2["max_tokens"] / max(0.5, 0.8 * deep) + 1800
        R.append_jsonl(attempts_path, {"kind": "server_start", "model": model, "host": C.HOST, "timestamp": R.now(),
                                       "n_ctx": n_ctx, "placement": pinfo, "placement_args": pargs,
                                       "watchdog_total_s": round(total_s)})

        def start():
            last = None
            for k in range(start_retries):
                s = Server(model, n_ctx, run_dir / f"server_{model}_{int(time.time())}.log", threads=C.server_threads(),
                           extra_args=pargs, reasoning_budget=S2["thinking_budget"], budget_message=S2["budget_message"])
                try:
                    info = s.start()
                    R.append_jsonl(attempts_path, {"kind": "server_ready", "model": model, "timestamp": R.now(),
                                                   "load_seconds": info.load_seconds, "layers": info.layers_offloaded,
                                                   "gpu_model_mib": info.gpu_model_mib, "pid": s.pid()})
                    return s
                except Exception as e:  # noqa: BLE001
                    s.stop()
                    last = e
                    R.append_jsonl(attempts_path, {"kind": "server_start_failed", "model": model, "timestamp": R.now(),
                                                   "try": k + 1, "error": repr(e)[:500]})
                    time.sleep(20)
            raise RuntimeError(f"server failed to start {start_retries} times: {last!r}")

        try:
            srv = start()
        except RuntimeError as e:
            incomplete[model] = str(e)[:300]
            continue
        sampler = Sampler(run_dir / f"telemetry_{model}.jsonl", srv.pid()).start()
        try:
            for iid in todo:
                if R.free_disk_gb(run_dir) < R.MIN_FREE_DISK_GB:
                    incomplete[model] = f"free disk below {R.MIN_FREE_DISK_GB} GB"
                    break
                for attempt in range(used.get(iid, 0), 3):
                    if srv.proc is None or srv.proc.poll() is not None:
                        srv.stop()
                        srv = start()
                        sampler.pid = srv.pid()
                    try:
                        r = R.run_attempt(srv, model, iid, C.RENDERED2[iid]["text"], S2["max_tokens"], total_s, "stage2",
                                          answer_cap=S2["answer_allowance"])
                    except Exception as e:  # noqa: BLE001
                        r = R.harness_error_record(model, iid, "stage2", S2["max_tokens"], e)
                    r["benchmark"], r["host"] = C.RENDERED2[iid]["benchmark"], C.HOST
                    infra = bool(r["error"]) or r["abort"] in ("first_token_timeout", "stall_timeout", "total_timeout")
                    r["attempt"], r["final_attempt"] = attempt + 1, (not infra) or attempt == 2
                    R.append_jsonl(attempts_path, r)
                    print(f"[stage2 {C.HOST} {model}] {iid} attempt={attempt + 1} finish={r['finish_reason']} "
                          f"abort={r['abort']} error={bool(r['error'])} tokens={r['completion_tokens']} "
                          f"wall={r.get('wall_s')}s", flush=True)
                    R.wait_idle(srv)
                    if not infra:
                        break
                if model in incomplete:
                    break
        except RuntimeError as e:
            incomplete[model] = str(e)[:300]
        finally:
            sampler.stop()
            srv.stop()
        if incomplete.get(model, "").startswith("free disk"):
            break
    return incomplete


def main(args: list[str]) -> None:
    dry = "--dry-run" in args
    models = [a for a in args if not a.startswith("--")] or C.H["models"]
    wrong = [m for m in models if m not in C.H["models"]]
    if wrong:
        raise SystemExit(f"REFUSED: {wrong} not assigned to host {C.HOST} (config_stage2.json hosts)")
    ok, why = approval_ok()
    if not dry and not ok:
        raise SystemExit(f"REFUSED: Stage 2 on {C.HOST} requires the user's approval: {why}")
    import preflight_stage2
    checks = preflight_stage2.run(models)
    for name, passed, detail in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name} {detail}")
    failed = [c for c in checks if not c[1] and not (dry and c[0].startswith("approval"))]
    p = plan(models)
    print(f"\nStage 2 plan on {C.HOST}: " + ", ".join(f"{m} ({len(i)} items)" for m, i in p))
    if dry:
        print(f"DRY RUN: nothing generated. {len(failed)} blocking preflight failure(s).")
        return
    if failed:
        raise SystemExit(f"REFUSED: {len(failed)} preflight check(s) failed")
    lock = C.llm_server.acquire_runner_lock(f"stage2 {C.HOST}")
    C.llm_server.keep_awake(True)
    try:
        C.RUN_DIR.mkdir(parents=True, exist_ok=True)
        (C.RUN_DIR / "RUN_INFO.json").write_text(json.dumps({"started": R.now(), "host": C.host_info(),
                                                             "freeze_sha256": C.sha(FREEZE), "models": models}, indent=1))
        incomplete = run_items(p, C.RUN_DIR)
    finally:
        C.llm_server.keep_awake(False)
        C.llm_server.release_runner_lock(lock)
    if incomplete:
        raise SystemExit(f"STAGE 2 INCOMPLETE on {C.HOST} (resumable; rerun the same command): {incomplete}")
    print(f"STAGE 2 GENERATION COMPLETE on {C.HOST}: {C.RUN_DIR}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])

"""Policy B forced-item sensitivity rerun (local/stage2/FORCED_RERUN_POLICY.json). SENSITIVITY ONLY: the official
Stage 2 result is never read, changed or replaced.

    MORGAN_HOST=<host> python local/stage2/run_forced_rerun.py <model> [--dry-run] [--resume]

Reruns exactly the items in local/stage2/sensitivity/forced_rerun_selection_<host>_<model>.json (hash pinned below)
with the Stage 2 loop of run_stage2.run_items; the only changes are the policy's rerun_settings:
  thinking_budget 16,384 -> 24,576 (llama-server --reasoning-budget), max_tokens 18,560 -> 26,752 (same construction),
  n_ctx recomputed with the same n_ctx_rule (max_tokens + longest Stage 2 prompt from the frozen probe + 1,024,
  rounded up to 256), placement from the same approved rule at that n_ctx, watchdog total from the same formula.
Answer allowance, budget message, model, GGUF, template, sampling, per-item seed and prompts are unchanged.
Output: local/runs/stage2-forced-rerun-<host>/ (refuses if it exists, unless --resume).
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

import placement  # noqa: E402
import run_local as R  # noqa: E402
from llm_server import MODEL_DIR, PINS, Server  # noqa: E402
from telemetry import Sampler  # noqa: E402

SELECTION_SHA256 = {("local-rtx4060", "gpt-oss-20b"): "b9b5e6d604d617df71e460e413a24d9d2226827d18c4fcbe02e90cd9a9f2d445"}
POLICY_SHA256 = "73dfe4a98f950ac2f5e3b4ae6d6c13d7f6cdfd10cb5f70128aa0c4ed6f15d976"
OUT = C.RUNS / f"stage2-forced-rerun-{C.HOST}"


def settings(model: str) -> dict:
    policy = json.loads((C.HERE / "FORCED_RERUN_POLICY.json").read_text(encoding="utf-8"))
    rs, s2 = policy["rerun_settings"], C.CONFIG2
    probe = json.loads((C.PROBE_DIR / f"probe_{model}.json").read_text(encoding="utf-8"))
    max_tokens = rs["thinking_budget"] + rs["answer_allowance"] + (s2["max_tokens"] - s2["thinking_budget"] - s2["answer_allowance"])
    n_ctx = R.round_up(max_tokens + probe["prompt_tokens"]["max"] + 1024)
    deep = probe["speed_deep_16k"]["tg_tok_s_at_depth"]
    return {"thinking_budget": rs["thinking_budget"], "answer_allowance": rs["answer_allowance"], "max_tokens": max_tokens,
            "budget_message": s2["budget_message"], "n_ctx": n_ctx, "longest_prompt_tokens": probe["prompt_tokens"]["max"],
            "watchdog_total_s": round(1.5 * max_tokens / max(0.5, 0.8 * deep) + 1800),
            "official": {"thinking_budget": s2["thinking_budget"], "answer_allowance": s2["answer_allowance"],
                         "max_tokens": s2["max_tokens"], "n_ctx": probe["n_ctx"], "placement_args": probe["placement"]["args"]}}


def checks(model: str, resume: bool) -> tuple[list[tuple[str, bool, str]], list[str], dict]:
    res = []

    def check(name, ok, detail=""):
        res.append((name, bool(ok), detail))

    sel_path = C.HERE / "sensitivity" / f"forced_rerun_selection_{C.HOST}_{model}.json"
    want = SELECTION_SHA256.get((C.HOST, model))
    got = C.sha(sel_path) if sel_path.exists() else None
    check("selection record matches its committed hash", want and got == want, f"{(got or 'missing')[:16]}…")
    committed = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", str(sel_path)], cwd=C.LOCAL.parent).returncode == 0
    check("selection record unchanged from the git commit", committed)
    sel = json.loads(sel_path.read_text(encoding="utf-8")) if got else {"selected_item_ids": []}
    check("policy file matches its committed hash", C.sha(C.HERE / "FORCED_RERUN_POLICY.json") == POLICY_SHA256)
    ids = sel["selected_item_ids"]
    check("selected items are forced items of the official run and in the rendered panel",
          len(ids) == sel.get("selected_count") and set(ids) <= set(sel.get("forced_item_ids_sorted", []))
          and all(i in C.RENDERED2 for i in ids), f"{len(ids)} items")
    s = settings(model)
    check("only the reasoning budget changes (answer allowance and budget message unchanged)",
          s["thinking_budget"] == 24576 and s["answer_allowance"] == C.CONFIG2["answer_allowance"] == 2048
          and s["max_tokens"] == 26752, f"max_tokens {s['max_tokens']} n_ctx {s['n_ctx']}")
    official_dir = C.RUN_DIR
    sums = C.RUNS / f"stage2-{C.HOST}.SHA256SUMS"
    bad = []
    for line in sums.read_text(encoding="utf-8").splitlines():
        h, name = line.split(" *", 1)
        if C.sha(C.RUNS / name) != h:
            bad.append(name)
    check("official Stage 2 raw outputs match their hash manifest", not bad, f"{official_dir.name}" + (f" changed {bad}" if bad else ""))
    check("rerun output directory is new" if not resume else "rerun output directory present (resume)",
          OUT.exists() == resume, str(OUT.relative_to(C.LOCAL.parent)))
    import psutil
    others = [p.info["pid"] for p in psutil.process_iter(["pid", "name", "cmdline"])
              if "llama-server" in (p.info["name"] or "") or any(m in " ".join(p.info["cmdline"] or []).lower()
                                                                  for m in ("qwen3.8", "gemma-4", "run_stage2.py"))]
    check("no llama-server, Qwen3.8, Gemma or Stage 2 runner process", not others, str(others))
    return res, ids, s


FRESHNESS = "no overlap with Stage 1 / calibration / probe / any previous run"
TESTS = "Stage 2 offline tests pass"


def post_run_equivalents() -> list[tuple[str, bool, str]]:
    """The two pre-run checks that fail by construction once the official Stage 2 run exists (its own attempts are
    'previous runs'), re-checked with only the official Stage 2 outputs excluded; the frozen files are not changed."""
    import glob
    import unittest

    import select_stage2
    base = select_stage2.used_ids
    official = {str(C.RUN_DIR), str(C.RUNS / f"{C.RUN_DIR.name}.raw-backup"), str(OUT)}
    real_glob = glob.glob
    try:
        glob.glob = lambda p, recursive=False: [f for f in real_glob(p, recursive=recursive)
                                                if str(Path(f).parent) not in official]
        used, _ = base()
    finally:
        glob.glob = real_glob
    ids = {p["item_id"] for p in C.PANEL2}
    dev = {i["item_id"] for i in json.loads((C.LOCAL.parent / "manifest/items/items_dev.json").read_text(encoding="utf-8"))}
    out = [(FRESHNESS + " (excluding the official Stage 2 run's own outputs)",
            not ids & used and not ids & dev and not ids & set(C.PROBE_ITEMS), f"{len(used)} excluded ids")]
    import test_stage2
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_stage2)
    result = unittest.TestResult()
    suite.run(result)
    bad = sorted(t.id().rsplit(".", 1)[-1] for t, _ in result.failures + result.errors)
    out.append((TESTS + " (all except the pre-run freshness test above)",
                set(bad) <= {"test_disjoint_from_everything_used"}, f"{result.testsRun} run; failing {bad}"))
    return out


def main(args: list[str]) -> None:
    model = next(a for a in args if not a.startswith("--"))
    dry, resume = "--dry-run" in args, "--resume" in args
    if model not in C.H["models"]:
        raise SystemExit(f"REFUSED: {model} is not assigned to host {C.HOST}")
    import preflight_stage2
    pre = preflight_stage2.run([model], full_hash=not resume)
    pre = [c for c in pre if c[0] not in (FRESHNESS, TESTS)] + post_run_equivalents()
    own, ids, s = checks(model, resume)
    for name, ok, detail in pre + own:
        print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
    failed = [c for c in pre + own if not c[1]]
    print(f"\n{len(pre + own) - len(failed)}/{len(pre + own)} checks passed; rerun plan: {model}, {len(ids)} items, "
          f"settings {json.dumps({k: v for k, v in s.items() if k != 'official'})}")
    if failed:
        raise SystemExit(f"REFUSED: {len(failed)} check(s) failed")
    pargs, pinfo = placement.placement_args(model, MODEL_DIR / PINS[model]["file"], s["n_ctx"])
    print(f"placement at n_ctx {s['n_ctx']}: {pargs} {pinfo}")
    if dry:
        print("DRY RUN: nothing generated.")
        return
    lock = C.llm_server.acquire_runner_lock(f"stage2 forced rerun {C.HOST}")
    C.llm_server.keep_awake(True)
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        info = OUT / "RUN_INFO.json"
        if not info.exists():
            info.write_text(json.dumps({"started": R.now(), "purpose": "Policy B sensitivity rerun (not the official score)",
                                        "host": C.host_info(), "model": model, "selected_item_ids": ids, "settings": s,
                                        "placement_args": pargs, "placement": pinfo,
                                        "selection_sha256": SELECTION_SHA256[(C.HOST, model)],
                                        "policy_sha256": POLICY_SHA256,
                                        "freeze_sha256": C.sha(C.HERE / "items" / f"stage2_freeze_{C.HOST}.json")}, indent=1),
                            encoding="utf-8")
        incomplete = run(model, ids, s, pargs, pinfo)
    finally:
        C.llm_server.keep_awake(False)
        C.llm_server.release_runner_lock(lock)
    if incomplete:
        raise SystemExit(f"FORCED RERUN INCOMPLETE (resumable with --resume): {incomplete}")
    print(f"FORCED RERUN COMPLETE: {OUT}", flush=True)


def run(model: str, ids: list[str], s: dict, pargs: list[str], pinfo: dict) -> str | None:
    """run_stage2.run_items for one model with the rerun settings (same retries, resume, server restarts)."""
    attempts_path = OUT / f"attempts_{model}.jsonl"
    done, used = R.completed_items(attempts_path), R.attempts_used(attempts_path)
    todo = [i for i in ids if i not in done]
    if not todo:
        return None
    R.append_jsonl(attempts_path, {"kind": "server_start", "model": model, "host": C.HOST, "timestamp": R.now(),
                                   "n_ctx": s["n_ctx"], "placement": pinfo, "placement_args": pargs,
                                   "reasoning_budget": s["thinking_budget"], "watchdog_total_s": s["watchdog_total_s"]})

    def start():
        last = None
        for k in range(3):
            srv = Server(model, s["n_ctx"], OUT / f"server_{model}_{int(time.time())}.log", threads=C.server_threads(),
                         extra_args=pargs, reasoning_budget=s["thinking_budget"], budget_message=s["budget_message"])
            try:
                li = srv.start()
                R.append_jsonl(attempts_path, {"kind": "server_ready", "model": model, "timestamp": R.now(),
                                               "load_seconds": li.load_seconds, "layers": li.layers_offloaded,
                                               "gpu_model_mib": li.gpu_model_mib, "kv_mib": li.kv_mib,
                                               "n_ctx_reported": li.n_ctx, "pid": srv.pid()})
                return srv
            except Exception as e:  # noqa: BLE001
                srv.stop()
                last = e
                R.append_jsonl(attempts_path, {"kind": "server_start_failed", "model": model, "timestamp": R.now(),
                                               "try": k + 1, "error": repr(e)[:500]})
                time.sleep(20)
        raise RuntimeError(f"server failed to start 3 times: {last!r}")

    try:
        srv = start()
    except RuntimeError as e:
        return str(e)[:300]
    sampler = Sampler(OUT / f"telemetry_{model}.jsonl", srv.pid()).start()
    try:
        for iid in todo:
            if R.free_disk_gb(OUT) < R.MIN_FREE_DISK_GB:
                return f"free disk below {R.MIN_FREE_DISK_GB} GB"
            for attempt in range(used.get(iid, 0), 3):
                if srv.proc is None or srv.proc.poll() is not None:
                    srv.stop()
                    srv = start()
                    sampler.pid = srv.pid()
                try:
                    r = R.run_attempt(srv, model, iid, C.RENDERED2[iid]["text"], s["max_tokens"], s["watchdog_total_s"],
                                      "stage2-forced-rerun", answer_cap=s["answer_allowance"])
                except Exception as e:  # noqa: BLE001
                    r = R.harness_error_record(model, iid, "stage2-forced-rerun", s["max_tokens"], e)
                r["benchmark"], r["host"] = C.RENDERED2[iid]["benchmark"], C.HOST
                infra = bool(r["error"]) or r["abort"] in ("first_token_timeout", "stall_timeout", "total_timeout")
                r["attempt"], r["final_attempt"] = attempt + 1, (not infra) or attempt == 2
                R.append_jsonl(attempts_path, r)
                print(f"[forced-rerun {C.HOST} {model}] {iid} attempt={attempt + 1} finish={r['finish_reason']} "
                      f"abort={r['abort']} error={bool(r['error'])} tokens={r['completion_tokens']} "
                      f"wall={r.get('wall_s')}s", flush=True)
                R.wait_idle(srv)
                if not infra:
                    break
    except RuntimeError as e:
        return str(e)[:300]
    finally:
        sampler.stop()
        srv.stop()
    return None


if __name__ == "__main__":
    main(sys.argv[1:])

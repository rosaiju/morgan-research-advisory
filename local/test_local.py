"""Offline tests for the local harness (no model, no server, no network).

    local\\.venv\\Scripts\\python.exe local/test_local.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import analyze_calibration as A  # noqa: E402
import placement  # noqa: E402
import client  # noqa: E402
import llm_server  # noqa: E402
import score_local  # noqa: E402

CFG = json.loads((HERE / "config_local.json").read_text(encoding="utf-8"))
PINS = json.loads((HERE / "gguf_pins.json").read_text(encoding="utf-8"))


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


class LoopStop(unittest.TestCase):
    def test_exact_repetition_triggers(self):
        cycle = [f"t{i}" for i in range(12)]
        self.assertTrue(client.loop_detected(["x"] * 100 + cycle * 25))

    def test_19_repeats_do_not_trigger(self):
        cycle = [f"t{i}" for i in range(12)]
        filler = [f"u{i}" for i in range(1500)]
        self.assertFalse(client.loop_detected(filler + cycle * 19))

    def test_normal_text_does_not_trigger(self):
        words = [f"w{i % 997}_{i // 997}" for i in range(4000)]
        self.assertFalse(client.loop_detected(words))

    def test_only_last_2048_tokens_considered(self):
        cycle = [f"t{i}" for i in range(12)]
        old_loop = cycle * 30
        fresh = [f"f{i}" for i in range(2100)]
        self.assertFalse(client.loop_detected(old_loop + fresh))


class Status(unittest.TestCase):
    base = {"reasoning_text": "r", "final_text": "ANSWER: 4", "error": None, "abort": None}

    def test_loop_terminated_is_budget_truncated(self):
        st, fl = score_local.pre_status({**self.base, "abort": "loop_terminated", "finish_reason": None})
        self.assertEqual(st, "BUDGET_TRUNCATED")
        self.assertIn("loop_terminated", fl)

    def test_watchdog_is_infrastructure(self):
        st, _ = score_local.pre_status({**self.base, "abort": "stall_timeout", "finish_reason": None})
        self.assertEqual(st, "INFRASTRUCTURE_FAILURE")

    def test_length_is_budget_truncated(self):
        st, _ = score_local.pre_status({**self.base, "finish_reason": "length"})
        self.assertEqual(st, "BUDGET_TRUNCATED")

    def test_empty_final_is_no_final_answer(self):
        st, _ = score_local.pre_status({**self.base, "final_text": "  ", "finish_reason": "stop"})
        self.assertEqual(st, "NO_FINAL_ANSWER")

    def test_unparsed_reasoning_is_malformed(self):
        st, fl = score_local.pre_status({**self.base, "final_text": "<think>x</think> ANSWER: 4", "finish_reason": "stop"})
        self.assertEqual(st, "MALFORMED_NATIVE_OUTPUT")

    def test_normal_stop_is_scorable(self):
        st, _ = score_local.pre_status({**self.base, "finish_reason": "stop"})
        self.assertEqual(st, "SCORABLE")


class LogParse(unittest.TestCase):
    LOG = """0.00.788.638 I load_tensors: offloaded 30/37 layers to GPU
0.00.788.643 I load_tensors:   CPU_Mapped model buffer size =   1125.60 MiB
0.00.788.644 I load_tensors:        CUDA0 model buffer size =  3663.59 MiB
0.02.069.071 I llama_kv_cache:      CUDA0 KV buffer size =   2467.12 MiB
0.02.077.128 I llama_kv_cache: size = 2467.12 MiB ( 33024 cells,  36 layers,  1/1 seqs), K (q8_0): 1233.56 MiB
0.02.084.383 I sched_reserve:      CUDA0 compute buffer size =   304.11 MiB
0.00.321.301 I common_params_fit_impl:   - CUDA0 (NVIDIA GeForce RTX 4060): 30 layers,   5955 MiB used,   1140 MiB free
"""

    def test_parse(self):
        i = llm_server.parse_log(self.LOG)
        self.assertEqual(i.layers_offloaded, "30/37")
        self.assertAlmostEqual(i.gpu_model_mib, 3663.59)
        self.assertAlmostEqual(i.cpu_model_mib, 1125.60)
        self.assertAlmostEqual(i.kv_mib, 2467.12)  # counted once, not twice
        self.assertAlmostEqual(i.compute_gpu_mib, 304.11)
        self.assertEqual(i.gpu_weight_fraction, 0.765)


class C1Rule(unittest.TestCase):
    @staticmethod
    def att(tokens, finish="stop", abort=None):
        return {"completion_tokens": tokens, "finish_reason": finish, "abort": abort}

    def test_smallest_passing_rung(self):
        a = {m: [self.att(3000)] * 6 for m in "abcdefg"}
        a["a"] = [self.att(10000)] + [self.att(3000)] * 5      # one natural completion above 8K
        c1, table = A.choose_c1(a)
        self.assertEqual(c1, 8192)                             # 1 per model and 1 total: allowed
        self.assertTrue(table[8192]["passes"])

    def test_two_from_one_model_forces_higher_rung(self):
        a = {m: [self.att(3000)] * 6 for m in "abcdefg"}
        a["a"] = [self.att(10000), self.att(13000)] + [self.att(3000)] * 4
        c1, table = A.choose_c1(a)
        self.assertFalse(table[8192]["passes"])                 # 2 from one model above 8K
        self.assertEqual(c1, 12288)                             # only 13000 exceeds 12K -> 1 per model

    def test_three_total_forces_higher_rung(self):
        a = {m: [self.att(3000)] * 6 for m in "abcdefg"}
        for m in "abc":
            a[m] = [self.att(9000)] + [self.att(3000)] * 5
        c1, _ = A.choose_c1(a)
        self.assertEqual(c1, 12288)

    def test_loops_and_dev_truncations_are_censored_not_counted(self):
        a = {m: [self.att(3000)] * 6 for m in "abcdefg"}
        a["a"] = [self.att(24576, "length"), self.att(15000, None, "loop_terminated")] + [self.att(3000)] * 4
        c1, _ = A.choose_c1(a)
        self.assertEqual(c1, 8192)


class PlacementParse(unittest.TestCase):
    BREAKDOWN_ONLY = ("I common_memory_breakdown_print: |   - CUDA0 (RTX 4060)   |  8187 = 7096 + ( 6729 =  6199 +     122 +     407)"
                      " +       -5637 |" + chr(10))
    SUMMARY = "I common_params_fit_impl: projected to use 5742 MiB of device memory vs. 7096 MiB of free device memory" + chr(10)

    def _run(self, outputs):
        import types
        calls = iter(outputs)
        orig = placement.subprocess.run
        placement.subprocess.run = lambda *a, **k: types.SimpleNamespace(stdout=next(calls), stderr="")
        try:
            return placement.projected(Path("x.gguf"), 4096, 3)
        finally:
            placement.subprocess.run = orig

    def test_summary_line(self):
        self.assertEqual(self._run([self.SUMMARY]), (5742, 7096))

    def test_breakdown_fallback_when_summary_missing(self):  # bug seen live on Muse 2026-10-03
        self.assertEqual(self._run([self.BREAKDOWN_ONLY]), (6729, 7096))

    def test_retry_then_fail(self):
        with self.assertRaises(RuntimeError):
            self._run(["garbage", "garbage", "garbage"])

    def test_ffn_regex_covers_first_k_layers(self):
        import re
        rx = placement.ffn_override(3).split("=")[0]
        self.assertTrue(re.fullmatch(rx + ".*", "blk.2.ffn_down.weight"))
        self.assertFalse(re.fullmatch(rx + ".*", "blk.3.ffn_down.weight"))
        self.assertFalse(re.fullmatch(rx + ".*", "blk.1.attn_q.weight"))


class BudgetStatus(unittest.TestCase):
    base = {"reasoning_text": "r", "final_text": "ANSWER: 4", "error": None, "abort": None, "finish_reason": "stop"}

    def test_forced_then_answered_is_scorable_and_flagged(self):
        st, fl = score_local.pre_status({**self.base, "reasoning_text": "x Time is up. I must stop thinking now and give"})
        self.assertEqual(st, "SCORABLE")
        self.assertIn("forced_conclusion", fl)

    def test_answer_overflow_is_budget_truncated(self):
        st, fl = score_local.pre_status({**self.base, "abort": "answer_allowance_exceeded"})
        self.assertEqual(st, "BUDGET_TRUNCATED")
        self.assertIn("answer_allowance_exceeded", fl)

    def test_token_count_failure_is_retried_and_recorded(self):  # live bug: Ministral probe counts were silently None
        import inspect
        import run_local
        src = inspect.getsource(run_local.run_attempt)
        self.assertIn("token_count_error", src)
        self.assertIn("for _ in range(3)", src)
        self.assertNotIn("except Exception:\n        pass", src)

    def test_answer_cap_stops_stream_logic_present(self):
        import inspect
        self.assertIn("answer_allowance_exceeded", inspect.getsource(client.stream_chat))


class Resume(unittest.TestCase):
    def test_completed_items_skips_only_final_attempts_and_tolerates_partial_line(self):
        import tempfile
        import run_local
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "attempts_x.jsonl"
            rows = [{"kind": "server_start"},
                    {"kind": "item", "item_id": "a", "final_attempt": True},
                    {"kind": "item", "item_id": "b", "final_attempt": False},   # infra failure, rerun pending
                    {"kind": "integration", "item_id": "c", "final_attempt": True}]
            p.write_text("".join(json.dumps(r) + chr(10) for r in rows) + '{"kind": "item", "item_id": "d", "fin', encoding="utf-8")
            self.assertEqual(run_local.completed_items(p), {"a"})

    def test_append_after_partial_line_keeps_new_record(self):
        import tempfile
        import run_local
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "attempts_x.jsonl"
            p.write_text(json.dumps({"kind": "item", "item_id": "a", "final_attempt": True, "attempt": 1}) + "\n"
                         + '{"kind": "item", "item_id": "b", "fin', encoding="utf-8")   # crash mid-write
            run_local.append_jsonl(p, {"kind": "item", "item_id": "b", "final_attempt": True, "attempt": 2})
            self.assertEqual(run_local.completed_items(p), {"a", "b"})
            self.assertEqual(run_local.attempts_used(p), {"a": 1, "b": 2})

    def test_stage1_plan_is_paired_and_deterministic(self):
        import run_local
        p1, p2 = run_local.stage1_plan(), run_local.stage1_plan()
        self.assertEqual(p1, p2)
        sets = {frozenset(items) for _, items in p1}
        self.assertEqual(len(sets), 1)            # same 22 items for every model
        self.assertEqual(len(next(iter(sets))), 22)


class _FakeServer:
    """Stands in for llm_server.Server in run_items tests: no process, no model."""
    fail_start = 0
    started = 0

    def __init__(self, model, n_ctx, log_path, **kw):
        self.model, self.proc, self.reasoning_budget = model, None, kw.get("reasoning_budget")

    def start(self):
        type(self).started += 1
        if type(self).fail_start > 0:
            type(self).fail_start -= 1
            raise RuntimeError("CUDA error: out of memory (simulated)")
        self.proc = type("P", (), {"poll": lambda s: None, "pid": 1})()
        return llm_server.LoadInfo(load_seconds=0.1)

    def pid(self):
        return 1

    def stop(self):
        self.proc = None


class _FakeSampler:
    def __init__(self, *a, **k):
        self.pid = None

    def start(self):
        return self

    def stop(self):
        return {}


class RunItems(unittest.TestCase):
    """The Stage 1 generation loop with a fake server and scripted attempt outcomes (no model, no network)."""

    def setUp(self):
        import tempfile
        import run_local
        self.rl = run_local
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.saved = (run_local.Server, run_local.Sampler, run_local.run_attempt, run_local.wait_idle,
                      run_local.time.sleep)
        run_local.Server, run_local.Sampler = _FakeServer, _FakeSampler
        run_local.wait_idle = lambda *a, **k: None
        run_local.time.sleep = lambda s: None
        _FakeServer.fail_start, _FakeServer.started = 0, 0
        self.script = {}   # item -> list of outcomes: "ok" | "raise" | "stall"

        def fake_attempt(srv, model, iid, text, max_tokens, total_s, stage, **kw):
            outcome = self.script[iid].pop(0)
            if outcome == "raise":
                raise ConnectionResetError("server went away (simulated)")
            return {"kind": "item", "stage": stage, "model": model, "item_id": iid, "benchmark": "x",
                    "finish_reason": "stop" if outcome == "ok" else None,
                    "abort": "stall_timeout" if outcome == "stall" else None, "error": None,
                    "completion_tokens": 5, "wall_s": 0.1, "reasoning_text": "r", "final_text": "ANSWER: A"}
        run_local.run_attempt = fake_attempt

    def tearDown(self):
        (self.rl.Server, self.rl.Sampler, self.rl.run_attempt, self.rl.wait_idle, self.rl.time.sleep) = self.saved
        self.tmp.cleanup()

    def rows(self, model="r1-0528-qwen3-8b"):
        p = self.dir / f"attempts_{model}.jsonl"
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

    def test_exception_is_recorded_retried_and_capped(self):
        self.script = {"i1": ["raise", "ok"], "i2": ["raise", "stall", "raise"]}
        inc = self.rl.run_items([("r1-0528-qwen3-8b", ["i1", "i2"])], self.dir, "test", texts={"i1": "a", "i2": "b"})
        self.assertEqual(inc, {})
        items = [r for r in self.rows() if r["kind"] == "item"]
        self.assertEqual([(r["item_id"], r["attempt"], r["final_attempt"]) for r in items],
                         [("i1", 1, False), ("i1", 2, True), ("i2", 1, False), ("i2", 2, False), ("i2", 3, True)])
        self.assertTrue(items[0]["error"].startswith("harness_exception: ConnectionResetError"))
        st, _ = score_local.pre_status(items[-1])
        self.assertEqual(st, "INFRASTRUCTURE_FAILURE")

    def test_resume_skips_done_continues_numbering_no_duplicates(self):
        self.script = {"i1": ["ok"], "i2": ["stall"]}
        p = self.dir / "attempts_r1-0528-qwen3-8b.jsonl"
        p.write_text(json.dumps({"kind": "item", "item_id": "i1", "attempt": 1, "final_attempt": True}) + "\n"
                     + json.dumps({"kind": "item", "item_id": "i2", "attempt": 2, "final_attempt": False}) + "\n"
                     + '{"kind": "item", "item_id": "i2", "att', encoding="utf-8")       # killed mid-write
        self.rl.run_items([("r1-0528-qwen3-8b", ["i1", "i2"])], self.dir, "test", texts={"i1": "a", "i2": "b"})
        items = [r for r in self.rows_tolerant() if r.get("kind") == "item"]
        self.assertEqual([(r["item_id"], r["attempt"], r["final_attempt"]) for r in items],
                         [("i1", 1, True), ("i2", 2, False), ("i2", 3, True)])
        self.assertEqual(self.script["i1"], ["ok"])              # i1 was not generated again
        # a second resume generates nothing
        self.rl.run_items([("r1-0528-qwen3-8b", ["i1", "i2"])], self.dir, "test", texts={"i1": "a", "i2": "b"})
        self.assertEqual(len([r for r in self.rows_tolerant() if r.get("kind") == "item"]), 3)

    def rows_tolerant(self):
        out = []
        for l in (self.dir / "attempts_r1-0528-qwen3-8b.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(l))
            except json.JSONDecodeError:
                pass
        return out

    def test_load_failure_retries_then_skips_model_and_continues(self):
        _FakeServer.fail_start = 3          # first model never loads
        self.script = {"i1": ["ok"]}
        inc = self.rl.run_items([("r1-0528-qwen3-8b", ["i1"]), ("gpt-oss-20b", ["i1"])], self.dir, "test",
                                texts={"i1": "a"})
        self.assertIn("r1-0528-qwen3-8b", inc)
        self.assertEqual([r["kind"] for r in self.rows()].count("server_start_failed"), 3)
        self.assertEqual(self.rl.completed_items(self.dir / "attempts_gpt-oss-20b.jsonl"), {"i1"})
        self.assertEqual(self.rl.completed_items(self.dir / "attempts_r1-0528-qwen3-8b.jsonl"), set())

    def test_transient_load_failure_recovers(self):
        _FakeServer.fail_start = 1
        self.script = {"i1": ["ok"]}
        inc = self.rl.run_items([("r1-0528-qwen3-8b", ["i1"])], self.dir, "test", texts={"i1": "a"})
        self.assertEqual(inc, {})
        self.assertEqual(self.rl.completed_items(self.dir / "attempts_r1-0528-qwen3-8b.jsonl"), {"i1"})

    def test_low_disk_stops_cleanly(self):
        self.script = {"i1": ["ok"]}
        saved = self.rl.free_disk_gb
        self.rl.free_disk_gb = lambda p: 1.0
        try:
            inc = self.rl.run_items([("r1-0528-qwen3-8b", ["i1"]), ("gpt-oss-20b", ["i1"])], self.dir, "test",
                                    texts={"i1": "a"})
        finally:
            self.rl.free_disk_gb = saved
        self.assertEqual(list(inc), ["r1-0528-qwen3-8b"])
        self.assertEqual(self.script["i1"], ["ok"])


class Infrastructure(unittest.TestCase):
    def test_malformed_stream_chunk_is_an_error_not_a_crash(self):
        import http.server
        import threading

        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\ndata: {not json\n\n')

            def log_message(self, *a):
                pass
        srv = http.server.HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            rec = client.stream_chat(srv.server_address[1], {"x": 1}, first_token_s=5, stall_s=5, total_s=10)
        finally:
            srv.shutdown()
        self.assertTrue(rec["error"].startswith("malformed stream chunk"))
        self.assertEqual(rec["final_text"], "hi")

    def test_server_refuses_to_start_when_port_taken(self):
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))                      # own ephemeral port: never interferes with a live run
        s.listen(1)
        saved = (llm_server.reap_orphans, llm_server.subprocess.Popen, llm_server.PORT)
        llm_server.PORT = s.getsockname()[1]
        llm_server.reap_orphans = lambda *a, **k: []   # never touch real processes from a test

        def no_launch(*a, **k):
            raise AssertionError("llama-server must not be launched while the port is taken")
        llm_server.subprocess.Popen = no_launch
        try:
            for _ in range(3):                        # also with the listener's backlog already full
                self.assertTrue(llm_server.port_in_use())
            with self.assertRaises(RuntimeError):
                llm_server.Server("r1-0528-qwen3-8b", 4096, HERE / "runs" / "_test_unused.log").start()
        finally:
            llm_server.reap_orphans, llm_server.subprocess.Popen, llm_server.PORT = saved
            s.close()

    def test_runner_lock_refuses_second_live_runner(self):
        import psutil
        saved_port = llm_server.PORT
        llm_server.PORT = 1          # a lock name no real run uses (the lock file is per port)
        lock = HERE / "runs" / f".runner_port{llm_server.PORT}.lock"
        other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        try:
            p = psutil.Process(other.pid)
            lock.write_text(json.dumps({"pid": other.pid, "create_time": p.create_time(), "purpose": "test"}))
            with self.assertRaises(SystemExit):
                llm_server.acquire_runner_lock("test")
            other.kill()
            other.wait()
            got = llm_server.acquire_runner_lock("test")   # stale lock is taken over
            llm_server.release_runner_lock(got)
            self.assertFalse(lock.exists())
        finally:
            if other.poll() is None:
                other.kill()
            lock.unlink(missing_ok=True)
            llm_server.PORT = saved_port


class Manifests(unittest.TestCase):
    def test_every_model_fully_specified(self):
        for key, m in CFG["models"].items():
            self.assertIn(key, PINS)
            self.assertEqual(set(m["sampling"]), {"temperature", "top_p", "top_k", "min_p"}, key)
            self.assertTrue((HERE / m["template_file"]).exists(), key)
            body = client.build_body(m, CFG["common_request"], "hi", 16, 1)
            for k in ("temperature", "top_p", "top_k", "min_p", "presence_penalty", "repeat_penalty", "seed",
                      "max_tokens", "chat_template_kwargs"):
                self.assertIn(k, body)

    def test_item_files_match_lock(self):
        lock = json.loads((HERE / "items/items_lock.json").read_text(encoding="utf-8"))
        for name in ("stage1_panel.json", "calibration_items.json"):
            self.assertEqual(sha(HERE / "items" / name), lock[name], name)
        rlock = json.loads((HERE / "items/rendered_lock.json").read_text(encoding="utf-8"))
        self.assertEqual(sha(HERE / "items/rendered_prompts.json"), rlock["rendered_prompts.json"])
        self.assertEqual(sha(HERE / "items/items_lock.json"), rlock["from_items_lock"])

    def test_selection_is_reproducible(self):
        before = {n: sha(HERE / "items" / n) for n in ("stage1_panel.json", "calibration_items.json")}
        subprocess.run([sys.executable, str(HERE / "select_items.py")], check=True, capture_output=True)
        after = {n: sha(HERE / "items" / n) for n in before}
        self.assertEqual(before, after)

    def test_stage1_is_refused(self):
        # Once the user has approved, `run_local.py stage1` is the real run (and its preflight runs these tests):
        # launching it from here would recurse. The gate is only testable while no approval exists.
        if (HERE / "STAGE1_APPROVED.json").exists():
            self.skipTest("Stage 1 approved; refusal gate not applicable (and launching it here would recurse)")
        p = subprocess.run([sys.executable, str(HERE / "run_local.py"), "stage1"], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("REFUSED", p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)

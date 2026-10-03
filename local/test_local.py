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
        p = subprocess.run([sys.executable, str(HERE / "run_local.py"), "stage1"], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("REFUSED", p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)

"""Offline tests: no network, no keys, no inference.   python runner/test_offline.py"""

import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adapters as A  # noqa: E402
import status as S  # noqa: E402

ROUTES = A.load_routes()
FAKE_KEY = "sk-" + "x" * 40


def sse(*chunks):
    return [f"data: {json.dumps(c)}\n" for c in chunks] + [": keep-alive\n", "data: [DONE]\n"]


class Routes(unittest.TestCase):
    def test_every_model_has_a_route(self):
        self.assertEqual({r.model for r in ROUTES.values()}, {"P35", "P25", "P28", "P27", "P29", "P34"})

    def test_payloads_contain_ceiling_and_no_secret(self):
        os.environ["DEEPSEEK_API_KEY"] = FAKE_KEY
        for rid, r in ROUTES.items():
            if r.api_style == "openai_completions_raw":
                continue
            body = A.build_request(r, "What is 2+2?", 131072, "mmlu_pro/1")
            self.assertEqual(body[r.max_output_param], 131072, rid)
            self.assertNotIn(FAKE_KEY, json.dumps(body))
            self.assertEqual(A.payload_sha256(body), A.payload_sha256(json.loads(json.dumps(body))))
        del os.environ["DEEPSEEK_API_KEY"]

    def test_effort_values_are_explicit(self):
        self.assertEqual(ROUTES["P25-deepseek"].body["reasoning_effort"], "max")
        self.assertEqual(ROUTES["P28-zai"].body["reasoning_effort"], "max")
        self.assertEqual(ROUTES["P27-zai"].body["reasoning_effort"], "max")
        self.assertEqual(ROUTES["P29-moonshot"].body["reasoning_effort"], "max")
        self.assertTrue(ROUTES["P35-deepinfra"].body["chat_template_kwargs"]["enable_thinking"])
        self.assertEqual(ROUTES["P34-deepinfra-fp4"].body["chat_template_kwargs"]["reasoning_effort"], "xhigh")
        self.assertIs(ROUTES["P28-zai"].body["do_sample"], True)

    def test_ceiling_above_route_limit_is_refused(self):
        with self.assertRaises(ValueError):
            A.build_request(ROUTES["P28-zai"], "x", 131073, "i")
        A.build_request(ROUTES["P25-deepseek"], "x", 393216, "i")

    def test_seed_rule_matches_manifest(self):
        import hashlib
        iid = "bbeh/boolean_expressions/17"
        self.assertEqual(A.item_seed(iid), int(hashlib.sha256(f"Morgan-2026-09-29|{iid}".encode()).hexdigest()[:8], 16) & 0x7FFFFFFF)
        body = A.build_request(ROUTES["P35-deepinfra"], "x", 1000, iid)
        self.assertEqual(body["seed"], A.item_seed(iid))
        self.assertNotIn("seed", A.build_request(ROUTES["P29-moonshot"], "x", 1000, iid))


class Parsing(unittest.TestCase):
    def test_chat_stream_with_reasoning_and_usage(self):
        lines = sse({"model": "m", "choices": [{"delta": {"reasoning_content": "think "}}]},
                    {"choices": [{"delta": {"reasoning_content": "more"}}]},
                    {"choices": [{"delta": {"content": "The answer is: 7"}, "finish_reason": "stop"}]},
                    {"choices": [], "usage": {"prompt_tokens": 10, "completion_tokens": 20,
                                              "completion_tokens_details": {"reasoning_tokens": 15}}})
        rec = A.normalise(ROUTES["P25-deepseek"], A.parse_sse(lines))
        self.assertEqual(rec["reasoning_text"], "think more")
        self.assertEqual(rec["final_text"], "The answer is: 7")
        self.assertEqual((rec["completion_tokens"], rec["reasoning_tokens"]), (20, 15))
        self.assertEqual(S.classify(rec)[0], "SCORABLE")
        self.assertAlmostEqual(A.estimated_cost(ROUTES["P25-deepseek"], rec), 10 / 1e6 * 0.66 + 20 / 1e6 * 1.98)

    def test_raw_completion_split(self):
        lines = sse({"choices": [{"text": "reason</think>\n\nANSWER: 3", "finish_reason": "stop", "stop_reason": 248046}]})
        rec = A.normalise(ROUTES["P34-dedicated-fp8"], A.parse_sse(lines))
        self.assertEqual((rec["reasoning_text"], rec["final_text"], rec["stop_detail"]), ("reason", "ANSWER: 3", 248046))

    def test_answer_only_in_reasoning_is_not_final(self):
        lines = sse({"choices": [{"delta": {"reasoning_content": "The answer is: 7"}, "finish_reason": "stop"}]})
        rec = A.normalise(ROUTES["P29-moonshot"], A.parse_sse(lines))
        self.assertEqual(S.classify(rec)[0], "NO_FINAL_ANSWER")


class Status(unittest.TestCase):
    def rec(self, finish, final="x", reasoning="r"):
        return {"finish_reason": finish, "final_text": final, "reasoning_text": reasoning}

    def test_precedence(self):
        self.assertEqual(S.classify(self.rec("stop"), transport_error=True)[0], "INFRASTRUCTURE_FAILURE")
        self.assertEqual(S.classify(self.rec("insufficient_system_resource"))[0], "INFRASTRUCTURE_FAILURE")
        self.assertEqual(S.classify(self.rec(None))[0], "INFRASTRUCTURE_FAILURE")
        self.assertEqual(S.classify(self.rec("sensitive"))[0], "PROVIDER_FILTERED")
        self.assertEqual(S.classify(self.rec("tool_calls"))[0], "MALFORMED_NATIVE_OUTPUT")
        self.assertEqual(S.classify(self.rec("length", final=None))[0], "BUDGET_TRUNCATED")
        st, flags = S.classify(self.rec("length", final="partial"))
        self.assertEqual((st, flags), ("BUDGET_TRUNCATED", ["final_channel_after_cap_partial"]))
        self.assertEqual(S.classify(self.rec("stop", final="  "))[0], "NO_FINAL_ANSWER")
        st, flags = S.classify(self.rec("repetition_truncation", final=None))
        self.assertEqual(st, "NO_FINAL_ANSWER"); self.assertIn("provider_repetition_truncation", flags)
        self.assertEqual(S.classify(self.rec("weird"))[0], "MALFORMED_NATIVE_OUTPUT")

    def test_loop_flag(self):
        looping = "the same twelve words repeat again and again in this loop forever now " * 12
        self.assertIn("loop_suspected", S.classify(self.rec("length", final=None, reasoning=looping))[1])


class Gate(unittest.TestCase):
    def test_gate_closed_by_default(self):
        os.environ.pop("MORGAN_ALLOW_NETWORK", None)
        with self.assertRaises(A.GateClosed):
            next(A.Transport("integration").send(ROUTES["P25-deepseek"], {}))

    def test_gate_closed_without_authorization_file(self):
        self.assertFalse(A.AUTH_FILE.exists(), "no stage may be authorised during preparation")
        os.environ["MORGAN_ALLOW_NETWORK"] = "1"
        try:
            with self.assertRaises(A.GateClosed):
                A.check_gate("integration", ROUTES["P25-deepseek"])
        finally:
            os.environ.pop("MORGAN_ALLOW_NETWORK")

    def test_redaction(self):
        self.assertNotIn(FAKE_KEY, A.redact(f"error Bearer {FAKE_KEY} {FAKE_KEY}"))


class IntegrationPlan(unittest.TestCase):
    def test_dry_run_builds_34_and_t5_repeats_t1(self):
        import run_integration as R
        reqs = R.planned_requests()
        self.assertEqual(len(reqs), 34)
        by = {(r["route_id"], r["test"]): r["payload_sha256"] for r in reqs}
        for route_id in R.PLAN["routes_in_first_paid_test"]:
            self.assertEqual(by[(route_id, "T1")], by[(route_id, "T5")], route_id)
        for r in reqs:
            self.assertNotIn(FAKE_KEY, json.dumps(r["body"]))
            if r["test"] == "T4":
                self.assertIn("maxx", json.dumps(r["body"]))

    def test_send_refused_without_gate(self):
        import run_integration as R
        os.environ.pop("MORGAN_ALLOW_NETWORK", None)
        with self.assertRaises(A.GateClosed):
            sys.argv = ["run_integration.py", "--send"]
            R.main()


class QwenRendering(unittest.TestCase):
    def test_client_rendered_prompt(self):
        try:
            import jinja2  # noqa: F401
        except ImportError:
            self.skipTest("jinja2 not installed (needed only for the dedicated Qwen route)")
        body = A.build_request(ROUTES["P34-dedicated-fp8"], "What is 2+2?", 131072, "math500/x")
        p = body["prompt"]
        self.assertTrue(p.endswith("<|im_start|>assistant\n<think>\n"), repr(p[-60:]))
        self.assertIn("Reasoning effort is set to xhigh", p)
        self.assertEqual((body["top_k"], body["min_p"]), (20, 0.0))


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Offline tests for Stage 2 preparation (no model, no server, never launches run_stage2).

    python local/stage2/test_stage2.py
"""
from __future__ import annotations

import collections
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import run_stage2  # noqa: E402
import select_stage2  # noqa: E402


class Panel(unittest.TestCase):
    def test_composition_and_uniqueness(self):
        ids = [p["item_id"] for p in C.PANEL2]
        self.assertEqual(len(ids), 284)
        self.assertEqual(len(set(ids)), 284)
        self.assertEqual(dict(collections.Counter(p["benchmark"] for p in C.PANEL2)),
                         {"mmlu_pro": 61, "math500": 58, "bbeh_mini": 67, "ifeval": 80, "student": 18})

    def test_disjoint_from_everything_used(self):
        used, _ = select_stage2.used_ids()
        ids = {p["item_id"] for p in C.PANEL2}
        self.assertFalse(ids & used)
        self.assertFalse(ids & set(C.PROBE_ITEMS))
        dev = {i["item_id"] for i in json.loads((C.LOCAL.parent / "manifest/items/items_dev.json").read_text(encoding="utf-8"))}
        self.assertFalse(ids & dev)
        self.assertTrue(set(C.PROBE_ITEMS) <= dev | {"ifeval/1012"})

    def test_locks(self):
        lock = json.loads((C.HERE / "items/stage2_items_lock.json").read_text(encoding="utf-8"))
        self.assertEqual(C.sha(C.HERE / "items/stage2_panel.json"), lock["stage2_panel.json"])
        rl = json.loads((C.HERE / "items/stage2_rendered_lock.json").read_text(encoding="utf-8"))
        self.assertEqual(C.sha(C.HERE / "items/stage2_rendered.json"), rl["stage2_rendered.json"])
        self.assertTrue(all(p["item_id"] in C.RENDERED2 for p in C.PANEL2))

    def test_plan_paired_and_deterministic(self):
        p1, p2 = run_stage2.plan(C.CONFIG2["finalists"]), run_stage2.plan(C.CONFIG2["finalists"])
        self.assertEqual(p1, p2)
        self.assertEqual(len({frozenset(i) for _, i in p1}), 1)


class Config(unittest.TestCase):
    def test_budget_and_inheritance(self):
        s2 = C.CONFIG2
        self.assertEqual((s2["thinking_budget"], s2["answer_allowance"], s2["max_tokens"]), (16384, 2048, 18560))
        stage1 = json.loads((C.LOCAL / "config_local.json").read_text(encoding="utf-8"))
        self.assertEqual(s2["budget_message"], stage1["stage1_v2"]["budget_message"])
        for m in s2["finalists"]:
            self.assertIn(m, stage1["models"])
            self.assertEqual(stage1["models"][m].get("forcing", "server"), "server")
        assigned = [m for h in s2["hosts"].values() for m in h["models"]]
        self.assertEqual(sorted(assigned), sorted(s2["finalists"]))


class Gate(unittest.TestCase):
    def test_approval_requires_matching_freeze_hash_and_host(self):
        with tempfile.TemporaryDirectory() as d:
            fz, ap = Path(d) / "freeze.json", Path(d) / "approved.json"
            self.assertFalse(run_stage2.approval_ok(ap, fz)[0])            # nothing written
            fz.write_text('{"x": 1}')
            self.assertFalse(run_stage2.approval_ok(ap, fz)[0])            # no approval
            ap.write_text(json.dumps({"freeze_sha256": "0" * 64, "host": C.HOST}))
            self.assertFalse(run_stage2.approval_ok(ap, fz)[0])            # wrong hash
            ap.write_text(json.dumps({"freeze_sha256": C.sha(fz), "host": "other-host"}))
            self.assertFalse(run_stage2.approval_ok(ap, fz)[0])            # wrong host
            ap.write_text(json.dumps({"freeze_sha256": C.sha(fz), "host": C.HOST}))
            self.assertTrue(run_stage2.approval_ok(ap, fz)[0])

    def test_models_restricted_to_host(self):
        other = [m for m in C.CONFIG2["finalists"] if m not in C.H["models"]]
        with self.assertRaises(SystemExit):
            run_stage2.main(["--dry-run", other[0]])


if __name__ == "__main__":
    unittest.main(verbosity=1)

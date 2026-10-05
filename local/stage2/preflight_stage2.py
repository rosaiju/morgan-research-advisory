"""Stage 2 readiness checks for the models assigned to THIS host (read-only; starts no model).

    MORGAN_HOST=<host> python local/stage2/preflight_stage2.py [--full-hash] [<model> ...]
"""
from __future__ import annotations

import collections
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

TARGET = {"mmlu_pro": 61, "math500": 58, "bbeh_mini": 67, "ifeval": 80, "student": 18}


def run(models: list[str] | None = None, full_hash: bool = False) -> list[tuple[str, bool, str]]:
    import run_stage2
    models = models or C.H["models"]
    s2, res = C.CONFIG2, []

    def check(name, ok, detail=""):
        res.append((name, bool(ok), detail))

    check("budget 16,384 + 2,048 (max_tokens 18,560)", s2["thinking_budget"] == 16384 and s2["answer_allowance"] == 2048
          and s2["max_tokens"] == 18560)
    stage1 = json.loads((C.LOCAL / "config_local.json").read_text(encoding="utf-8"))
    check("forcing message identical to Stage 1", s2["budget_message"] == stage1["stage1_v2"]["budget_message"])
    check("model settings inherited unchanged (config_local.json hash)",
          C.sha(C.LOCAL / "config_local.json") == s2["config_local_sha256_at_creation"])
    items = C.HERE / "items"
    lock = json.loads((items / "stage2_items_lock.json").read_text(encoding="utf-8"))
    check("panel matches its lock", C.sha(items / "stage2_panel.json") == lock["stage2_panel.json"])
    counts = collections.Counter(p["benchmark"] for p in C.PANEL2)
    check("panel composition 61/58/67/80/18 = 284", dict(counts) == TARGET, dict(counts))
    import select_stage2
    used, _ = select_stage2.used_ids()
    ids = {p["item_id"] for p in C.PANEL2}
    dev = {i["item_id"] for i in json.loads((C.LOCAL.parent / "manifest/items/items_dev.json").read_text(encoding="utf-8"))}
    check("no overlap with Stage 1 / calibration / probe / any previous run",
          not ids & used and not ids & dev and not ids & set(C.PROBE_ITEMS), f"{len(used)} excluded ids")
    rl = json.loads((items / "stage2_rendered_lock.json").read_text(encoding="utf-8"))
    check("rendered prompts match lock", C.sha(items / "stage2_rendered.json") == rl["stage2_rendered.json"])
    check("every panel item rendered", all(i in C.RENDERED2 for i in ids))
    ver = C.host_info().get("llama_server_version") or []
    check("llama.cpp commit fb4b2737a (build b11349)", any("fb4b2737" in v for v in ver), " ".join(ver))
    for m in models:
        ok, how = C.weights_ok(m, full_hash)
        check(f"weights verified: {m}", ok, how)
        pr = C.PROBE_DIR / f"probe_{m}.json"
        if pr.exists():
            p = json.loads(pr.read_text(encoding="utf-8"))
            good = (p.get("integration", {}).get("passed") and not p.get("error") and not p.get("skip_long")
                    and p.get("forced_conclusion_ok") and p.get("context_stable_16k"))
            check(f"Stage 2 probe passed on {C.HOST}: {m}", good,
                  f"integration={p.get('integration', {}).get('passed')} forced={p.get('forced_conclusion_ok')} "
                  f"16K={p.get('context_stable_16k')} skip_long={p.get('skip_long')} n_ctx={p.get('n_ctx')}")
        else:
            check(f"Stage 2 probe passed on {C.HOST}: {m}", False, "no probe record")
        check(f"official template present: {m}", (C.LOCAL / stage1["models"][m]["template_file"]).exists())
    freeze = run_stage2.FREEZE
    if freeze.exists():
        fz = json.loads(freeze.read_text(encoding="utf-8"))
        bad = [f for f, h in fz["files"].items() if not (C.LOCAL / f).exists() or C.sha(C.LOCAL / f) != h]
        check(f"every frozen file matches {freeze.name}", not bad, f"{len(fz['files'])} files" + (f"; changed {bad}" if bad else ""))
    else:
        check(f"freeze record {freeze.name}", False, "not frozen yet (local/stage2/freeze_stage2.py)")
    check("free disk >= 20 GB", shutil.disk_usage(C.LOCAL).free / 2**30 >= 20, f"{shutil.disk_usage(C.LOCAL).free / 2**30:.0f} GB")
    p = subprocess.run([sys.executable, str(C.HERE / "test_stage2.py")], capture_output=True, text=True)
    check("Stage 2 offline tests pass", p.returncode == 0, ((p.stdout + p.stderr).strip().splitlines() or [""])[-1])
    ok, why = run_stage2.approval_ok()
    check(f"approval for {C.HOST} present and matches the freeze", ok, why)
    return res


if __name__ == "__main__":
    args = sys.argv[1:]
    r = run([a for a in args if not a.startswith("--")] or None, full_hash="--full-hash" in args)
    for name, ok, detail in r:
        print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
    print(f"\n{sum(ok for _, ok, _ in r)}/{len(r)} checks passed ({C.HOST})")

"""Stage 1 (v2) preflight: every check must pass before any Stage 1 generation. Read-only; starts no model.

    python local/preflight.py            # report only
Used by `run_local.py stage1` (which additionally requires the user's local/STAGE1_APPROVED.json).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MODEL_DIR = Path(os.environ.get("MORGAN_MODEL_DIR", r"C:\llm\models"))
PROBE_ID = os.environ.get("MORGAN_PROBE_ID", "probe-20261003")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha_big(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


def run(full_hash: bool = False) -> list[tuple[str, bool, str]]:
    cfg = json.loads((HERE / "config_local.json").read_text(encoding="utf-8"))
    pins = json.loads((HERE / "gguf_pins.json").read_text(encoding="utf-8"))
    res = []

    def check(name, ok, detail=""):
        res.append((name, bool(ok), detail))

    s1 = cfg.get("stage1_v2", {})
    check("config: stage1_v2 section present", bool(s1))
    check("config: budget 6144 + 1536", s1.get("thinking_budget") == 6144 and s1.get("answer_allowance") == 1536,
          f"{s1.get('thinking_budget')} + {s1.get('answer_allowance')}")
    check("config: stage1_v2 frozen", s1.get("frozen") is True, f"frozen={s1.get('frozen')}")
    freeze = HERE / "items/stage1_v2_freeze.json"
    if freeze.exists():
        fz = json.loads(freeze.read_text(encoding="utf-8"))
        check("config hash matches freeze record", fz.get("config_sha256") == sha(HERE / "config_local.json"))
    else:
        check("freeze record exists (items/stage1_v2_freeze.json)", False)

    # items
    lock = json.loads((HERE / "items/stage1_v2_lock.json").read_text(encoding="utf-8"))
    check("panel v2 matches its lock", sha(HERE / "items/stage1_panel_v2.json") == lock["stage1_panel_v2.json"])
    check("panel v2 derived from locked v1", sha(HERE / "items/stage1_panel.json") == lock["derived_from"]["stage1_panel.json"])
    panel = json.loads((HERE / "items/stage1_panel_v2.json").read_text(encoding="utf-8"))
    cal = json.loads((HERE / "items/calibration_items.json").read_text(encoding="utf-8"))
    check("no Stage 1 / calibration overlap (id + content)",
          not ({p["item_id"] for p in panel} & {c["item_id"] for c in cal})
          and not ({p["content_sha256"] for p in panel} & {c["content_sha256"] for c in cal}))
    probe_items = {"math500/test/geometry/880.json", "ifeval/1012"}
    check("probe items are not Stage 1 items", not ({p["item_id"] for p in panel} & probe_items))
    rl = json.loads((HERE / "items/rendered_lock.json").read_text(encoding="utf-8"))
    rendered = HERE / "items/rendered_prompts.json"
    check("rendered prompts match lock", rendered.exists() and sha(rendered) == rl["rendered_prompts.json"])
    if rendered.exists():
        rp = json.loads(rendered.read_text(encoding="utf-8"))
        check("every panel item has a rendered prompt", all(p["item_id"] in rp for p in panel))
    il = json.loads((ROOT / "manifest/items/item_manifest_lock.json").read_text(encoding="utf-8"))
    for n in ("answer_key_final.json", "answer_key_dev.json"):
        p = ROOT / "manifest/items" / n
        check(f"answer key present and locked: {n}", p.exists() and sha(p) == il[n])

    # models
    for k, pin in pins.items():
        f = MODEL_DIR / pin["file"]
        side = f.with_suffix(".gguf.sha256")
        ok = f.exists() and f.stat().st_size == pin["size"] and side.exists() and side.read_text().strip() == pin["sha256"]
        detail = "sidecar"
        if ok and full_hash:
            ok, detail = sha_big(f) == pin["sha256"], "full re-hash"
        check(f"weights verified: {k}", ok, detail)
        pr = HERE / "runs" / PROBE_ID / f"probe_{k}.json"
        if pr.exists():
            d = json.loads(pr.read_text(encoding="utf-8"))
            check(f"probe passed: {k}", d.get("integration", {}).get("passed") and d.get("forced_conclusion_ok")
                  and not d.get("error"), f"integration={d.get('integration', {}).get('passed')} forced={d.get('forced_conclusion_ok')}")
        else:
            check(f"probe passed: {k}", False, "no probe result")
    for t in {m["template_file"] for m in cfg["models"].values()}:
        check(f"template present: {t}", (HERE / t).exists())
    ol = json.loads((HERE / "official/official-lock.json").read_text(encoding="utf-8"))
    bad = [f"{k}/{f}" for k, e in ol.items() for f, h in e["files"].items()
           if (HERE / "official" / f"{k}__{f}").exists() and sha(HERE / "official" / f"{k}__{f}") != h]
    check("official templates/configs match official-lock.json", not bad, ", ".join(bad))

    # scorers + harness tests
    vpy = ROOT / ".venv-scoring/Scripts/python.exe"
    env = {**os.environ, "NLTK_DATA": str(ROOT / "scoring/vendor/nltk_data"), "PYTHONIOENCODING": "utf-8"}
    p = subprocess.run([str(vpy), "-m", "pytest", "scoring/test_scorers.py", "-q", "-p", "no:cacheprovider"],
                       cwd=ROOT, capture_output=True, text=True, env=env)
    check("scorer fixtures pass", p.returncode == 0, (p.stdout.strip().splitlines() or [""])[-1])
    p = subprocess.run([sys.executable, str(HERE / "test_local.py")], capture_output=True, text=True, env=env)
    check("harness offline tests pass", p.returncode == 0, ((p.stdout + p.stderr).strip().splitlines() or [""])[-1])
    check("Stage 1 approval file present (user-written)", (HERE / "STAGE1_APPROVED.json").exists())
    return res


if __name__ == "__main__":
    r = run(full_hash="--full-hash" in sys.argv)
    for name, ok, detail in r:
        print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
    print(f"\n{sum(ok for _, ok, _ in r)}/{len(r)} checks passed")

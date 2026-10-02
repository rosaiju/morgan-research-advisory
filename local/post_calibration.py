"""After calibration: score, apply the C1 rule, quiet-machine speed re-check, Stage 1 projection, report.

Runs unattended (launched by post_calibration.sh once calibrate_all.sh prints ALL DONE). Never starts Stage 1
and never edits config_local.json; it writes C1 as a CANDIDATE in the report for the user's review.

Steps
  1. score calibration attempts with the locked scorer (.venv-scoring) -> scored.jsonl
  2. C1 = pre-registered rule over all calibrated models (analyze_calibration.choose_c1)
  3. per model, with no downloads running: reload at the calibration context and at the Stage 1 context
     (n_ctx = C1 + longest Stage 1 prompt + 1024), record load time / offload / KV, run the standard speed
     probe (pp512 / tg256, 3 reps) at both
  4. Stage 1 decode estimate = calibration decode-at-depth * (tg256 at Stage 1 ctx / tg256 at calibration ctx)
  5. write calibration_report.json (+ stage1 adjustment) and CALIBRATION_REPORT.md
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import analyze_calibration as A  # noqa: E402
import run_local as R  # noqa: E402
from llm_server import Server  # noqa: E402
from telemetry import gpu_snapshot  # noqa: E402


def downloads_running() -> bool:
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq curl.exe"], capture_output=True, text=True).stdout
    return "curl.exe" in out


def main(run_dir: Path) -> None:
    log = (run_dir / "post_calibration.log").open("a", encoding="utf-8")

    def say(msg):
        line = f"{datetime.now().isoformat(timespec='seconds')} {msg}"
        print(line, flush=True)
        log.write(line + "\n")
        log.flush()

    # 1) scoring
    vpy = ROOT / ".venv-scoring/Scripts/python.exe"
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "NLTK_DATA": str(ROOT / "scoring/vendor/nltk_data")}
    p = subprocess.run([str(vpy), str(HERE / "score_local.py"), str(run_dir)], capture_output=True, text=True, env=env)
    say(f"scoring: {p.stdout.strip()} {p.stderr.strip()[-500:]}")

    # 2) C1 + base projection
    A.main(run_dir)
    report = json.loads((run_dir / "calibration_report.json").read_text(encoding="utf-8"))
    c1 = report["C1"]
    say(f"C1 candidate = {c1}; models = {report['models']}")

    # 3) quiet speed re-check
    while downloads_running():
        say("waiting for downloads to finish before the quiet speed re-check")
        time.sleep(300)
    recheck = {}
    for m in report["models"]:
        s = json.loads((run_dir / f"model_{m}.json").read_text(encoding="utf-8"))
        n_cal = s["n_ctx_calibration"]
        n_s1 = R.round_up(c1 + s["prompt_tokens"]["max_stage1"] + 1024)
        recheck[m] = {"n_ctx_calibration": n_cal, "n_ctx_stage1": n_s1}
        for tag, n in (("calibration_ctx", n_cal), ("stage1_ctx", n_s1)):
            try:
                import psutil
                base = gpu_snapshot()["gpu_mem_used_mib"]
                vm0 = psutil.virtual_memory()
                ram0 = (vm0.total - vm0.available) / 2**20
                srv = Server(m, n, run_dir / f"server_{m}_recheck_{tag}.log")
                li = srv.start()
                vm1 = psutil.virtual_memory()
                ram_delta = round((vm1.total - vm1.available) / 2**20 - ram0, 1)
                proc_ws = round(psutil.Process(srv.pid()).memory_info().rss / 2**20, 1)
                try:
                    probe = R.speed_probe(srv)
                    peak = gpu_snapshot()["gpu_mem_used_mib"]
                finally:
                    srv.stop()
                recheck[m][tag] = {"load_seconds": li.load_seconds, "layers_offloaded": li.layers_offloaded,
                                   "gpu_weight_fraction": li.gpu_weight_fraction, "gpu_model_mib": li.gpu_model_mib,
                                   "cpu_model_mib": li.cpu_model_mib, "kv_mib": li.kv_mib,
                                   "gpu_mem_baseline_mib": base, "gpu_mem_after_probe_mib": peak,
                                   "gpu_mem_model_mib": round(peak - base, 1), "sys_ram_baseline_mib": round(ram0, 1),
                                   "sys_ram_delta_after_load_mib": ram_delta, "proc_working_set_mib": proc_ws, **probe}
                say(f"recheck {m} {tag} n_ctx={n}: tg256={probe['tg256_tok_s_median']} pp512={probe['pp512_tok_s_median']} "
                    f"offload={li.layers_offloaded} frac={li.gpu_weight_fraction}")
            except Exception as e:
                recheck[m][tag] = {"error": repr(e)}
                say(f"recheck {m} {tag} FAILED {e!r}")
            time.sleep(3)

    # 4) Stage 1 projection adjusted to the Stage 1 context
    tot_core = tot_full = 0.0
    for m in report["models"]:
        pm = report["per_model"][m]["projection"]
        rc = recheck[m]
        try:
            ratio = rc["stage1_ctx"]["tg256_tok_s_median"] / rc["calibration_ctx"]["tg256_tok_s_median"]
        except (KeyError, ZeroDivisionError, TypeError):
            ratio = 1.0
        ratio = max(ratio, 1.0)  # never project faster than measured unless the smaller context measurably helps
        adj = {"ctx_speed_ratio": round(ratio, 3)}
        for block in ("core", "reserve"):
            b = pm[block]
            gen_h = b["gen_tokens"] / (pm["decode_tok_s_at_depth"] * ratio) / 3600
            other_h = b["hours"] - b["gen_tokens"] / pm["decode_tok_s_at_depth"] / 3600
            adj[block + "_hours"] = round(gen_h + other_h, 2)
        report["per_model"][m]["projection_stage1_ctx"] = adj
        tot_core += adj["core_hours"] + pm["load_hours"]
        tot_full += adj["core_hours"] + adj["reserve_hours"] + 2 * pm["load_hours"]
    report["speed_recheck"] = recheck
    report["projection_total_hours_stage1_ctx"] = {"core": round(tot_core, 1), "core_plus_reserve": round(tot_full, 1)}
    (run_dir / "calibration_report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    write_markdown(run_dir, report)
    say(f"projection (Stage 1 ctx): core {tot_core:.1f} h, core+reserve {tot_full:.1f} h")
    say("POST-CALIBRATION DONE (Stage 1 NOT started; requires local/STAGE1_APPROVED.json from the user)")


def write_markdown(run_dir: Path, rep: dict) -> None:
    scored = {}
    sp = run_dir / "scored.jsonl"
    if sp.exists():
        for line in sp.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            scored.setdefault(r["model"], []).append(r)
    L = [f"# Calibration report ({rep['run']})", "",
         f"Generated {datetime.now().isoformat(timespec='seconds')}. Models calibrated: {len(rep['models'])}/7. "
         "**Stage 1 has NOT been started.**", "",
         f"## C1 candidate: {rep['C1']} tokens", "",
         "Rule: smallest ladder value with <=1 natural completion above it per model and <=2 in total "
         "(loop-terminated / C_dev-truncated attempts censored).", "",
         "| L | per-model natural completions above L | total | passes | would truncate incl. censored (descriptive) | share |",
         "|---|---|---|---|---|---|"]
    for L_, t in rep["c1_table"].items():
        L.append(f"| {L_} | {t['per_model']} | {t['total']} | {t['passes']} | {t.get('would_truncate_incl_censored')} | "
                 f"{t.get('would_truncate_share')} |")
    L += ["", "The pre-registered rule ignores attempts censored at C_dev (24,576) or loop-terminated. The last two columns are "
          "descriptive only: they show how many development attempts would not finish naturally at each L."]
    L += ["", "## Per model", "",
          "| Model | Integration | Decode tok/s at depth (cal.) | tg256 cal ctx / Stage 1 ctx (quiet) | GPU weights (layers) cal ctx | "
          "GPU weights Stage 1 ctx | Model VRAM MiB (S1 ctx) | Peak device VRAM MiB (cal.) | RAM added by load MiB (S1 ctx) | "
          "Peak sys RAM MiB (cal.) | Load s | Max GPU temp | Throttle flags |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in rep["models"]:
        p = rep["per_model"][m]
        rc = rep.get("speed_recheck", {}).get(m, {})
        tg_c = rc.get("calibration_ctx", {}).get("tg256_tok_s_median")
        tg_s = rc.get("stage1_ctx", {}).get("tg256_tok_s_median")
        t = p["telemetry"]
        s1 = rc.get("stage1_ctx", {})
        L.append(f"| {m} | {p['integration_passed']} ({p['template_fidelity']}) | {p['projection']['decode_tok_s_at_depth']} | "
                 f"{tg_c} / {tg_s} | {p['gpu_weight_fraction']} ({p['layers_offloaded']}) | "
                 f"{s1.get('gpu_weight_fraction')} ({s1.get('layers_offloaded')}) | {s1.get('gpu_mem_model_mib')} | "
                 f"{t['peaks']['gpu_mem_used_mib']} | {s1.get('sys_ram_delta_after_load_mib')} | {t['peaks']['sys_used_mib']} | "
                 f"{p['load_seconds']} | {t['peaks']['gpu_temp_c']} | {t['throttle_reasons_seen'] or 'none'} |")
    L += ["", "## Development attempts", "", "| Model | Item | Finish | Abort | Tokens | Status |", "|---|---|---|---|---|---|"]
    for m in rep["models"]:
        st = {r["item_id"]: r["status"] for r in scored.get(m, [])}
        for a in rep["per_model"][m]["attempts"]:
            L.append(f"| {m} | {a['item']} | {a['finish']} | {a['abort']} | {a['tokens']} | {st.get(a['item'], '?')} |")
    L += ["", "## Stage 1 projection", "", "| Model | core h | reserve h |", "|---|---|---|"]
    for m in rep["models"]:
        adj = rep["per_model"][m].get("projection_stage1_ctx", {})
        L.append(f"| {m} | {adj.get('core_hours')} | {adj.get('reserve_hours')} |")
    L += ["", f"Totals (incl. loads): {rep.get('projection_total_hours_stage1_ctx')}",
          "", "Accuracy on development items is shown for pipeline verification only; it cannot influence C1 or any setting."]
    (run_dir / "CALIBRATION_REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))

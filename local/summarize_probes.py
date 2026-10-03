"""Summarise probe results into local/runs/<probe id>/PROBE_REPORT.md (measurement tables only; no inference)."""
from __future__ import annotations

import json
import os
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE / "runs" / os.environ.get("MORGAN_PROBE_ID", "probe-20261003")
CFG = json.loads((HERE / "config_local.json").read_text(encoding="utf-8"))
ORDER = ["r1-0528-qwen3-8b", "gpt-oss-20b", "glm-4.7-flash", "ministral-3-14b-reasoning",
         "muse-glimmer-30b", "qwen3.8-27b", "gemma-4-31b"]
F, N = "math500/test/geometry/880.json", "ifeval/1012"


def main() -> None:
    rows, comp, forced, dep = [], [], [], []
    for m in ORDER:
        p = RUN / f"probe_{m}.json"
        if not p.exists():
            rows.append(f"| {m} | not probed | | | | | | | | |")
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        L = d.get("loads", [{}])
        l3 = L[-1] if L else {}
        sf, sd = d.get("speed_fresh", {}), d.get("speed_deep", {})
        pl = d.get("placement", {})
        place = pl.get("rule", "")
        if "k_ffn_cpu" in pl:
            place += f" (FFN of {pl['k_ffn_cpu']}/{pl.get('n_layers')} layers on CPU" + (f", ngl {pl['ngl']}" if "ngl" in pl else "") + ")"
        t = d.get("telemetry", {})
        rows.append(f"| {m} | {sf.get('tg_fresh_tok_s')} | {sd.get('tg_tok_s_at_depth')} | {sf.get('pp512_tok_s')} | "
                    f"{l3.get('gpu_weight_fraction')} | {l3.get('vram_added_mib')} | {l3.get('sys_ram_added_mib')} | "
                    f"{[x.get('load_seconds') for x in L]} | {t.get('peaks', {}).get('gpu_temp_c')} | {t.get('throttle_reasons_seen')} |")
        b = d.get("baseline_fit", {})
        if b and "tg_fresh_tok_s" in b:
            dep.append(f"| {m} | {b.get('layers_offloaded')} ({b.get('gpu_weight_fraction')}) | {b.get('tg_fresh_tok_s')} | "
                       f"{b.get('deep', {}).get('tg_tok_s_at_depth')} | {place} | {sf.get('tg_fresh_tok_s')} | {sd.get('tg_tok_s_at_depth')} |")
        else:
            dep.append(f"| {m} | (MoE: --fit already experts-first) | | | {place} | {sf.get('tg_fresh_tok_s')} | {sd.get('tg_tok_s_at_depth')} |")
        i = d.get("integration", {})
        comp.append(f"| {m} | {i.get('passed')} | {i.get('template_fidelity')} | {i.get('effort_control_changes_prompt')} | "
                    f"{i.get('token_accounting', {}).get('hidden_delimiter_tokens')} | {i.get('truncation_ok')} | {d.get('error') or ''} |")
        mech = CFG["models"][m].get("forcing", "server")
        fc = d.get("forced_conclusion", {})
        ok = d.get("forced_conclusion_ok")
        hf = RUN / f"probe_{m}_forced_harness.json"
        if mech == "harness" and hf.exists():
            h = json.loads(hf.read_text(encoding="utf-8"))
            fc, ok = {F: h.get(F, {}), N: h.get(N, {})}, h.get("forced_conclusion_ok")
        f_, n_ = fc.get(F, {}), fc.get(N, {})
        forced.append(f"| {m} | {mech} | {ok} | {f_.get('reasoning_tokens')} | {f_.get('final_tokens')} | {f_.get('finish_reason')} / "
                      f"{f_.get('abort')} | {n_.get('reasoning_tokens')} + {n_.get('final_tokens')} ({n_.get('finish_reason')}) |")
    proj = RUN / "stage1_projection.json"
    pj = json.loads(proj.read_text(encoding="utf-8")) if proj.exists() else None
    out = ["# Probe report (approved Stage 1 v2 configuration)", "",
           "Context = Stage 1 v2 n_ctx (~10.5K); KV q8_0; 8 threads; llama.cpp b11349. Deep = tg128 after an ~8K-token prompt.", "",
           "## Deployment measurements (approved placement)", "",
           "| Model | tok/s fresh | tok/s at 8K | prompt tok/s | GPU weight share | VRAM added MiB | RAM added MiB | load s (x3) | max GPU C | throttle flags |",
           "|---|---|---|---|---|---|---|---|---|---|", *rows, "",
           "## Placement effect (dense: old whole-layer --fit split vs approved rule)", "",
           "| Model | old split (GPU share) | old fresh | old 8K | approved placement | new fresh | new 8K |",
           "|---|---|---|---|---|---|---|", *dep, "",
           "## Compatibility", "", "| Model | passed | template | effort control changes prompt | hidden delimiter tokens | truncation ok | error |",
           "|---|---|---|---|---|---|---|", *comp, "",
           "## Forced conclusion at 6,144 + 1,536 (geometry/880, development item) and natural item (ifeval/1012)", "",
           "| Model | mechanism | forced OK | reasoning tok | answer tok | finish / abort | natural item reasoning + answer |",
           "|---|---|---|---|---|---|---|", *forced, ""]
    if pj:
        out += ["## Stage 1 v2 projection (measured speeds)", "", "| Model | tokens | hours | token source |", "|---|---|---|---|"]
        for m in ORDER:
            o = pj["per_model"].get(m, {})
            out.append(f"| {m} | {o.get('gen_tokens')} | {o.get('hours')} | {o.get('token_source', o.get('status'))} |")
        out += ["", f"**Total: {pj['total_hours']} h** (22 items x 7 models)"]
    (RUN / "PROBE_REPORT.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()

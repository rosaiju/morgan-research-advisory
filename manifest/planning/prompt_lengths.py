"""Offline: rendered user-prompt character lengths per benchmark (no tokenizer, no inference)."""
import json, statistics as st, sys
from pathlib import Path
M = Path(r"C:\Users\rohan\morgan-research-advisory-2026-09-29\manifest")
sys.path.insert(0, str(M))
import generate_item_manifests as g

def capture(orig_item):
    store = {}
    def item(bench, iid, stratum, content):
        store[iid] = content
        return orig_item(bench, iid, stratum, content)
    return store, item

store, g.item = capture(g.item)
f, d, kf, kd = [], [], {}, {}
g.mmlu_pro(f, d, kf, kd); g.math500(f, d, kf, kd); g.bbeh(f, d, kf, kd)
tpl = {b: len((M / "prompts" / f"{b}_user_template.txt").read_text(encoding="utf-8")) for b in ("mmlu_pro", "math500", "bbeh")}
for name, items in (("final", f), ("dev", d)):
    by = {}
    for it in items:
        c = store[it["item_id"]]
        if it["benchmark"] == "mmlu_pro":
            q, opts = json.loads(c); n = len(q) + sum(len(o) + 4 for o in opts) + tpl["mmlu_pro"]
        elif it["benchmark"] == "math500":
            n = len(c) + tpl["math500"]
        else:
            n = len(c) + tpl["bbeh"]
        by.setdefault(it["benchmark"], []).append(n)
    for b, v in by.items():
        v.sort()
        print(f"{name:5} {b:13} n={len(v):4} mean_chars={st.mean(v):8.0f} median={st.median(v):7.0f} p95={v[int(.95*len(v))-1]:7} max={max(v):7} total={sum(v)}")

"""Planning model v2: expected cost/runtime at several COMMON output ceilings (no API calls, no inference).

Output length per attempt ~ LogNormal(median m*verbosity, sigma) truncated at the ceiling C, plus a
probability p_loop that an attempt degenerates into a loop and runs to C. Expected generated tokens per
attempt = E[min(L, C)] (closed form) * (1 - p_loop) + C * p_loop. All length parameters are PLANNING
ASSUMPTIONS [A] to be replaced by development-calibration measurements; verbosity multipliers are relative
AA Intelligence-Index output-token totals [I]. Prices are first-party list prices read 2026-09-29.

    python manifest/planning/cost_model_v2.py
"""
import json
import math
from pathlib import Path

ITEMS = json.loads((Path(__file__).resolve().parents[1] / "items" / "items_final.json").read_text(encoding="utf-8"))
DEV = json.loads((Path(__file__).resolve().parents[1] / "items" / "items_dev.json").read_text(encoding="utf-8"))
assert len({i["item_id"] for i in ITEMS}) == len(ITEMS) == 1280, "final items must be 1,280 unique ids"
assert len({i["item_id"] for i in DEV}) == len(DEV) == 216
assert not {i["item_id"] for i in ITEMS} & {i["item_id"] for i in DEV}

def counts(items):
    c = {}
    for i in items:
        b = {"bbeh_sampled": "bbeh", "bbeh_mini": "bbeh"}.get(i["benchmark"], i["benchmark"])
        c[b] = c.get(b, 0) + 1
    return c

SETS = {"dev": counts(DEV), "final": counts(ITEMS), "ifeval": {"ifeval": 541}}
# prompt characters re-measured 2026-09-29 with v2 items (official BBEH Mini) and the paper-verbatim BBEH suffix
IN_TOKENS = {"dev": 299414 / 4 + 500 * 216, "final": 2599721 / 4 + 500 * 1280, "ifeval": 541 * 400 / 4 + 500 * 541}

# (median tokens, sigma) per benchmark; loop probability per attempt
SCEN = {
    "low":     ({"mmlu_pro": (1200, .8), "math500": (1600, .8), "bbeh": (4500, .9),  "ifeval": (600, .8)},  0.003),
    "central": ({"mmlu_pro": (2700, .9), "math500": (3300, .9), "bbeh": (10000, 1.0), "ifeval": (1300, .9)}, 0.010),
    "high":    ({"mmlu_pro": (6000, 1.), "math500": (7500, 1.), "bbeh": (24000, 1.1), "ifeval": (3500, 1.)}, 0.030),
}
# name: verbosity, $in/M, $out/M, route tokens/s (AA measured on that route)
MODELS = {
    "MiMo-V2.6-Pro (Xiaomi or DeepInfra list price)": (0.90, 0.435, 0.87, 41),
    "DeepSeek-V4-Pro-0813 (off-peak)":               (1.02, 0.66, 1.98, 81),
    "GLM-5.3":                                        (1.31, 1.40, 4.40, 83),
    "GLM-5.3-Flash":                                  (1.13, 0.15, 0.50, 46),
    "Kimi-K3 (upper list price)":                     (1.01, 3.00, 15.0, 39),
    "Qwen3.8-2.4T-A95B (serverless list price)":      (1.08, 2.00, 6.00, 98),
}
CEILINGS = [8192, 16384, 32768, 65536, 98304, 131072]
PHI = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))

def e_min(median, sigma, c):
    """E[min(L, c)] and P(L > c) for L ~ LogNormal(ln median, sigma)."""
    mu = math.log(median)
    z = (math.log(c) - mu) / sigma
    partial = math.exp(mu + sigma ** 2 / 2) * PHI(z - sigma)
    return partial + c * (1 - PHI(z)), 1 - PHI(z)

def tokens(setname, scen, mult, c):
    params, p_loop = SCEN[scen]
    out = trunc = 0.0
    for b, n in SETS[setname].items():
        m, s = params[b]
        e, p = e_min(m * mult, s, c)
        out += n * ((1 - p_loop) * e + p_loop * c)
        trunc += n * ((1 - p_loop) * p + p_loop)
    return out, trunc / sum(SETS[setname].values())

def table(setname):
    print(f"\n=== {setname}: {sum(SETS[setname].values())} items/model x 6 models = {6*sum(SETS[setname].values())} primary requests ===")
    print("ceiling  " + "  ".join(f"{s:>22}" for s in SCEN) + "   (total $ all six | mean censored share | slowest-model sequential hours)")
    for c in CEILINGS:
        cells = []
        for scen in SCEN:
            cost = hours = cens = 0.0
            for name, (mult, pin, pout, tps) in MODELS.items():
                out, tr = tokens(setname, scen, mult, c)
                cost += out / 1e6 * pout + IN_TOKENS[setname] / 1e6 * pin
                hours = max(hours, out / tps / 3600)
                cens += tr / len(MODELS)
            cells.append(f"${cost:7,.0f} |{100*cens:5.1f}% |{hours:5.0f}h")
        print(f"{c:>7}  " + "  ".join(f"{x:>22}" for x in cells))

def per_model(setname, c=131072):
    print(f"\n--- {setname} per model at C={c} (low / central / high $) ---")
    for name, (mult, pin, pout, tps) in MODELS.items():
        vals = []
        for scen in SCEN:
            out, _ = tokens(setname, scen, mult, c)
            vals.append(out / 1e6 * pout + IN_TOKENS[setname] / 1e6 * pin)
        print(f"{name:48} " + " / ".join(f"${v:6,.0f}" for v in vals))

def dedicated_qwen():
    print("\n--- Qwen dedicated FP8 route (16 x B300, planning [A]) ---")
    for scen in SCEN:
        toks = sum(tokens(s, scen, 1.08, 131072)[0] for s in ("dev", "final"))
        for rate, tput in ((5.0, 4000), (7.0, 2500), (9.0, 1500)):
            hours = 3 + toks / tput / 3600  # 3 h provisioning/weight load/smoke test
            print(f"{scen:8} out={toks/1e6:5.1f}M tokens  ${rate}/GPU-h  {tput} tok/s aggregate -> {hours:5.1f} h  ${hours*16*rate:7,.0f}")

if __name__ == "__main__":
    for s in ("dev", "final", "ifeval"):
        table(s)
    per_model("dev"); per_model("final")
    dedicated_qwen()

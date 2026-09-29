"""Planning cost/runtime model (no API calls). Assumptions documented in 18 §7."""
FINAL = {"mmlu_pro": 420, "math500": 400, "bbeh": 460}
DEV = {"mmlu_pro": 70, "math500": 100, "bbeh": 46}
IFEVAL = {"ifeval": 541}
OUT = {  # output tokens per item (reasoning + final) for a median-verbosity max-effort model: low, central, high
    "mmlu_pro": (1500, 4000, 10000), "math500": (2000, 5000, 12000),
    "bbeh": (6000, 15000, 40000), "ifeval": (800, 2000, 6000)}
IN_CHARS = {"final": 2464920, "dev": 283592, "ifeval": 541 * 400}
OVERHEAD = 500  # native template/effort-prefix tokens per request (assumed)
C = 131072
# name: (verbosity multiplier, input $/M, output $/M, output $/M upper, tokens/s on the documented route)
MODELS = {
    "MiMo-V2.6-Pro":      (0.90, 0.435, 0.87, 0.87, 41),
    "DeepSeek-V4-Pro-0813": (1.02, 0.66, 1.98, 3.96, 81),
    "GLM-5.3":            (1.31, 1.40, 4.40, 4.40, 83),
    "GLM-5.3-Flash":      (1.13, 0.15, 0.50, 0.50, 46),
    "Kimi-K3":            (1.01, 3.00, 15.0, 15.0, 39),
    "Qwen3.8-2.4T-A95B":  (1.08, 2.00, 6.00, 7.50, 39),
}
REF = {"DeepSeek-V4.1-Flash (dropped, for reference)": (1.34, 0.15, 0.60, 1.20, 212)}

def run(label, sets, in_chars, models=MODELS):
    print(f"\n== {label} ==")
    tot = [0.0, 0.0, 0.0]; hours = [0, 0, 0]; worst = 0.0
    n_req = sum(sets.values())
    in_tok = in_chars / 4 + OVERHEAD * n_req
    for m, (mult, pin, pout, pout_hi, tps) in models.items():
        row = []
        for k in range(3):
            out = sum(n * min(C, OUT[b][k] * mult) for b, n in sets.items())
            price = pout_hi if k == 2 else pout
            cost = out / 1e6 * price + in_tok / 1e6 * pin
            row.append((out, cost, out / tps / 3600))
            tot[k] += cost; hours[k] = max(hours[k], out / tps / 3600)
        w = n_req * C / 1e6 * pout_hi + in_tok / 1e6 * pin
        worst += w
        print(f"{m:45} req={n_req:5} in={in_tok/1e6:5.2f}M  out(M) {row[0][0]/1e6:5.1f}/{row[1][0]/1e6:5.1f}/{row[2][0]/1e6:5.1f}"
              f"  $ {row[0][1]:7.0f}/{row[1][1]:7.0f}/{row[2][1]:7.0f}  seq-h {row[0][2]:5.0f}/{row[1][2]:5.0f}/{row[2][2]:5.0f}  worst-case ${w:,.0f}")
    print(f"TOTAL $ low/central/high = {tot[0]:,.0f} / {tot[1]:,.0f} / {tot[2]:,.0f};  every-item-hits-C bound ${worst:,.0f}")
    print(f"slowest model sequential hours low/central/high = {hours[0]:.0f}/{hours[1]:.0f}/{hours[2]:.0f}")

run("development calibration (216)", DEV, IN_CHARS["dev"])
run("final evaluation (1,280)", FINAL, IN_CHARS["final"])
run("IFEval diagnostic (541)", IFEVAL, IN_CHARS["ifeval"])
run("final (1,280) - dropped model reference", FINAL, IN_CHARS["final"], REF)

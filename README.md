# Morgan open-weight model research package

Updated September 29, 2026. Proposed research documents and offline preparation only. **No inference, benchmark, model loading or weight download has been performed.** No results exist.

## What this repository deliberately does not contain

These are excluded by `.gitignore`:
- API keys and `.env` files (only the variable names are in `runner/.env.example`);
- stage authorisation files and run outputs (`runs/`);
- **benchmark answer keys** (`answer_key_*.json`);
- benchmark datasets and third-party sources (`manifest/evaluation-sources/`);
- the scoring virtualenv and vendored third-party scorer code.

Every file is stored byte-for-byte (`.gitattributes`), so the SHA-256 locks verify on any checkout.

**To rebuild the excluded material on a fresh clone** (no model or API needed):
```
python manifest/fetch_evaluation_sources.py        # re-download pinned data; checked against evaluation-files-lock.json
python manifest/generate_item_manifests.py         # regenerates items + answer keys; must match items/item_manifest_lock.json
python -m venv .venv-scoring                       # then install per scoring/requirements-lock.txt;
                                                   # Math-Verify from the pinned commit archive (see 21 §1)
python scoring/setup_vendor.py                     # vendored IFEval + BBEH scorer, checked against vendor-lock.json
python verify_all.py                               # all local checks
```

## Stage 1 complete (2026-09-29): read 20 and 21

- **[20: stage-1 provider questions](20-stage1-provider-questions.md):** draft questions (not sent), the Qwen deviation ladder and disclosure text, and the user's API-access steps.
- **[21: local validation report](21-local-validation-report.md):**
  - Math-Verify is installed and tested.
  - The scorers are implemented, with 45/45 fixtures passing.
  - The BBEH suffix is corrected to the paper's text, and BBEH now uses the official Mini.
  - IFEval is seeded.
- **Checking the package:** `python verify_all.py` re-runs every local check (14/14 pass).
- **Nothing paid, sent or run.**

## Current state (v2, 2026-09-29): start with 19

**The user tentatively accepted the v2 set on 2026-09-29.** The set: **P35 MiMo-V2.6-Pro-RL**, P25 DeepSeek-V4-Pro-0813, P28 GLM-5.3, P27 GLM-5.3-Flash, P29 Kimi-K3, P34 Qwen3.8-2.4T-A95B. DeepSeek-V4.1-Flash (P24) is superseded and kept in `models.json` → `superseded_models`.

**Read [19: readiness, execution routes and calibration plan](19-readiness-and-calibration-plan.md) first.** It covers:
- MiMo checkpoint identity;
- the Qwen route recommendation;
- output limits;
- the calibration rule;
- cost scenarios;
- exact request counts;
- the first paid integration test.

Also current:
- [15](15-six-model-configuration-manifest.md), [16](16-frozen-evaluation-protocol.md) and [17](17-fairness-reproducibility-audit.md) are updated to v2;
- `runner/` holds the offline-tested adapter layer, which is network-gated.

The v1 versions of all changed files are in `manifest/history/2026-09-29_v1_pre-MiMo/`. [18](18-final-candidate-and-execution-audit.md) holds the candidate audit that led to v2.

**Nothing has been executed:** no paid request, account, inference or model loading.

## Current documents (in precedence order). v1 text below; 19 → 17 → 16 → 15 → 14 in v2

1. [14: capability-first shortlist](14-capability-first-shortlist.md): the six proposed models, selected without hardware considerations. This takes precedence on selection.
2. [15: six-model configuration manifest](15-six-model-configuration-manifest.md) + [manifest/models.json](manifest/models.json): exact revisions, native interfaces, explicit effort and sampling, stop/parse rules, precision identities and integration gates. Each field is labelled verified, proposed or pending.
3. [16: evaluation protocol](16-frozen-evaluation-protocol.md) + [manifest/evaluation.json](manifest/evaluation.json): tasks, exact samples (1,280 final and 216 development items), prompts, scoring, status precedence, budget policy, seeds, retries and the statistical plan.
   - **Frozen:** the procedure.
   - **Pending:** the output-ceiling value (`calibrated=false`).
4. [17: fairness and reproducibility audit](17-fairness-reproducibility-audit.md): what was actually executed versus only documented, 15 issues resolved in the manifests, open blockers, and disclosed fairness limits.

Supporting: [12](12-candidate-pool-revalidated.md) (the 34-model discovery registry) and [13](13-protocol-after-audit.md) (scorer and template corrections, retained; its hardware gates and 355-item bridge screen are superseded). Files 00-11 are proposal history; do not execute their older shortlists, screens or hardware gates.

## Manifest folder

| Path | Contents |
|---|---|
| `source-lock.json` + `<publisher>--<model>/` | 32 pinned model documentation/config/template files (hash-verified 2026-09-29) |
| `evaluation-source-lock.json` | dataset and evaluator revision pins |
| `evaluation-files-lock.json` + `evaluation-sources/` | 46 fetched pinned source and data files with SHA-256 (no weights, no vocabularies) |
| `prompts/` + `prompts-lock.json` | fixed prompt templates (MMLU-Pro and MATH byte-identical to the pinned sources; BBEH suffix study-authored and disclosed) |
| `items/` | generated development/final item manifests, isolated answer keys, and `item_manifest_lock.json` |
| `models.json`, `evaluation.json`, `dev-calibration-spec.json` | machine-readable configuration and protocol |
| `fetch_evaluation_sources.py`, `generate_item_manifests.py` | reproducible preparation scripts (the older `.ps1` fetcher is superseded) |

## What remains before any experiment (each needs separate authorization)

- **Tokenizer files:** needed to compute the common output ceiling and to name GLM's stop tokens.
- **Scorer installation and tests:** install Math-Verify and pass the scorer fixture suites; choose and test a Kimi output parser.
- **Integration checks:** the serving backend's fidelity to each native template/encoder, sampling setting and precision.
- **Development calibration:** run on the 216 development items, then set `calibrated=true`.

Morgan GPU details are not needed for any of this preparation. They belong to the later execution and deployment phases.

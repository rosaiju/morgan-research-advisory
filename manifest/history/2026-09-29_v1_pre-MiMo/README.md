# Morgan open-weight model research package

Updated September 29, 2026. Proposed research documents and offline preparation only. **No inference, benchmark, model loading or weight download has been performed.** No results exist.

## Pending decision: read 18 first

[18: final candidate and execution audit](18-final-candidate-and-execution-audit.md) (2026-09-29) proposes three things:
- **A model swap:** replace DeepSeek-V4.1-Flash (P24) with **MiMo-V2.6-Pro-RL** (P35).
- **Hosted execution:** a per-model API route for each of the six.
- **A pre-outcome amendment:** set the common output ceiling to 131,072 tokens, the hosted routes' output limit.

It also gives cost and runtime estimates and the gated execution plan. Until you accept 18, documents 14–17 and the manifests below still describe the *previous* six. 18 §9 lists every file that would change. Nothing has been executed.

## Current documents (in precedence order)

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

# Claude Code handoff: finish the six-model methodology manifest

> **Fourth update, 2026-09-29 (stage 1 done).** The user approved stage 1 only.
>
> **Done:**
> - Math-Verify installed from the pinned commit archive (`.venv-scoring`) and validated.
> - `scoring/` scorers built; 45/45 fixtures pass.
> - BBEH suffix corrected to the paper's verbatim text.
> - BBEH final = the official Mini.
> - IFEval `langdetect` seeded.
> - Qwen practical route = DeepInfra FP4 (D2, disclosed).
> - Provider questions drafted in 20; they are NOT sent.
> - `verify_all.py` passes 14/14.
>
> **Next:** only with the user's explicit authorisation, run the 34-request integration test (`runner/integration_plan.json`, $15 cap). The user must first create accounts and keys (20 §8).
>
> **Third update, 2026-09-29 (v2 applied).** The user tentatively accepted the v2 set. Changes made:
> - **Manifests updated:** `models.json` v2, `evaluation.json` v2, `dev-calibration-spec.json` v2, and 15/16/17 v2. v1 is archived in `manifest/history/`.
> - **New files:** `19-readiness-and-calibration-plan.md` and `runner/` (14 offline tests pass; network gated).
>
> **Key open items:**
> - Z.ai `max_tokens` may exclude reasoning (integration test T2);
> - DeepInfra must confirm MiMo's revision and precision; otherwise use H-MiMo-Xiaomi, labelled;
> - the dedicated Qwen FP8 GPU authorisation, or the FP4 fallback;
> - Math-Verify fixtures;
> - calibration, then freezing C_final.
>
> Still no paid request, account, inference or loading. The next step needs the user's authorisation (see 19 §8–§9).
>
> **Second update, 2026-09-29.** `18-final-candidate-and-execution-audit.md` proposes the following, and is **awaiting the user's decision**:
> - replace P24 DeepSeek-V4.1-Flash with MiMo-V2.6-Pro-RL @ `73875d00`;
> - hosted API routes for all six models;
> - a hosted output ceiling of 131,072 tokens;
> - an estimated cost of about $382 central for the complete run (range $157–$1,082);
> - stage-gated execution.
>
> Do not edit 15/16/17 or the JSON manifests for MiMo until the user accepts 18. Its §9 lists the exact edits. No inference, accounts or spending have been authorised.
>
> **Status update, 2026-09-29 (Claude Code).** The deliverables in §7 now exist: 15, 16, 17, `manifest/models.json`, `manifest/evaluation.json`, `manifest/dev-calibration-spec.json`, the item manifests (`manifest/items/`), prompt templates and locks. The 32 archived source hashes were re-verified.
>
> Pinned evaluation sources and data were fetched: 46 files, including the Kimi encoder, now audited. BBEH has 23 tasks (4,520 items).
>
> Still pending, and each needs separate authorization: tokenizer files (the output-ceiling value and GLM stop-token names), Math-Verify installation and fixture tests, a Kimi output parser, backend integration checks, and development calibration (`calibrated=false`).
>
> Still true: no inference, benchmark, model loading or weight download has occurred. The sections below are the original handoff and are kept for history. Where they say a deliverable "has not been written", that is superseded by this note; see README.md for current precedence.

Prepared September 29, 2026. Read this first. The user requested handoff before Codex completed the preparation stage.

## 1. Current task and strict boundaries

Finish the configuration and evaluation manifest for these six models, then audit it for fairness/reproducibility and report unresolved issues:

- DeepSeek-V4.1-Flash
- DeepSeek-V4-Pro-0813
- GLM-5.3
- GLM-5.3-Flash
- Kimi-K3
- Qwen3.8-2.4T-A95B

The user authorized research, preparation and documentation ONLY. DO NOT run model inference, any benchmark, development inference, model loading, or model-weight downloads. Do not generate experimental results. No paid endpoints, deployments, emails or irreversible actions. Downloading small public metadata/configuration/source files has been used for research; it is not permission to download weights. Keep tokens/API secrets out of outputs.

Do NOT require Morgan hardware information to select models. The professor explicitly said not to worry about GPU/VRAM now. Capability selection is independent of availability, deployment feasibility, VRAM, cost or existing laptop downloads. Hardware belongs to later execution planning and deployment evaluation. Do not silently substitute smaller models later if the execution route is difficult.

The user wants the methodology specified BEFORE seeing results. Because empirical development calibration is prohibited now, freeze the calibration PROCEDURE and leave its resulting token ceiling explicitly pending. Do not pretend the entire executable experiment is frozen when that empirical dependency remains.

## 2. Workspace and what actually exists

Windows PowerShell workspace: `C:\Users\rohan`.
Research package: `C:\Users\rohan\morgan-research-advisory-2026-09-29`.
The user's application/benchmark repository has NOT been located, inspected or modified by this preparation work. Work inside the advisory package unless the user later changes scope. No new inference/benchmark run was started, and no existing user run was managed.

Read in this order:

1. `14-capability-first-shortlist.md`: current six-model decision; all 34 candidate dispositions.
2. `13-protocol-after-audit.md`: useful benchmark/scoring corrections, but its hardware-first and previous screening provisions are superseded.
3. `12-candidate-pool-revalidated.md`: source-linked 34-model discovery registry; hardware gating is superseded.
4. `manifest/source-lock.json`: pinned model repositories and hashes of 32 fetched documentation/config/template files.
5. `manifest/evaluation-source-lock.json`: pinned dataset and evaluator revisions.

`README.md` currently points to file 14. Files 00-11 preserve proposal history and published evidence. Do not execute older proposals. In particular: earlier three-model choice, nine-model compulsory screen, 5-point bootstrap elimination, 30-question math screen and hardware dependency are not current.

No final configuration-manifest JSON/YAML, complete protocol, development item set, final item manifest, parser fixture suite, or final audit report has yet been written. Do not describe them as completed.

## 3. Project rationale and previous mistakes

Undergraduate Morgan State research: select strong open-weight reasoning/general-capability models, then separately investigate university GPU serving and university tools/RAG.

Separate A = capability, B = deployment/system behavior, C = university application. Do not combine into one intelligence score. IFEval instruction following is a separate diagnostic from reasoning accuracy.

Original 20-question custom v2 had temperature 0, 4096 output tokens, 8192 context and 1200-second timeout. Earlier reasoning models repeatedly truncated or looped; CPU speed and answer-format requirements distorted interpretation. These user-reported pilot findings are supporting history, not the new selection criterion. Raw pilot data has not been audited here.

Current proposal: evaluate ALL SIX together, avoiding an unnecessary six-to-four elimination screen. If the user later insists on four, document a separate disjoint screening stage for all six, without automatic family slots. No claim that these are statistically the world's best six or that excluded models are defeated. The shortlist is a purposive evidence-supported research sample.

## 4. Exact model revisions VERIFIED and archived

These were fetched from Hugging Face publisher API metadata and used in immutable `/resolve/<sha>/...` URLs. Full source paths/hashes are in `manifest/source-lock.json`.

| Repository | Revision |
|---|---|
| `deepseek-ai/DeepSeek-V4.1-Flash` | `dba1be0a40aa45a94ad051997016db3960a90277` |
| `deepseek-ai/DeepSeek-V4-Pro-0813` | `72e1d3230f6c080a530b0a1d46f8eb4602340597` |
| `zai-org/GLM-5.3` | `aca966e4e02791568aa6a4ced368624b3d897f42` |
| `zai-org/GLM-5.3-Flash` | `eb9eb208eb0d988989d07a6a12d0fdeb5f52574a` |
| `moonshotai/Kimi-K3` | `f831ab66814297da540d832a5235f8e904f29d06` |
| `Qwen/Qwen3.8-2.4T-A95B` | `207bd685a7e3696cfaff12ded7c6a7ea0f88c996` |

Each model has a `manifest/<publisher>--<model>/` directory with `metadata.json`, README, config and tokenizer_config; generation_config where present. GLM/Qwen official Jinja templates are archived. DeepSeek official encoding Python, README and test source are archived with `/` flattened to `__`. Weight/tokenizer-vocabulary downloads were NOT performed. Tests were NOT executed.

### Important verified findings: DeepSeek

- Neither DeepSeek release supplies a Jinja chat template. Use its OWN pinned official Python encoder and parser, not a generic R1 or Qwen template.
- V4.1: `encoding/encoding.py`; `thinking_mode="thinking"`, numeric `reasoning_effort` 1-100. String low/high/max map to 50/75/100; default high=75. Explicitly select 100 for proposed high-capability condition rather than relying on default.
- V4.1 encoder documentation demonstrates separate `reasoning_content`, `content`, `tool_calls`. Parser expects well-formed output and does not repair malformed output. Inspect parser around line 935; EOS handling matters if serving strips stop tokens.
- V4.1 pinned README recommends temperature 1.0, top_p .95 or 1.0, max_tokens >=256K. Its instruct-evaluation text uses top_p .95. Config context limit = 1,048,576, nested under text_config; native mixed FP8/FP4 details in config.
- Pro: `encoding/encoding_dsv4.py`; thinking mode plus low/high/max effort. Pinned README says local temperature 1.0, top_p .95 for agents and 1.0 OTHERWISE. This matters for the no-tools panel. Generation config also uses 1.0/1.0.
- **Pro README explicitly recommends maximum output length 384K at high/max effort.** The earlier provisional 32K cap is not justified as adequate.
- Pro context =1,048,576, EOS id1, BOS0, native FP8 config with FP4 experts. Do not label this artifact simply BF16 because torch_dtype says bfloat16.
- Pro and V4.1 tool syntax differs; never reuse encoders interchangeably.

### Important verified findings: GLM pair

- Both have pinned `chat_template.jinja`. Effort choices low/high/max; template defaults any value other than low/high to max. Explicit max and validation of accepted values are necessary.
- Template adds its native system effort prefix; common user prompt need not imply identical raw serialized tokens across families.
- `clear_thinking` defaults false. Card advises true for chat; fresh single-turn context avoids historical ambiguity, but manifest must choose explicitly and justify.
- Generation configs explicitly temperature1.0/top_p.95; do_sample is not explicitly set there. Do not accidentally inherit greedy generation. Explicit sampling must be specified in study config.
- EOS list `[154820,154827,154829]`; distinguish normal turn completion from tool-related stops by inspecting tokenizer/template/backend semantics, not simply treating every EOS as an answered question.
- Both context configs =1,048,576; FP8 quantization. Official templates prefill `<think>`; final channel follows `</think>`.
- Publisher per-task recipes vary widely (.95 or1 top_p, agent tools/judges, 64K/128K/163840 outputs). Those are not one universal no-tools recipe. Do not copy publisher fallback-to-baseline scoring from PostTrainBench into this experiment.

### Important verified findings: Kimi

- Card says thinking always on, returns `reasoning_content`; top-level reasoning_effort low/high/max, default max.
- Card's single-step evaluations use temperature1.0/top_p.95; agent tasks use top_p1.0.
- Full assistant reasoning history must be preserved for multi-turn; experiment should be fresh single-turn.
- No Jinja chat_template in fetched tokenizer_config. Official `encoding_k3.py` exists at pinned repository root, confirmed from file listing but **NOT downloaded/read yet**. Fetch and audit it next.
- Config context =1,048,576. Tokenizer's huge model_max_length sentinel is not the real context limit. Native MXFP4 weights/compressed-tensors config, card mentions MXFP8 activations. Custom code references exist.
- Generation config EOS163586, max_length1048576. Nested text config contains generic generation defaults (do_sample false, max_length20, top_k50); DO NOT mistake those for the card's recommended inference recipe. Explicitly resolve them.

### Important verified findings: Qwen

- Official pinned Jinja template is present. Text-only, mandatory thinking; disabling it raises an error.
- Effort choices xhigh(default), medium, low. Template rejects other values. `preserve_thinking` true by default. Explicit xhigh is proposed; don't pass GLM's max string.
- Recommended temperature1.0, top_p.95, top_k20, min_p0, presence_penalty0, repetition_penalty1.
- Outputs reasoning in `<think>...</think>` followed by final output. Native template prefill includes opening think marker.
- Native context262144; README describes extension to1,010,000. Do not silently enable extension or confuse native and advertised extended contexts.
- generation_config EOS list `[248046,248044]`, whereas config EOS248044; resolve/pin intended generation semantics.
- The prominently displayed publisher score table labels hosted Qwen3.8-Max. Do not use those scores as measured results of this exact released checkpoint.

Use archived pinned documentation when making claims. Web-rendered `main` versions sometimes omitted paragraphs seen in the downloaded pinned README. Cite immutable source URLs from the locks.

## 5. Dataset/evaluator revisions already resolved

These are metadata pins only. Most source files/data have NOT yet been downloaded/read at these revisions.

| Source | Revision |
|---|---|
| HF `TIGER-Lab/MMLU-Pro` | `b189ec765aa7ed75c8acfea42df31fdae71f97be` |
| HF `HuggingFaceH4/MATH-500` | `6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be` |
| GitHub `google-deepmind/bbeh` | `80d12ca916b7158f22293fcf3144f4d3d854d4be` |
| GitHub `google-research/google-research` | `d36068b845da4c2b24927fee2cea1e6ef98dadda` |
| GitHub `UKGovernmentBEIS/inspect_evals` | `b49df6bc9e30b2d24571084bc710b9439b9ffa77` |
| GitHub `UKGovernmentBEIS/inspect_ai` | `18acb828a23e581c4a9e8b5a78bf2d556c29e32b` |
| GitHub `huggingface/Math-Verify` | `ba3d3aaff23b3f4cac7a14672b4f6e293d97c98b` |

MMLU-Pro files: data/test-00000-of-00001.parquet and data/validation-00000-of-00001.parquet. MATH-500 file: test.jsonl. Use these exact sources; small dataset/source retrieval is preparation, not benchmark execution.

`manifest/fetch_evaluation_sources.ps1` was WRITTEN BUT NOT RUN. It fetches small pinned READMEs, MATH-500 JSONL, official IFEval inputs/source, BBEH evaluator/README, Inspect task source, Math-Verify source, Kimi encoder. Inspect syntax and requests before using. It does not fetch MMLU parquet or all BBEH task JSONs yet; extend only with explicit small dataset/source paths, never weight wildcards. Earlier inline version failed PowerShell parsing before executing; current file version has not been validated. No `evaluation-sources/` directory or `evaluation-files-lock.json` existed at handoff.

Math-Verify is a scorer CANDIDATE, not an approved installed/tested dependency. Merely pinning its repository does not complete scoring design.

## 6. Audit findings to preserve

- Inspect is a possible runner, not a certified turnkey method. Pin implementation/dependencies and explicit task args.
- Earlier inspected original MMLU-Pro local script had short generation defaults and random guessing on extraction failure. NO random replacement. Inspect MMLU-Pro defaults to zero-shot; publisher results may be five-shot. Name our chosen protocol honestly.
- Generic Inspect MATH loads another dataset, includes temperature override and model-based equivalence grading. Do not call it MATH-500. Use exact H4 data and an audited deterministic scorer.
- Earlier math utilities used SIGALRM; execution-platform dependency needs handling. No hidden judge API calls.
- BBEH full and mini implementations can use different aggregation; a sampled task-balanced panel must be labeled sampled, not full official benchmark. Verify task count (previous proposal assumed23) before deriving sample counts.
- IFEval original prompts must remain unchanged: no FINAL wrapper, no generic reasoning instruction appended. Score final response channel, not internal reasoning. Strict prompt and instruction-level scores separately. Preserve required whitespace/content; no arbitrary cleaning.
- Reasoning text is not a correctness rubric. Don't extract a correct-looking answer from thought when no answer was submitted.
- Same user task/scorer is required; native templates/effort/decoding may differ. Equal token caps are neither equal compute nor automatically fair.
- Separate actual wrong answers from extraction failures, missing finals, budget truncations, malformed native outputs, and infrastructure failures. Track overlapping flags and an explicit primary status precedence.
- Public benchmarks may have training contamination. Disjoint project dev/test splits do not eliminate it.
- Repeated generations are clustered by question; do not pretend they increase independent sample count. No pass@k/best-of cherry-picking for a single-attempt metric.
- Keep native quantization identities; no assumption that inference dtype equals weight-storage precision.

## 7. What Claude must still produce

Recommended file names (not created yet):

1. `15-six-model-configuration-manifest.md` plus `manifest/models.json` or YAML: exact hashes, native interfaces, source citations, decoding including unsupported/unspecified parameters, effort, EOS/stop handling, precision, context, parser requirements, backend-neutral semantics and unresolved integration gates.
2. `16-frozen-evaluation-protocol.md` plus machine-readable evaluation manifest: exact tasks, versions, sample sizes/item IDs, fixed prompt text, generations/seeds, scoring, attempt records, retries, budget calibration and statistical plan.
3. `17-fairness-reproducibility-audit.md`: passed checks, unresolved issues, impact and prerequisites; distinguish documented from tested.
4. Development-only calibration manifest with exact prompts or deterministic generator/specification, disjoint from final data. Not executed.
5. Final sample manifest with stable source IDs/content hashes and an isolated answer-key file if small datasets are fetched. No model outputs. Artifact hashes and source ledger.
6. Update README/current precedence and handoff. Retain old proposals as superseded history.

The user's requested specifics all remain deliverables: exact sample sizes; prompt construction; extraction/equivalence policy; reasoning channel handling; output budgets; truncation; retries; infrastructure/malformed/incorrect statuses; generation count; seeds; uncertainty and multiplicity. Do not leave every decision as 'later choose'. Resolve methodological choices now and explicitly mark only genuine empirical/backend dependencies pending.

## 8. Budget calibration: essential unresolved design

Prior 8K/32K/optional64K proposal is not adequate without reconsideration given native recommendations above. Need a defensible maximum-effort capability policy rather than another arbitrary shared cap. Possible approach to evaluate critically: model-native generous reference ceilings with identical development adequacy criteria, plus a separate matched-token sensitivity condition. This is a suggestion, NOT an already adopted design.

Choose a finite predeclared development set, budget ladder/reference, repeats, adequacy criterion (completion/censoring/tail headroom), rules for failure to meet it, and terminal maximum. No answer-accuracy tuning on final questions. Calibration may depend on completion behavior but must not rescue particular favorites. Define what happens if one model still loops at the largest valid budget; absence of completion remains a capability/configuration outcome, not automatic infrastructure error. Do not promise zero truncation from a small development sample.

Native context must accommodate prompt + reasoning + final + protocol overhead. Qwen native262144 makes a universal384K output cap invalid without explicitly justified context extension. Output allowance and reasoning-effort controls are different. Do not use laptop wall-clock speed to score capability. Set finite operational abort handling separately and report missing attempts honestly.

No development tests can be run in the present authorization. Leave `calibrated=false` and actual selected ceiling unset until a later authorized stage; make preflight refuse final evaluation with unresolved mandatory fields.

## 9. Suggested order of remaining work

1. Validate existing locks and small-file hashes; read native sources without dumping huge config files.
2. Fetch/read Kimi encoder and pinned benchmark/scorer sources. Resolve template/parser/EOS gaps and task counts.
3. Choose a bounded final panel and exact sampling procedure; do not use the old355-item SCREEN as the final sample by accident. Prefer enough distinct questions; document precision limits and possible MATH-500 ceiling. GPQA was only an optional prior suggestion, not committed. Explicitly include or exclude it before outcomes.
4. Generate manifests/item IDs offline if source data is obtained. No inference. Audit answer isolation and disjointness.
5. Write full completion/failure and calibration policies, reproducibility/statistical plan.
6. Audit internal consistency and links/hashes. Synthetic parser checks may be proposed as preparation, but do not start any inference or benchmark. Report accurately whether fixtures were only written or actually executed.
7. Deliver documents and short list of unresolved methodological/integration issues. No GPU information is required to finish this preparation.

## 10. Local tooling and operational details

- Python command alias `python` is unusable here, but actual interpreter WORKS: `C:\Users\rohan\AppData\Local\Python\pythoncore-3.14-64\python.exe`.
- Read-only module availability check found pyarrow, pandas, jinja2 installed; datasets not installed. No libraries installed in this turn. Pyarrow can read the pinned MMLU parquet if needed, so no need to fetch mutable dataset-viewer rows or install a dataset framework just for sampling.
- Node exists at `C:\Program Files\nodejs\node.exe`.
- PowerShell JSON files written with UTF8 may have BOM; use Python encoding `utf-8-sig`.
- Network requests from sandbox initially failed; approved escalated public metadata requests succeeded. Follow Claude's own permission system; this handoff is not blanket approval for arbitrary commands.
- One verbose read-only PowerShell command (Codex exec session43518) appeared stalled. A Ctrl-C request did not confirm exit; it was reading configs and searching files, not running models. Do not terminate unrelated user processes. No benchmark process was created by Codex.
- No AGENTS.md was found at the two explicitly checked paths `C:\Users\rohan\AGENTS.md` and advisory-folder `AGENTS.md`; obey any applicable instructions Claude discovers.
- No subagents were used. Do not assume the user requested delegation.

## 11. Completion standard

The deliverable is a complete proposed methodology and verifiable source/configuration manifest, with honest pending development validation and implementation gaps. It is not a completed experiment, validated serving stack, or result-bearing survey. The final empirical report/abstract comes after testing. End with what is pinned, what remains uncertain, and what later authorization would allow; do not start that later work.

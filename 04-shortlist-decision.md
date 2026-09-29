# Provisional three-model decision

> Superseded proposal. Use [07-candidate-decisions.md](07-candidate-decisions.md). No finalists are preselected under the current protocol.

Decision date: September 29, 2026. **This selects research subjects, not Morgan's final deployed model.** No local validation has been performed.

## Recommended trio

| Role | Exact checkpoint | Reason for allocating a slot |
|---|---|---|
| Controlled mode comparison and direct-answer baseline | `ibm-granite/granite-4.2-8b` | Its documented recipe allows the same sampling settings across thinking and non-thinking modes. This reduces one confound in the proposed experiment. |
| Newer capability challenger | `Qwen/Qwen3.5-9B` | Adds a current small-model alternative with published reasoning evidence and a different architecture. |
| Specialist / historical contrast | `microsoft/Phi-4-reasoning` | Connects the investigation to the reported pilot failure while testing a different family with its supported recipe. It is intentionally older, not claimed to be a current frontier model. |

Publisher references: [Granite](https://huggingface.co/ibm-granite/granite-4.2-8b), [Qwen](https://huggingface.co/Qwen/Qwen3.5-9B), [Phi](https://huggingface.co/microsoft/Phi-4-reasoning).

## What this choice buys

The key result can be a within-checkpoint comparison in which weights, tasks, precision, serving backend, and sampling are held fixed while mode and generation allowance vary. The other checkpoints provide context for the usefulness of those operating points. Cross-checkpoint differences remain observational; they do not isolate the effect of architecture, training, or parameter count.

Granite's non-thinking condition supplies the baseline. A fourth legacy instruct checkpoint is not essential to the minimum study. Avoid adding Qwen2.5 merely because a baseline needs a separate model name.

Phi is included because diagnostic continuity has scientific value under the chosen question. This is a purposive sample, and that selection rationale must be disclosed. Its inclusion does not justify tuning on the old failed questions or assuming that sampling caused the previous failures. Inspect the artifact and parser on development items, then evaluate independently held-out tasks.

## The strongest objection

This trio is not optimized solely for finding Morgan's strongest available service. Phi's historical relevance consumes a slot that could instead evaluate a newer model. The design also includes one main mode experiment, so it cannot show a universal effect of thinking across families.

If the professor prioritizes immediate model selection over explanatory research, change the question and shortlist before final testing. A plausible deployment-oriented trio would be Qwen3.5-9B, Gemma-4-12B-it, and Qwen3.6-27B, conditional on allocated memory and serving support. That is an alternative scope, not an additional required experiment. [Gemma](https://huggingface.co/google/gemma-4-12B-it), [larger Qwen](https://huggingface.co/Qwen/Qwen3.6-27B)

## Replacement rules

1. If DeepSeek is explicitly required, replace Phi with `deepseek-ai/DeepSeek-R1-0528-Qwen3-8B`; do not add another full run. The exact checkpoint removes the ambiguity of the local tag. This candidate shares Qwen lineage with the challenger, so do not describe it as independent pretraining-family coverage. [Source](https://huggingface.co/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B)
2. If Granite cannot be served correctly within a fixed, modest setup effort, use Qwen3-8B as the mode-study fallback and disclose the mode-specific sampling difference. Avoid choosing a fallback because the original scores were disappointing. [Source](https://huggingface.co/Qwen/Qwen3-8B)
3. If hardware cannot support the planned precision/context, choose a common feasible precision where appropriate or document artifact-specific quantization. Do not silently change precision midway through the experiment.
4. If a larger allocation is available, first decide whether a larger candidate answers the chosen question. More hardware does not require more models. If deployment quality is primary, reconsider the larger reserve before freezing the study.
5. Stop adding newly released candidates after the protocol is frozen. Discuss later releases as a limitation or future work.

## Selection gates to finalize later

- Professor agrees on explanatory study versus deployment-first selection.
- Actual allocated GPU and software environment are known.
- Each checkpoint's revision, tokenizer, template, precision, and license are recorded.
- Supported mode controls and final-answer extraction pass development checks.
- A short development pilot shows the proposed held-out experiment fits the agreed compute/time budget.

Do not read held-out results before these gates are resolved. Development checks are not being run as part of this overnight research package.

## Decision log

**Why not simply keep the earlier Qwen/Gemma/Phi suggestion?** A closer review found a useful same-sampling control in the newer Granite release. The proposed study benefits from that feature even though published percentages alone do not identify Granite as the strongest model. This is an evidence-based adjustment to the experimental role, not a new performance claim.

**Why not GPT-OSS or Nemotron?** Both are relevant survey alternatives. They add MoE, artifact-format, or hardware-specific questions to a study already constrained in time. They are not excluded as weak models. A later deployment-focused study may reasonably select them.

**Can step 2 be considered done?** The survey and a justified provisional selection are prepared. Final eligibility is conditional on resource and scope confirmation; no honest review can replace those unknown facts with assumed GPU access.

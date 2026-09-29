# Capability-first experimental shortlist

September 29, 2026. Proposed for review; no inference, benchmarks or weight downloads performed.

## Governing correction

The user's instruction removes Morgan GPU availability, VRAM, hardware feasibility and deployment cost from capability selection. This document supersedes the hardware-first gate and next-action requirements in 12/13 and all earlier documents. Hardware is a later execution/deployment question, not a condition for selecting models. An unavailable execution route must be reported as a missing experiment, not silently replaced by an easier model.

Research question: how do evidence-supported contemporary open-weight contenders compare on English text reasoning and general problem solving under a documented, controlled protocol? This is a purposive comparative study, not proof of the globally best six. Architecture is descriptive; this design cannot isolate architecture effects from training, scale and post-training.

## Decision

Reduce the 34-model pool to SIX proposed experimental models: P24, P25, P27, P28, P29, P34. Prefer one controlled evaluation of all six over screening six merely to discard two. If approximately four is a firm experimental limit, all six require the same disjoint screening panel; no automatic family slots or bye to the final evaluation.

Selection principles: exact released weights; documented reasoning interface; convergent evidence of strong broad capability; relevance to unresolved reasoning comparisons; avoid duplicating variants whose primary additional role is deployment efficiency. These are explicit expert sampling judgments, not retrospective statistical dominance tests. Release recency, parameter count and brand are not sufficient selection evidence. No hardware, price, latency or existing downloads enter the decision.

## Six selections and limitations

| ID | Exact checkpoint | Inclusion evidence and research value | What remains uncertain |
|---|---|---|---|
| P24 | [deepseek-ai/DeepSeek-V4.1-Flash](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash) | Full current DeepSeek; distinct causal encoder-decoder architecture, explicit effort controls, academic and agentic evidence. Test whether broad improvements transfer to our no-tools panel. | Independent index and publisher agent results do not establish superiority to Pro on single-turn reasoning. |
| P25 | [deepseek-ai/DeepSeek-V4-Pro-0813](https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro-0813) | Full Pro reference. Publisher comparisons preserve a plausible reasoning-strength alternative to newer Flash. Both are retained because their capability tradeoff is unresolved, not to reserve two DeepSeek slots. | Some public evidence is scaffold-dependent; no claim of matched statistical superiority. |
| P27 | [zai-org/GLM-5.3-Flash](https://huggingface.co/zai-org/GLM-5.3-Flash) | Strong independent broad-capability signal plus a newly trained hybrid sparse/linear-attention base. Not a quantized or merely smaller copy of GLM-5.3. | Public reporting emphasizes agents; relation to GLM-5.3 on our no-tools tasks is unknown. Inclusion is not based on efficiency. |
| P28 | [zai-org/GLM-5.3](https://huggingface.co/zai-org/GLM-5.3) | Strong independent broad-capability coverage and documented reasoning effort. Provides a serious test of whether agent-heavy progress transfers to academic/deductive reasoning. | Its card's task-specific tools, judges and long budgets preclude direct use as our reasoning score. |
| P29 | [moonshotai/Kimi-K3](https://huggingface.co/moonshotai/Kimi-K3) | Released full model, native reasoning, technical report with knowledge/reasoning results, independent coverage; KDA/attention-residual design adds a distinct configuration. | Vendor high scores do not prove superiority under our common task protocol; multimodal/agent results are out of scope for A. |
| P34 | [Qwen/Qwen3.8-2.4T-A95B](https://huggingface.co/Qwen/Qwen3.8-2.4T-A95B) | Released reasoning checkpoint with independent evaluation under its own name; strong candidate for Qwen's capability ceiling. | The card's prominent benchmark table is labeled Qwen3.8-Max. Do not transfer hosted Max scores/features to the released checkpoint without verified equivalence. |

These are all full released models, not R1 distilled students. Full models may still use distillation during post-training; 'full' does not mean no distillation anywhere in training.

## Evidence audit used for narrowing

[Artificial Analysis's current leaderboard](https://artificialanalysis.ai/leaderboards/models) lists GLM-5.3 max 45, Kimi-K3 max 44, GLM-5.3-Flash 42, released Qwen3.8-2.4T-A95B 40, DeepSeek-V4.1-Flash max 39, and DeepSeek-V4-Pro-0813 max 36. These are prioritization observations, not the study's ranking. Same index is stronger comparative context than unrelated vendor percentages, but endpoints, effort and token use differ, component provenance requires audit, and the index includes agentic/private tasks. No significance or equal-compute inference is made. [Qwen's independent page](https://artificialanalysis.ai/models/qwen3-8-2-4t-a95b) identifies the released checkpoint separately from hosted Max and names index v4.3.2. [GLM Flash independent page](https://artificialanalysis.ai/models/glm-5-3-flash).

The full DeepSeek comparison does not warrant assuming the latest Flash is the universal reasoning successor to Pro. Base-model tables must not be assigned to instruct checkpoints; HLE tool/no-tool and judge changes must remain separate. [Primary comparison and footnotes](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/raw/main/README.md).

GLM-5.3-Flash is explicitly a newly trained hybrid base, while GLM-5.3 describes post-training changes on its prior base. This makes the pair a meaningful unresolved capability comparison, though not a controlled architecture ablation. [Flash card](https://huggingface.co/zai-org/GLM-5.3-Flash/raw/main/README.md), [GLM card](https://huggingface.co/zai-org/GLM-5.3/raw/main/README.md).

## Disposition of every other candidate

Exclusion means not selected for this bounded capability experiment. It does NOT establish inferiority, strict dominance, or absence of university value. Sources and exact checkpoint identifiers for all IDs remain in [12](12-candidate-pool-revalidated.md). Reserves are literature references, not an automatic additional screening queue.

| ID | Candidate | Reason not selected now |
|---|---|---|
| P01 | Qwen3.5-9B | Compact/scaling role adds less to current capability-ceiling question than P34; not excluded for being small or slow. |
| P02 | Qwen3.8-27B | Strong dense reserve and independent coverage; would serve a scale/dense contrast, which is not the present primary question. Not proven dominated by P34. |
| P03 | Qwen3.6-35B-A3B | Sparse efficiency/scaling comparison deferred; no demonstrated unique reasoning advantage warranting another Qwen slot in this bounded study. |
| P04 | Gemma4-12B | Within-family capability evidence favors considering 31B first; extra size comparison not needed now. |
| P05 | Gemma4-26B-A4B | Sparse/dense tradeoff is useful later; no established unique capability advantage for this panel. |
| P06 | Gemma4-31B | Best Gemma reserve in this pool; available broad independent evidence gives less priority than chosen contenders, without proving no-tools inferiority. |
| P07 | GPT-OSS-20B | Larger sibling is the more relevant capability reference; no need for paired size experiment now. |
| P08 | Nemotron3-Nano-30B-A3B | Hybrid/scaling contrast is interesting, but does not establish a frontier capability slot. |
| P09 | Granite4.2-8B | Tool/enterprise integration and mode ablations do not by themselves justify inclusion in a strongest-capability comparison. |
| P10 | Muse-Glimmer-30B | Agent-oriented evidence does not establish competitive no-tools reasoning; no transfer of closed Muse Spark scores. Retain as application/agent reserve. |
| P11 | GLM4.7-Flash | Older smaller family reference; current GLM pair is a more informative unresolved frontier comparison. No inference from age alone. |
| P12 | R1-0528-Qwen3-8B | Distillation/compact-model research role; not a proxy for full DeepSeek. |
| P13 | R1-Distill-Qwen-32B | Older distilled student; would answer a distillation question rather than the selected current full-model question. |
| P14 | Olmo3.1-32B-Think | Strongest transparency research contrast; training openness alone is not capability evidence. Keep in survey, add only if transparency becomes an empirical research question. |
| P15 | EXAONE4.5-33B | Multilingual/document emphasis and limited matched evidence for our English panel; no distinct capability case sufficient to displace a selected contender. License restriction is documented, not used as an intelligence score. |
| P16 | Phi4-reasoning-plus | Useful historical math-specialist baseline; not mandatory for current broad frontier comparison. |
| P17 | GPT-OSS-120B | Strong standardized-reasoning historical reference; useful reproducibility baseline, but no demonstrated unique current frontier role in the accumulated evidence. Exclusion is prioritization, not statistical defeat. |
| P18 | Nemotron3-Super-120B-A12B | Intermediate family/scaling role; Ultra is the more relevant quality reference in the literature. |
| P19 | Ling3.0-flash | Interesting hybrid design; published agent/cache tailoring and incomplete independent evidence give less confidence for this capability study. Missing evidence is not failure. |
| P20 | Mistral-Small4-119B | Another family/scale comparison with no established unique frontier reasoning contribution in reviewed evidence. |
| P21 | Mistral-Medium3.5-128B | Credible generalist reserve, but available evidence is insufficient to claim a stronger or uniquely informative capability case than selected configurations. Not excluded for license/cost/hardware. |
| P22 | Step3.5-Flash | Credible reasoning reserve; older/agent-heavy comparison evidence does not establish a unique advantage warranting expansion. Do not transfer Step 5 hosted scores. |
| P23 | DeepSeek-V4-Flash-0731 | Earlier Flash role represented by P24; Pro retained as the unresolved reasoning alternative. Not a formal dominance claim. |
| P26 | Full DeepSeek-R1-0528 | Historical reasoning and distillation reference; a longitudinal comparison is outside the present current-capability question. |
| P30 | MiniMax-M3 | Credible closest additional-family reserve with reasoning modes and independent coverage; lower prioritization signal and agent-heavy evidence. Cannot claim our six beat it on no-tools reasoning without testing. |
| P31 | Inkling-Small | Limited/partly estimated independent context and no compelling distinct reasoning case; don't retain for its smaller footprint. |
| P32 | Inkling | Distinct family but less compelling reviewed capability evidence; larger size does not automatically improve its priority. |
| P33 | Nemotron3-Ultra-550B-A55B | Serious hybrid-architecture reserve; current broad evidence is less compelling for frontier selection. Its reproducibility/architecture role does not require an extra slot when primary goal is capability. |

The family concentration is a consequence of evidence prioritization, not a nationality/brand requirement. Missing all-family coverage limits external validity. A comparison across all architectures or all publishers would be a different, larger study. The 34-model boundary is retained for this decision; this is not a claim to have excluded every subsequently discovered release worldwide.

## Is screening necessary?

Preferred: NO separate elimination screen. Freeze these six and evaluate all six on the same final panel after integration and development-budget validation. Six configurations is a manageable model count for a bounded comparative study; this statement is not a promise about execution time or available access. This avoids using a small preliminary sample to discard a genuinely strong contender and preserves data for estimation.

If four is mandatory: YES, compare ALL six on a disjoint screening panel. The exact unresolved comparisons are P24 versus P25, P27 versus P28, and the cross-family relation of those four to P29 and P34. There is no defensible guaranteed top four from present evidence. Use the 355-item bridge proposal in 13 (140 MMLU-Pro, 100 MATH-500, 115 BBEH), subject to implementation validation and predeclared budget, with its capability-only frontier/declared tie-break rules. Report selection uncertainty. Do not force one winner per family. A screen does not validate excluding every literature reserve.

## Capability protocol and next step

Retain A/B/C separation and scorer/template corrections from 13. A: no-tools MMLU-Pro, exact MATH-500, BBEH; IFEval is a separate instruction-following diagnostic. Because this shortlist is stronger than the earlier compact pool, MATH-500 may have a ceiling: use it for mathematical reliability, not tiny-gap winner claims. GPQA Diamond can be a prespecified harder science supplement if its access and exact evaluator are confirmed before final generation; do not add it after disappointing separation. No benchmark is general intelligence itself.

Use native documented templates and sampling; explicit reasoning modes; same tasks/scoring and a development-validated output allowance. Equal tokens do not mean equal compute. Include final-answer failures and truncation separately; reasoning text is not a correctness rubric. Pin weights/endpoints, revisions, precision and inference configuration. Model-specific budget escalation after seeing test failures is prohibited. Public contamination remains unresolved.

Next required preparation: build the six-model configuration/benchmark manifest and offline scoring fixtures, then approve the capability protocol. Morgan GPU details are not required to select this set. Later determine execution routes and then conduct B deployment tests and C university-application tests. Hosted evaluation, if later authorized, must identify the exact checkpoint/configuration; product names alone do not establish equivalence. No paid service or execution is authorized by this document.

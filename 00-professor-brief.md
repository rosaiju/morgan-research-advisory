# Proposed undergraduate research direction

> Superseded proposal. Use [06-independent-protocol.md](06-independent-protocol.md). The trio below is historical, not an approved selection.

September 29, 2026. Draft for discussion; not an approved protocol.

**Working title:** Reasoning Accuracy, Completion, and Deployment Tradeoffs in Selected Open-Weight Language Models for a University Service.

The project will survey the original eight candidates and newer alternatives, then experimentally compare three selected checkpoints. The central question is how supported reasoning configurations and generation allowances affect correct answer delivery. A second question is which evaluated configuration can support a useful prototype on Morgan's allocated GPU resources.

The existing custom benchmark will be retained as pilot evidence. It revealed important interactions between decoding, output limits, and completion, but its small question set and shared settings cannot establish broad model superiority.

The proposed experimental sample is Granite 4.2 8B, Qwen3.5 9B, and Phi-4 Reasoning. Granite supplies a controlled thinking/non-thinking comparison; Qwen supplies a newer challenger; Phi supplies a specialist contrast connected to the pilot. These are research roles, not a claim that the trio represents the strongest three available models. The [survey](03-model-survey.md) and [selection rationale](04-shortlist-decision.md) document the evidence and alternatives.

Experiments will use established deduction and mathematics tasks, correct model templates, declared inference settings, repeated attempts, and held-out questions. Accuracy, completion, uncertainty, and resource use will be reported separately. A limited GPU load test and a small university document-use demonstration will connect the research to deployment. Full RAG optimization and production deployment are outside the minimum scope.

**Deliverables:** a sourced model survey, reproducible experimental records, capability and deployment findings, a prototype demonstration if resources permit, and a conditional recommendation.

**Decisions requested:** confirm whether this explanatory study fits the assignment, identify the GPU allocation and access route, and specify the submission date and whether a live server demonstration is required. If immediate deployment selection is the priority, the shortlist and experiment will be revised before testing.

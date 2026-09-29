# GPU resources: requirements and confirmation

Prepared September 29, 2026. **The project's actual allocation is unconfirmed.** No server login, inspection, reservation, or load test was performed.

## What is known

The student reports that the professor says Morgan has GPU resources. A September 10 university announcement describes access through Google Public Sector's GPAR program and mentions Morgan's Obsidian AI platform. It does not specify this student's GPU entitlement, quota, machine type, or access procedure. [Morgan announcement](https://www.morgan.edu/news/google-x-morgan-collaboration)

This makes both on-premises and institution-controlled cloud compute plausible project environments. Do not assume the project should create a separate campus platform before checking how it should relate to existing university work.

## Confirmation sheet

| Required fact | Current status | Why it matters |
|---|---|---|
| Resource owner and project sponsor | Unknown | Establish the correct access route |
| On-premises machine, cluster job, or cloud project | Unknown | Determines scheduling and service deployment |
| Exact GPU model and count allocated together | Unknown | Determines kernel support and model placement |
| VRAM per GPU; MIG partition if any | Unknown | Actual memory available can differ from device capacity |
| Shared or exclusive allocation | Unknown | Shared work can distort timings |
| Driver, OS, container support, permitted software | Unknown | Determines serving compatibility |
| CPU RAM, local storage, and persistent storage | Unknown | Loading, caching, logs, and datasets |
| GPU-hour quota, credits, maximum job time | Unknown | Defines an affordable experiment |
| Access start date and reservation availability | Unknown | Defines the real schedule |
| Model/dataset download access | Unknown | Determines preparation requirements |
| SSH/VPN, scheduler, or managed-notebook access | Unknown | Determines how the experiment is operated |
| Whether persistent HTTP services are permitted | Unknown | Batch compute does not imply hosting permission |
| Intended relation to Obsidian AI or other services | Unknown | Avoids duplicating an existing deployment effort |

No passwords, private keys, tokens, or other credentials belong in this document or in chat.

## Initial planning request

Request access to a supported Linux GPU environment with enough memory for one selected model at a time, a finite reserved pilot allocation, and storage for weights and logs. Sequential model loading is adequate; the study does not require all three models resident simultaneously.

A 48 GB or larger supported GPU would be a useful planning target for the proposed 8-14B dense-model study, but is neither a confirmed requirement nor a fit guarantee. An 80 GB allocation permits more comfortable exploration of larger candidates. With 24 GB, quantization or smaller contexts may be necessary for some configurations. Actual fit depends on architecture, precision, context, concurrency, and runtime overhead.

For dense models, rough BF16 weight storage alone is `2 x parameter_count` bytes:

| Nominal model size | Weight-only decimal GB | Weight-only GiB, approximately |
|---|---:|---:|
| 8B | 16 | 14.9 |
| 9B | 18 | 16.8 |
| 12B | 24 | 22.4 |
| 14B | 28 | 26.1 |
| 27B | 54 | 50.3 |
| 30B | 60 | 55.9 |

These are calculations, not observed VRAM requirements. Add attention/state caches, activations, runtime buffers, and any additional model components. Advertised size labels are rounded. For MoE models, active parameters estimate only part of computation; total resident parameters still matter for storage. Multiple GPU memories do not combine automatically without a supported placement/parallelism scheme.

Start by requesting a small pilot allocation; estimate the full run from measured generation rate and token distributions. The earlier 10-40 GPU-hour figure was a provisional reservation envelope, not a validated runtime estimate. Distinguish elapsed hours from GPU-hours: two allocated GPUs for ten hours consume twenty GPU-hours.

## Draft request for the student to send

Subject: GPU allocation details for open-weight model evaluation project

Professor / computing support team,

I am preparing a small reproducible comparison of open-weight models focused on reasoning accuracy, completion, and deployment performance. Before finalizing the three model configurations, could you confirm which GPU resource the project should use, including the GPU model/count, VRAM available to the project, access procedure, and time or credit limits?

I also need to know whether the allocation is shared, whether containers and model downloads are permitted, and whether it supports only batch experiments or also a temporary web/API demonstration. Should the prototype align with Morgan's existing Obsidian AI work or another university service?

The initial request is for a short compatibility and runtime pilot, followed by a bounded evaluation whose compute request will be based on pilot measurements. Models will be loaded one at a time. Please also confirm whether the expected project deliverable includes a live GPU-hosted demonstration.

Thank you.

**This draft has not been sent.** Actual resource confirmation and professor agreement remain external dependencies. The survey and proposed shortlist can be reviewed before those replies arrive.

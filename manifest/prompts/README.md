# Fixed prompt templates (hashes in ../prompts-lock.json)

| File | Provenance | Status |
|---|---|---|
| `mmlu_pro_user_template.txt` | verbatim `USER_PROMPT_TEMPLATE` from pinned `inspect_evals/mmlu_pro/mmlu_pro.py` (b49df6bc..., L50-56). `{letters}` and `{choices}` are rendered by the pinned inspect_ai `multiple_choice` solver (no shuffling). | verified source text |
| `math500_user_template.txt` | verbatim `USER_PROMPT_TEMPLATE` from pinned `inspect_evals/math/math.py` (L60-66), applied to the exact H4 MATH-500 `problem`. Only the prompt text is borrowed; the generic MATH task, its dataset, temperature override and model judge are NOT used. | verified source text |
| `bbeh_user_template.txt` | **study-authored** suffix. BBEH task inputs do not carry an answer-format instruction, and the pinned google-deepmind/bbeh repository (README, evaluate.py) does not provide a prompt suffix. The suffix asks for the exact prefix recognised first by the official `extract_answer` ("The answer is:"). It is modelled on the BBEH paper's instruction but is NOT verified as the paper's verbatim prompt. | proposed; verification against the paper is an open item |
| IFEval | original `input_data.jsonl` prompts, byte-identical, no template | verified source |

No template adds a system message. Rendering must not add or strip whitespace beyond the template.

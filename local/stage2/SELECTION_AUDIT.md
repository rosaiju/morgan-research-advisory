# Stage 2 panel selection audit

Seed `morgan-local-stage2-2026-10-05`; script `local/stage2/select_stage2.py` (deterministic: rerunning reproduces the same files).

Panel: {'mmlu_pro': 61, 'math500': 58, 'bbeh_mini': 67, 'ifeval': 80, 'student': 18} = 284 items, identical for every finalist.

`stage2_panel.json` SHA-256 `bc35e691b4ec3327890258b4dec18760795e210d821ff694d1a0fd4f03cec5d5`

## Exclusions

62 item ids excluded (every item ever selected or run in this study):

- local/items/stage1_panel.json: 56
- local/items/stage1_panel_v2.json: 22
- local/items/calibration_items.json: 6
- item ids in local/runs/**/attempts_*.jsonl: 28
- Stage 1 probe items: ['math500/test/geometry/880.json', 'ifeval/1012']

Checks: no Stage 2 item is in the exclusion set, the development set, or the probe items; every capability item has a key in the frozen final answer key.

## Composition

**mmlu_pro** (61): biology 5, business 5, chemistry 5, computer science 4, economics 4, engineering 4, health 4, history 4, law 5, math 4, other 5, philosophy 4, physics 4, psychology 4

**math500** (58): Algebra|L1 2, Algebra|L2 3, Algebra|L3 3, Algebra|L4 4, Algebra|L5 4, Counting & Probability|L2 1, Counting & Probability|L4 1, Counting & Probability|L5 1, Geometry|L2 1, Geometry|L3 1, Geometry|L4 1, Geometry|L5 2, Intermediate Algebra|L1 1, Intermediate Algebra|L2 1, Intermediate Algebra|L3 2, Intermediate Algebra|L4 3, Intermediate Algebra|L5 4, Number Theory|L1 1, Number Theory|L2 1, Number Theory|L3 2, Number Theory|L4 2, Number Theory|L5 1, Prealgebra|L1 1, Prealgebra|L2 2, Prealgebra|L3 2, Prealgebra|L4 2, Prealgebra|L5 2, Precalculus|L2 2, Precalculus|L3 2, Precalculus|L4 2, Precalculus|L5 1

**bbeh_mini** (67): bbeh_boardgame_qa 3, bbeh_boolean_expressions 3, bbeh_buggy_tables 3, bbeh_causal_understanding 3, bbeh_disambiguation_qa 3, bbeh_dyck_languages 3, bbeh_geometric_shapes 3, bbeh_hyperbaton 3, bbeh_linguini 3, bbeh_movie_recommendation 2, bbeh_multistep_arithmetic 2, bbeh_nycc 3, bbeh_object_counting 3, bbeh_object_properties 3, bbeh_sarc_triples 3, bbeh_shuffled_objects 3, bbeh_spatial_reasoning 3, bbeh_sportqa 3, bbeh_temporal_sequence 3, bbeh_time_arithmetic 3, bbeh_web_of_lies 3, bbeh_word_sorting 3, bbeh_zebra_puzzles 3

**ifeval** (80): pool after exclusion 528; instruction groups change_case 17, combination 7, detectable_content 9, detectable_format 27, keywords 22, language 4, length_constraints 22, punctuation 11, startend 12

**student** (18): {'programming': 3, 'algorithms': 3, 'debugging': 3, 'conceptual': 3, 'reasoning': 3, 'instruction_following': 3} (all unused suite prompts; the suite has 30, Stage 1 v1 selected 12). Includes 3 programming items graded in the Docker sandbox.

## Development probe items (never Stage 2 items)

- `math500/test/geometry/880.json`: forced conclusion at 16,384 (ran past 24K unforced in calibration)
- `ifeval/1012`: natural-length item

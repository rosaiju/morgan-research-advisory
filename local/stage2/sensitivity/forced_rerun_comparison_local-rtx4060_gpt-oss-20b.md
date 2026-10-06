# Policy B forced-item rerun: gpt-oss-20b on local-rtx4060 (sensitivity only)

The official Stage 2 score is unchanged. Same items, prompts, seeds and settings; only the reasoning budget changed from 16,384 to 24,576 tokens.

Official correct on these 20 items: 6; rerun correct: 8.

| Benchmark | n | stayed correct | stayed incorrect | incorrect→correct | correct→incorrect | extraction/truncation changed | still hit 24,576 |
|---|---|---|---|---|---|---|---|
| bbeh_mini | 14 | 2 | 11 | 1 | 0 | 0 | 12 |
| ifeval | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| math500 | 1 | 0 | 0 | 1 | 0 | 1 | 1 |
| mmlu_pro | 4 | 3 | 1 | 0 | 0 | 0 | 3 |
| **total** | 20 | 6 | 12 | 2 | 0 | 1 | 16 |

| Item | official (16,384) | rerun (24,576) | rerun tokens | hit 24,576 |
|---|---|---|---|---|
| `bbeh/bbeh_buggy_tables/119` | INCORRECT | INCORRECT | 24612 | yes |
| `bbeh/bbeh_buggy_tables/79` | INCORRECT | INCORRECT | 24612 | yes |
| `bbeh/bbeh_dyck_languages/109` | INCORRECT | INCORRECT | 24612 | yes |
| `bbeh/bbeh_geometric_shapes/139` | INCORRECT | INCORRECT | 24346 | no |
| `bbeh/bbeh_geometric_shapes/69` | INCORRECT | INCORRECT | 24613 | yes |
| `bbeh/bbeh_hyperbaton/149` | INCORRECT | INCORRECT | 24613 | yes |
| `bbeh/bbeh_hyperbaton/169` | INCORRECT | INCORRECT | 24611 | yes |
| `bbeh/bbeh_linguini/159` | INCORRECT | INCORRECT | 24706 | yes |
| `bbeh/bbeh_object_counting/79` | CORRECT | CORRECT | 16984 | no |
| `bbeh/bbeh_object_properties/149` | CORRECT | CORRECT | 24612 | yes |
| `bbeh/bbeh_temporal_sequence/119` | INCORRECT | INCORRECT | 24615 | yes |
| `bbeh/bbeh_web_of_lies/129` | INCORRECT | INCORRECT | 24615 | yes |
| `bbeh/bbeh_zebra_puzzles/109` | INCORRECT | INCORRECT | 24612 | yes |
| `bbeh/bbeh_zebra_puzzles/59` | INCORRECT | CORRECT | 24612 | yes |
| `ifeval/2677` | CORRECT | CORRECT | 8352 | no |
| `math500/test/geometry/965.json` | EXTRACTION_FAILURE | CORRECT | 25331 | yes |
| `mmlu_pro/11198` | CORRECT | CORRECT | 4981 | no |
| `mmlu_pro/11760` | CORRECT | CORRECT | 25506 | yes |
| `mmlu_pro/12033` | CORRECT | CORRECT | 24609 | yes |
| `mmlu_pro/1606` | INCORRECT | INCORRECT | 24609 | yes |

"""Scorer fixture suite (no model outputs; synthetic responses and gold round-trips only).

    set NLTK_DATA=scoring/vendor/nltk_data
    .venv-scoring/Scripts/python -m pytest scoring/test_scorers.py -q
"""
import io
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import scorers as S  # noqa: E402

SRC = ROOT / "manifest" / "evaluation-sources"


@pytest.fixture(scope="module")
def mv():
    v = S.MathVerifier(timeout_s=60)
    yield v
    v.close()


# ------------------------------------------------------------------ MMLU-Pro
@pytest.mark.parametrize("text,expected", [
    ("Reasoning...\nANSWER: C", ("CORRECT", "C")),
    ("answer: c", ("CORRECT", "C")),
    ("**ANSWER: C**", ("CORRECT", "C")),
    ("ANSWER: (C)", ("CORRECT", "C")),
    ("ANSWER: C.", ("CORRECT", "C")),
    ("ANSWER: $C$", ("CORRECT", "C")),
    ("ANSWER: A\nwait, reconsider\nANSWER: C", ("CORRECT", "C")),
    ("ANSWER: D", ("INCORRECT", "D")),
    ("ANSWER: K", ("EXTRACTION_FAILURE", None)),      # beyond 10 options
    ("ANSWER: A, B", ("EXTRACTION_FAILURE", None)),   # two letters for a single-answer item
    ("The answer is C", ("EXTRACTION_FAILURE", None)),  # wrong format: no guessing
    ("", ("EXTRACTION_FAILURE", None)),
])
def test_mmlu_fixtures(text, expected):
    status, _, letter = S.score_mmlu_pro(text, 10, "C")
    assert (status, letter) == expected


def test_mmlu_gold_roundtrip_all_items():
    import pyarrow.parquet as pq
    keys = {**json.loads((ROOT / "manifest/items/answer_key_final.json").read_text(encoding="utf-8")),
            **json.loads((ROOT / "manifest/items/answer_key_dev.json").read_text(encoding="utf-8"))}
    n_opts = {}
    for split in ("test", "validation"):
        for r in pq.read_table(io.BytesIO((SRC / f"TIGER-Lab--MMLU-Pro__{split}.parquet").read_bytes())).to_pylist():
            n_opts[f"mmlu_pro/{r['question_id']}"] = len(r["options"])
    ids = [k for k in keys if k.startswith("mmlu_pro/")]
    assert len(ids) == 490
    for iid in ids:
        gold = keys[iid]["answer"]
        assert S.score_mmlu_pro(f"Some reasoning.\nANSWER: {gold}", n_opts[iid], gold)[0] == "CORRECT", iid


# ------------------------------------------------------------------ MATH-500
MATH_CASES = [
    (r"\frac{3}{4}", "ANSWER: 3/4", "CORRECT"),
    (r"\frac{3}{4}", "ANSWER: 0.75", "CORRECT"),
    (r"\frac{1}{2}", r"ANSWER: \dfrac12", "CORRECT"),
    (r"\sqrt{2}", r"ANSWER: \sqrt2", "CORRECT"),
    (r"\frac{\sqrt{3}}{2}", r"ANSWER: \frac{\sqrt3}{2}", "CORRECT"),
    (r"3\sqrt{13}", r"ANSWER: 3 \sqrt{13}", "CORRECT"),
    (r"(-\infty,3]", r"ANSWER: (-\infty, 3]", "CORRECT"),
    (r"(-\infty,3]", r"ANSWER: (-\infty, 3)", "INCORRECT"),
    ("2, 5", "ANSWER: 5, 2", "CORRECT"),
    ("10", r"ANSWER: 10 \text{ cm}", "CORRECT"),
    (r"90^\circ", "ANSWER: 90", "CORRECT"),
    ("4", r"ANSWER: \boxed{4}", "CORRECT"),
    ("x^2+1", "ANSWER: 1+x^2", "CORRECT"),
    (r"\text{(C)}", "ANSWER: C", "CORRECT"),
    ("12", "ANSWER: 13", "INCORRECT"),
    ("12", "The answer is 12", "EXTRACTION_FAILURE"),               # no ANSWER line
    ("12", "ANSWER: 12\nThat is my final answer.", "EXTRACTION_FAILURE"),  # not on last line (Inspect \\Z rule)
    ("12", "ANSWER: ", "EXTRACTION_FAILURE"),
]


@pytest.mark.parametrize("gold,text,expected", MATH_CASES)
def test_math_fixtures(mv, gold, text, expected):
    assert S.score_math500(text, gold, mv, "fixture")[0] == expected


def test_math_malformed_latex_is_not_correct(mv):
    assert S.score_math500(r"ANSWER: \frac{3}{", r"\frac{3}{4}", mv, "m")[0] in ("EXTRACTION_FAILURE", "INCORRECT")


def test_math_gold_roundtrip_all_500(mv):
    rows = [json.loads(l) for l in (SRC / "HuggingFaceH4--MATH-500__test.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    bad = [r["unique_id"] for r in rows if S.score_math500(f"Work.\nANSWER: {r['answer']}", r["answer"], mv, r["unique_id"])[0] != "CORRECT"]
    assert not bad, bad[:10]


def test_math_timeout_then_recovery():
    v = S.MathVerifier(timeout_s=0.001)  # worker start-up alone exceeds this
    status, flags, _ = S.score_math500("ANSWER: 4", "4", v, "t")
    assert (status, flags) == ("EXTRACTION_FAILURE", ["scorer_timeout"])
    v.timeout_s = 60
    assert S.score_math500("ANSWER: 4", "4", v, "t2")[0] == "CORRECT"   # restarted worker
    v.close()


# ------------------------------------------------------------------ BBEH
@pytest.mark.parametrize("text,gold,ok", [  # the eight examples printed by the official evaluate.py
    ("Ok The final answer is: \\boxed{4}.", "4", True),
    ("[Reasoning] The final answer is: \\boxed{4}.", "3", False),
    ("Alright! The final answer is: 2, 3, 4", "2,3,4", True),
    ("blah blah The final answer is: 2, 3, 4", "2,3,5", False),
    ("Ok The answer is: (A)", "a", True),
    ("Ok The answer is: (A)", "b", False),
    ("Ok The answer is: **25**\nHere's why.", "25.0", True),
    ("Ok The answer is: **25**\nHere's why.", "26.0", False),
])
def test_bbeh_official_examples(text, gold, ok):
    assert (S.score_bbeh(text, gold)[0] == "CORRECT") is ok


def test_bbeh_flag_without_prefix():
    status, flags, _ = S.score_bbeh("yes", "yes")
    assert status == "CORRECT" and flags == ["no_answer_prefix"]   # official verdict stands; flagged


def test_bbeh_gold_roundtrip_all_4520():
    """Official-scorer defect (documented in 20/17): targets ending in '.' lose the period on the prediction
    side (twice) but keep it on the reference side, so even a perfect answer scores 0. Exactly 11 of 4,520
    items (all bbeh_linguini) are affected; none is in the official Mini final set (1 is in dev)."""
    bad = []
    for f in sorted(SRC.glob("bbeh__bbeh__benchmark_tasks__*__task.json")):
        for i, ex in enumerate(json.loads(f.read_text(encoding="utf-8"))["examples"]):
            if S.score_bbeh(f"Reasoning.\nThe answer is: {ex['target']}", ex["target"])[0] != "CORRECT":
                bad.append(f"bbeh/{f.name.split('__benchmark_tasks__')[1].split('__task.json')[0]}/{i}")
    assert len(bad) == 11 and all(b.startswith("bbeh/bbeh_linguini/") for b in bad), bad
    final_keys = json.loads((ROOT / "manifest/items/answer_key_final.json").read_text(encoding="utf-8"))
    assert not set(bad) & set(final_keys), "an official-scorer-unreachable item is in the final set"


# ------------------------------------------------------------------ IFEval (separate strand)
def test_ifeval_end_to_end_on_real_prompt():
    recs = [json.loads(l) for l in (SRC / "ifeval__data__input_data.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(recs) == 541
    rec = next(r for r in recs if r["instruction_id_list"] == ["punctuation:no_comma"])
    assert S.ifeval_evaluate(rec, "This response has no commas at all")["strict_prompt"] is True
    assert S.ifeval_evaluate(rec, "This response, however, has one")["strict_prompt"] is False

"""Study scorers (the ONLY component allowed to read manifest/items/answer_key_*.json).

Each scorer receives the FINAL channel only (never reasoning text) of an attempt whose pre-scoring status
(runner/status.py) is SCORABLE, and returns (status, flags, extracted) with status in
{CORRECT, INCORRECT, EXTRACTION_FAILURE}.

  MMLU-Pro  : inspect_ai 0.3.271 multiple_choice.parse_answers (single answer), ported verbatim below;
              no match -> EXTRACTION_FAILURE; no random guessing.
  MATH-500  : last 'ANSWER:' line via inspect_ai ANSWER_PATTERN_LINE (inspect_evals math extract_answer),
              then Math-Verify (pinned ba3d3aaf) gold=\\boxed{answer}, pred=$...$, in a worker process with a
              hard outer timeout. Worker timeout on an item -> EXTRACTION_FAILURE + flag scorer_timeout.
  BBEH      : official evaluate_correctness (vendored, unchanged); flag no_answer_prefix when none of the
              official prefixes occurs (official verdict stands; BBEH never yields EXTRACTION_FAILURE).
  IFEval    : official evaluation_lib strict + loose (separate strand), langdetect seeded (ifeval_seed.py).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "vendor"))

# ---------------------------------------------------------------- MMLU-Pro (inspect_ai 0.3.271, verbatim logic)


def answer_character(index: int) -> str:
    return chr(ord("A") + index) if index < 26 else str(index - 25)


def mmlu_parse_answer(completion: str, n_choices: int) -> str | None:
    """Port of inspect_ai/solver/_multiple_choice.py parse_answers(multiple_correct=False)."""
    completion = re.sub(r"\x24\s*([A-Za-z\d][A-Za-z\d ,]*?)\s*\x24", r"\1", completion)
    completion = re.sub(r"\*\*\s*([A-Za-z\d][A-Za-z\d ,]*?)\s*\*\*", r"\1", completion)
    completion = re.sub(r"(?i)(^|[:,])(\s*)\(([A-Za-z\d])\)(?=\s*(?:,|\.|\n|\Z))", r"\1\2\3", completion)
    matches = re.findall(r"(?i)^ANSWER\s*:\s*([A-Za-z\d ,]+)\s*(?:$|\n|\.)", completion, flags=re.MULTILINE)
    if not matches:
        matches = re.findall(r"(?i)ANSWER\s*:\s*([A-Za-z\d ,]+)(?:[^\w]|\n|$|\.)", completion)
    if not matches:
        return None
    matched = matches[-1].strip().rstrip(".").upper()
    allowed = {answer_character(i) for i in range(n_choices)}
    tokens = [t for t in matched.split(",") if t]
    return tokens[0] if len(tokens) == 1 and tokens[0] in allowed else None


def score_mmlu_pro(final_text: str, n_choices: int, gold_letter: str):
    letter = mmlu_parse_answer(final_text, n_choices)
    if letter is None:
        return "EXTRACTION_FAILURE", [], None
    return ("CORRECT" if letter == gold_letter.upper() else "INCORRECT"), [], letter


# ---------------------------------------------------------------- MATH-500

ANSWER_PATTERN_LINE = r"(?i)ANSWER\s*:\s*([^\n]+)\s*\Z"  # inspect_ai/_util/pattern.py (0.3.271)


def math_extract_answer(completion: str) -> str:
    """inspect_evals math/utils.py extract_answer: last match of AnswerPattern.LINE."""
    matches = list(re.finditer(ANSWER_PATTERN_LINE, completion))
    return matches[-1].group(1) if matches else ""


class MathVerifier:
    """Persistent Math-Verify worker with a hard per-item timeout (kill + restart on timeout)."""

    def __init__(self, timeout_s: float = 30.0, python: str | None = None):
        self.timeout_s, self.python, self.proc = timeout_s, python or sys.executable, None

    def _start(self):
        self.proc = subprocess.Popen([self.python, str(HERE / "math_worker.py")], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True, encoding="utf-8", bufsize=1)

    def check(self, item_id: str, gold: str, pred: str) -> dict:
        if self.proc is None or self.proc.poll() is not None:
            self._start()
        result: dict = {}
        self.proc.stdin.write(json.dumps({"id": item_id, "gold": gold, "pred": pred}) + "\n")
        self.proc.stdin.flush()
        reader = threading.Thread(target=lambda: result.update(json.loads(self.proc.stdout.readline() or "{}")))
        reader.start()
        reader.join(self.timeout_s)
        if reader.is_alive() or not result:
            self.proc.kill()
            self.proc = None
            return {"id": item_id, "status": "TIMEOUT"}
        return result

    def close(self):
        if self.proc and self.proc.poll() is None:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)


def score_math500(final_text: str, gold: str, verifier: MathVerifier, item_id: str = "x"):
    answer = math_extract_answer(final_text)
    if not answer:
        return "EXTRACTION_FAILURE", [], None
    r = verifier.check(item_id, gold, answer)
    if r["status"] == "TIMEOUT":
        return "EXTRACTION_FAILURE", ["scorer_timeout"], answer
    if r["status"] == "GOLD_PARSE_FAILURE":
        raise RuntimeError(f"gold answer failed to parse for {item_id}; scorer fixtures must prevent this")
    return r["status"], [], answer


# ---------------------------------------------------------------- BBEH (official, vendored)

import bbeh_eval  # noqa: E402

BBEH_PREFIXES = ("The answer is:", "The final answer is ", "The final answer is: ", "The answer is ")


def score_bbeh(final_text: str, gold: str):
    flags = [] if any(p in final_text for p in BBEH_PREFIXES) else ["no_answer_prefix"]
    ok = bbeh_eval.evaluate_correctness(final_text, gold)
    return ("CORRECT" if ok else "INCORRECT"), flags, bbeh_eval.preprocess_sample(final_text)


# ---------------------------------------------------------------- IFEval (official; separate strand)


def ifeval_evaluate(prompt_record: dict, response: str) -> dict:
    os.environ.setdefault("NLTK_DATA", str(HERE / "vendor" / "nltk_data"))
    sys.path.insert(0, str(HERE))
    import ifeval_seed  # noqa: F401  (langdetect seed = 0)
    from instruction_following_eval import evaluation_lib as ev

    inp = ev.InputExample(key=prompt_record["key"], instruction_id_list=prompt_record["instruction_id_list"],
                          prompt=prompt_record["prompt"], kwargs=prompt_record["kwargs"])
    strict = ev.test_instruction_following_strict(inp, {inp.prompt: response})
    loose = ev.test_instruction_following_loose(inp, {inp.prompt: response})
    return {"strict_prompt": strict.follow_all_instructions, "strict_instructions": strict.follow_instruction_list,
            "loose_prompt": loose.follow_all_instructions, "loose_instructions": loose.follow_instruction_list}

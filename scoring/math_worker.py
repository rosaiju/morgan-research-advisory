"""Math-Verify worker process: reads JSON lines {"id","gold","pred"} on stdin, writes {"id","status",...}.

Runs Math-Verify with its INNER timeout disabled (Windows-safe); the parent (scorers.MathVerifier)
enforces a hard OUTER timeout per item by killing and restarting this process.
"""
import json
import sys

import math_verify.grader as grader
import math_verify.parser as parser
from math_verify import parse, verify


def _identity_timeout(timeout_seconds=None):
    return lambda func: func


parser.timeout = grader.timeout = _identity_timeout


def wrap_pred(s: str) -> str:
    return s if ("$" in s.replace(r"\$", "") or r"\boxed" in s) else f"${s}$"


def main():
    for line in sys.stdin:
        job = json.loads(line)
        out = {"id": job["id"]}
        try:
            gold = parse("\\boxed{" + job["gold"] + "}", parsing_timeout=None)
            pred = parse(wrap_pred(job["pred"]), parsing_timeout=None)
            if not gold:
                out["status"] = "GOLD_PARSE_FAILURE"
            elif not pred:
                out["status"] = "EXTRACTION_FAILURE"
            else:
                out["status"] = "CORRECT" if verify(gold, pred, timeout_seconds=None) else "INCORRECT"
                out["parsed_pred"] = str(pred[0])[:200]
        except Exception as exc:  # noqa: BLE001
            out["status"] = "EXTRACTION_FAILURE"
            out["error"] = repr(exc)[:200]
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

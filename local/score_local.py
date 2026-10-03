"""Score raw local attempts (the ONLY local component that reads answer keys).

Run with the locked scoring environment:
    .venv-scoring\\Scripts\\python.exe local/score_local.py <run_dir>

Reads <run_dir>/attempts_*.jsonl, writes <run_dir>/scored.jsonl (one line per attempt).
Status precedence follows morgan 16 section 4 via runner/status.classify, with two local additions:
  - abort == loop_terminated            -> BUDGET_TRUNCATED + flag loop_terminated (approved rule)
  - abort in watchdog/transport errors  -> INFRASTRUCTURE_FAILURE
  - unparsed native reasoning delimiters left in the final channel -> MALFORMED_NATIVE_OUTPUT
Only the final channel is scored; reasoning text is never passed to a scorer.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
APP = Path(r"C:\Users\rohan\open-source-ai-model")
sys.path[:0] = [str(ROOT / "runner"), str(ROOT / "scoring"), str(APP)]

import status as morgan_status  # noqa: E402  (runner/status.py)

REASONING_MARKERS = ("<think>", "</think>", "[THINK]", "[/THINK]", "<|channel|>", "<|start|>", "<|message|>",
                     "<|channel>", "<channel|>")


FORCE_MARK = "Time is up. I must stop thinking now"


def pre_status(rec: dict) -> tuple[str, list[str]]:
    abort = rec.get("abort")
    forced = ["forced_conclusion"] if FORCE_MARK in (rec.get("reasoning_text") or "") else []
    if abort == "answer_allowance_exceeded":
        return "BUDGET_TRUNCATED", sorted(set(forced + ["answer_allowance_exceeded"]))
    if forced:
        st, fl = pre_status({**rec, "reasoning_text": (rec.get("reasoning_text") or "").replace(FORCE_MARK, "")})
        return st, sorted(set(fl + forced))
    if abort == "loop_terminated":
        status, flags = morgan_status.classify({**rec, "finish_reason": "length"})
        return "BUDGET_TRUNCATED", sorted(set(flags + ["loop_terminated"]))
    if rec.get("error") or abort in ("first_token_timeout", "stall_timeout", "total_timeout"):
        return "INFRASTRUCTURE_FAILURE", [f"abort:{abort}"] if abort else ["transport_error"]
    status, flags = morgan_status.classify(rec)
    if status == "SCORABLE" and any(m in (rec.get("final_text") or "") for m in REASONING_MARKERS):
        return "MALFORMED_NATIVE_OUTPUT", flags + ["reasoning_markers_in_final"]
    return status, flags


class Scorer:
    def __init__(self):
        import scorers  # noqa: E402  (scoring/scorers.py)
        self.s = scorers
        self.keys = {}
        for n in ("answer_key_final.json", "answer_key_dev.json"):
            self.keys.update(json.loads((ROOT / "manifest/items" / n).read_text(encoding="utf-8")))
        self._mmlu_n = None
        self._ifeval = None
        self.verifier = scorers.MathVerifier(timeout_s=30.0)

    def mmlu_n_choices(self, iid: str) -> int:
        if self._mmlu_n is None:
            import pyarrow.parquet as pq
            src = ROOT / "manifest/evaluation-sources"
            self._mmlu_n = {}
            for split in ("test", "validation"):
                for r in pq.read_table(io.BytesIO((src / f"TIGER-Lab--MMLU-Pro__{split}.parquet").read_bytes())).to_pylist():
                    self._mmlu_n[f"mmlu_pro/{r['question_id']}"] = len(r["options"])
        return self._mmlu_n[iid]

    def ifeval_record(self, iid: str) -> dict:
        if self._ifeval is None:
            p = ROOT / "manifest/evaluation-sources/ifeval__data__input_data.jsonl"
            self._ifeval = {f"ifeval/{r['key']}": r for r in
                            (json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip())}
        return self._ifeval[iid]

    def score(self, rec: dict) -> dict:
        iid, bench = rec["item_id"], rec["benchmark"]
        status, flags = pre_status(rec)
        out = {"status": status, "flags": flags, "extracted": None, "correct": False, "detail": None}
        if status != "SCORABLE":
            return out
        final = rec["final_text"]
        if bench == "mmlu_pro":
            st, fl, ex = self.s.score_mmlu_pro(final, self.mmlu_n_choices(iid), self.keys[iid]["answer"])
        elif bench == "math500":
            st, fl, ex = self.s.score_math500(final, self.keys[iid]["answer"], self.verifier, iid)
        elif bench == "bbeh_mini":
            st, fl, ex = self.s.score_bbeh(final, self.keys[iid]["answer"])
        elif bench == "ifeval":
            r = self.s.ifeval_evaluate(self.ifeval_record(iid), final)
            st = "CORRECT" if r["strict_prompt"] else "INCORRECT"
            fl, ex = [], None
            out["detail"] = r
        elif bench == "student":
            from app.evaluation import graders, suite
            g = graders.grade(suite.get(iid.split("/", 1)[1]), final, allow_code_execution=False)
            st = "SKIPPED" if g.skipped else ("CORRECT" if g.passed else "INCORRECT")
            fl, ex = [], None
            out["detail"] = {"score": g.score, "passed": g.passed, "skipped": g.skipped}
        else:
            raise ValueError(bench)
        out.update(status=st, flags=sorted(set(flags + fl)), extracted=ex, correct=(st == "CORRECT"))
        return out


def main(run_dir: Path, out_name: str = "scored.jsonl") -> None:
    sc = Scorer()
    rows = []
    for p in sorted(run_dir.glob("attempts_*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                if rec.get("kind") != "item":
                    continue
                rows.append({k: rec[k] for k in ("model", "item_id", "benchmark", "stage", "attempt") if k in rec}
                            | {"completion_tokens": rec.get("completion_tokens"), "finish_reason": rec.get("finish_reason"),
                               "abort": rec.get("abort")} | sc.score(rec))
    sc.verifier.close()
    (run_dir / out_name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"scored {len(rows)} attempts -> {run_dir / out_name}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), *(sys.argv[2:3]))

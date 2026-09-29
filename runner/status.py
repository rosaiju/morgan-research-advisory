"""Primary attempt status and flags (manifest/evaluation.json attempt_status; v2 finish-reason mapping).

Precedence: INFRASTRUCTURE_FAILURE > PROVIDER_FILTERED > MALFORMED_NATIVE_OUTPUT > BUDGET_TRUNCATED >
NO_FINAL_ANSWER > (scorer: EXTRACTION_FAILURE > INCORRECT > CORRECT). This module decides everything up
to NO_FINAL_ANSWER; answer scoring happens later in a separate scorer that alone reads the answer key.
"""

from __future__ import annotations

from collections import Counter

INFRA = {"insufficient_system_resource", "aborted", "network_error", "model_context_window_exceeded", None}
FILTERED = {"content_filter", "sensitive"}


def loop_suspected(text: str, n: int = 12, threshold: int = 10) -> bool:
    words = text.split()
    if len(words) < n * threshold:
        return False
    grams = Counter(tuple(words[i:i + n]) for i in range(len(words) - n + 1))
    return grams.most_common(1)[0][1] >= threshold


def classify(record: dict, *, transport_error: bool = False) -> tuple[str, list[str]]:
    """Return (pre-scoring status, flags). 'SCORABLE' means pass the final channel to the scorer."""
    flags: list[str] = []
    text = (record.get("reasoning_text") or "") + (record.get("final_text") or "")
    if loop_suspected(text):
        flags.append("loop_suspected")
    finish = record.get("finish_reason")
    if record.get("seed_unsupported"):
        flags.append("seed_unsupported_by_backend")
    if transport_error or finish in INFRA:
        return "INFRASTRUCTURE_FAILURE", flags
    if finish in FILTERED:
        return "PROVIDER_FILTERED", flags
    if finish == "tool_calls":
        return "MALFORMED_NATIVE_OUTPUT", flags
    if finish == "repetition_truncation":  # Xiaomi server-side loop intervention
        flags.append("provider_repetition_truncation")
        return "NO_FINAL_ANSWER", flags
    if finish == "length":
        if record.get("final_text"):
            flags.append("final_channel_after_cap_partial")
        return "BUDGET_TRUNCATED", flags
    if finish != "stop":
        return "MALFORMED_NATIVE_OUTPUT", flags
    if not (record.get("final_text") or "").strip():
        return "NO_FINAL_ANSWER", flags
    return "SCORABLE", flags

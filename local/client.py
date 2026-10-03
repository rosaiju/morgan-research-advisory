"""Streaming chat-completion client for llama-server with the approved loop early-stop and watchdog.

Loop early-stop (approved 2026-10-02): abort when any 12-token n-gram occurs >= 20 times within the
last 2048 generated tokens, checked every 64 tokens. Streamed delta chunks are llama-server's per-token
pieces, so a piece is one generated token.
"""
from __future__ import annotations

import hashlib
import http.client
import json
import socket
import time
from collections import Counter

LOOP_N, LOOP_REPEATS, LOOP_WINDOW, LOOP_EVERY = 12, 20, 2048, 64


def loop_detected(pieces: list[str]) -> bool:
    window = pieces[-LOOP_WINDOW:]
    if len(window) < LOOP_N * LOOP_REPEATS:
        return False
    grams = Counter(tuple(window[i:i + LOOP_N]) for i in range(len(window) - LOOP_N + 1))
    return grams.most_common(1)[0][1] >= LOOP_REPEATS


def build_body(model_cfg: dict, common: dict, user_text: str, max_tokens: int, seed: int) -> dict:
    s = model_cfg["sampling"]
    return {
        "messages": [{"role": "user", "content": user_text}],
        "stream": True, "stream_options": {"include_usage": True},
        "max_tokens": max_tokens, "seed": seed,
        "temperature": s["temperature"], "top_p": s["top_p"], "top_k": s["top_k"], "min_p": s["min_p"],
        "presence_penalty": common["presence_penalty"], "frequency_penalty": common["frequency_penalty"],
        "repeat_penalty": common["repeat_penalty"], "typical_p": common["typical_p"],
        "dry_multiplier": common["dry_multiplier"], "xtc_probability": common["xtc_probability"],
        "mirostat": common["mirostat"], "cache_prompt": common["cache_prompt"],
        "chat_template_kwargs": model_cfg["chat_template_kwargs"],
    }


def payload_sha256(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def stream_chat(port: int, body: dict, *, first_token_s: float, stall_s: float, total_s: float,
                loop_stop: bool = True, answer_cap: int | None = None, reasoning_cap: int | None = None) -> dict:
    rec = {"reasoning_text": "", "final_text": "", "finish_reason": None, "usage": None, "timings": None,
           "n_pieces": 0, "abort": None, "error": None, "t_first_token_s": None, "t_first_final_s": None,
           "wall_s": None}
    reasoning, final, pieces = [], [], []
    last_check = 0
    n_final = 0
    n_reason = 0
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=first_token_s)
    t0 = time.perf_counter()
    try:
        conn.request("POST", "/v1/chat/completions", body=json.dumps(body).encode("utf-8"),
                     headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        if resp.status != 200:
            rec["error"] = f"HTTP {resp.status}: {resp.read()[:500]!r}"
            return rec
        while True:
            try:
                raw = resp.readline()
            except (socket.timeout, TimeoutError):
                rec["abort"] = "first_token_timeout" if rec["t_first_token_s"] is None else "stall_timeout"
                break
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace").strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            if chunk.get("timings"):
                rec["timings"] = chunk["timings"]
            if chunk.get("usage"):
                rec["usage"] = chunk["usage"]
            for ch in chunk.get("choices") or []:
                d = ch.get("delta") or {}
                r, c = d.get("reasoning_content"), d.get("content")
                if r or c:
                    now = time.perf_counter() - t0
                    if rec["t_first_token_s"] is None:
                        rec["t_first_token_s"] = round(now, 3)
                        conn.sock.settimeout(stall_s)
                    if r:
                        reasoning.append(r)
                        pieces.append(r)
                        n_reason += 1
                    if c:
                        if rec["t_first_final_s"] is None and c.strip():
                            rec["t_first_final_s"] = round(now, 3)
                        final.append(c)
                        pieces.append(c)
                        n_final += 1
                if ch.get("finish_reason"):
                    rec["finish_reason"] = ch["finish_reason"]
            if loop_stop and len(pieces) - last_check >= LOOP_EVERY:
                last_check = len(pieces)
                if loop_detected(pieces):
                    rec["abort"] = "loop_terminated"
                    break
            if reasoning_cap is not None and n_final == 0 and n_reason >= reasoning_cap:
                rec["abort"] = "reasoning_budget_reached"
                break
            if answer_cap is not None and n_final > answer_cap:
                rec["abort"] = "answer_allowance_exceeded"
                break
            if time.perf_counter() - t0 > total_s:
                rec["abort"] = "total_timeout"
                break
    except (ConnectionError, http.client.HTTPException, OSError) as e:
        rec["error"] = repr(e)
    finally:
        conn.close()  # closing the socket makes llama-server cancel the task
        rec["wall_s"] = round(time.perf_counter() - t0, 3)
        rec["reasoning_text"], rec["final_text"] = "".join(reasoning), "".join(final)
        rec["n_pieces"] = len(pieces)
        rec["n_final_pieces"] = n_final
        rec["n_reasoning_pieces"] = n_reason
    return rec

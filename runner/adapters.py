"""Provider adapters for the Morgan capability study (offline-testable; network is gated).

Pure functions build and hash request payloads, parse streamed responses and normalise them into one
attempt record. Sending is possible only through `Transport.send`, which refuses unless a stage
authorisation file exists AND MORGAN_ALLOW_NETWORK=1 is set in the environment. No key is ever read
before sending, and keys never enter payloads, hashes, records or logs.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator

RUNNER = Path(__file__).resolve().parent
PACKAGE = RUNNER.parent
AUTH_FILE = RUNNER / "AUTHORIZATION.json"  # created by the user per stage; never contains secrets


class GateClosed(RuntimeError):
    pass


@dataclass(frozen=True)
class Route:
    model: str
    route_id: str
    api_style: str
    base_url_env: str
    base_url_default: str | None
    key_env: str
    model_string: str
    max_output_param: str
    route_max_output: int
    body: dict
    price: dict | None
    seed_param: str | None
    reasoning_field: str | None
    extra_finish_reasons: dict = field(default_factory=dict)
    client_rendering: dict | None = None


def load_routes(path: Path = RUNNER / "routes.json") -> dict[str, Route]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    return {r["route_id"]: Route(
        model=r["model"], route_id=r["route_id"], api_style=r["api_style"],
        base_url_env=r["base_url_env"], base_url_default=r.get("base_url_default"), key_env=r["key_env"],
        model_string=r["model_string"], max_output_param=r["max_output_param"],
        route_max_output=int(r["route_max_output"]["value"]), body=r.get("body", {}),
        price=r.get("price_usd_per_m"), seed_param=r.get("seed_param"), reasoning_field=r.get("reasoning_field"),
        extra_finish_reasons=r.get("extra_finish_reasons", {}), client_rendering=r.get("client_rendering"),
    ) for r in spec["routes"]}


def item_seed(item_id: str) -> int:
    return int(hashlib.sha256(f"Morgan-2026-09-29|{item_id}".encode()).hexdigest()[:8], 16) & 0x7FFFFFFF


def render_qwen_prompt(user_text: str, rendering: dict) -> str:
    """Client-side rendering with the pinned Jinja template (dedicated raw-completions route only)."""
    import jinja2  # optional dependency, needed only for this route

    template_text = (PACKAGE / rendering["template"]).read_text(encoding="utf-8")
    env = jinja2.Environment(trim_blocks=True, lstrip_blocks=True)
    env.globals["raise_exception"] = lambda msg: (_ for _ in ()).throw(ValueError(msg))
    return env.from_string(template_text).render(messages=[{"role": "user", "content": user_text}], **rendering["kwargs"])


def build_request(route: Route, user_text: str, ceiling: int, item_id: str) -> dict:
    """Return the exact JSON body to send (no secrets). Raises if the ceiling exceeds the route limit."""
    if ceiling > route.route_max_output:
        raise ValueError(f"{route.route_id}: ceiling {ceiling} exceeds documented route maximum {route.route_max_output}")
    body: dict = {"model": route.model_string, "stream": True}
    if route.api_style == "openai_chat":
        body["messages"] = [{"role": "user", "content": user_text}]
        body["stream_options"] = {"include_usage": True}
    elif route.api_style == "openai_completions_raw":
        body["prompt"] = render_qwen_prompt(user_text, route.client_rendering)
    else:
        raise ValueError(f"unknown api_style {route.api_style}")
    body.update(json.loads(json.dumps(route.body)))  # deep copy of fixed study parameters
    body[route.max_output_param] = ceiling
    if route.seed_param:
        body[route.seed_param] = item_seed(item_id)
    return body


def payload_sha256(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def parse_sse(lines: Iterable[str]) -> dict:
    """Aggregate OpenAI-style streamed chunks (chat or completions) into one response dict."""
    out = {"reasoning": [], "final": [], "finish_reason": None, "usage": None, "model_echo": None,
           "system_fingerprint": None, "chunks": 0, "stop_detail": None}
    for raw in lines:
        line = raw.strip()
        if not line.startswith("data:"):
            continue  # keep-alive comments and blank lines
        data = line[5:].strip()
        if data == "[DONE]":
            break
        chunk = json.loads(data)
        out["chunks"] += 1
        out["model_echo"] = chunk.get("model", out["model_echo"])
        out["system_fingerprint"] = chunk.get("system_fingerprint", out["system_fingerprint"])
        if chunk.get("usage"):
            out["usage"] = chunk["usage"]
        for choice in chunk.get("choices", []):
            delta = choice.get("delta", {})
            if delta.get("reasoning_content"):
                out["reasoning"].append(delta["reasoning_content"])
            if delta.get("content"):
                out["final"].append(delta["content"])
            if choice.get("text"):
                out["final"].append(choice["text"])
            if choice.get("finish_reason"):
                out["finish_reason"] = choice["finish_reason"]
                out["stop_detail"] = choice.get("stop_reason", out["stop_detail"])
    out["reasoning"] = "".join(out["reasoning"])
    out["final"] = "".join(out["final"])
    return out


def split_raw_completion(text: str) -> tuple[str, str | None]:
    """Raw-completion route: the rendered prompt already opens '<think>\\n'."""
    if "</think>" not in text:
        return text, None
    reasoning, final = text.split("</think>", 1)
    return reasoning, final.strip()


def normalise(route: Route, parsed: dict) -> dict:
    if route.api_style == "openai_completions_raw":
        reasoning, final = split_raw_completion(parsed["final"])
    else:
        reasoning, final = parsed["reasoning"], (parsed["final"] if parsed["final"].strip() else None)
    usage = parsed.get("usage") or {}
    details = usage.get("completion_tokens_details") or {}
    return {
        "route_id": route.route_id,
        "model_echo": parsed.get("model_echo"),
        "system_fingerprint": parsed.get("system_fingerprint"),
        "finish_reason": parsed.get("finish_reason"),
        "stop_detail": parsed.get("stop_detail"),
        "reasoning_text": reasoning,
        "final_text": final,
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "reasoning_tokens": details.get("reasoning_tokens"),
    }


def estimated_cost(route: Route, record: dict) -> float | None:
    if not route.price or record.get("completion_tokens") is None:
        return None
    return (record.get("prompt_tokens") or 0) / 1e6 * route.price["input"] + record["completion_tokens"] / 1e6 * route.price["output"]


REDACT = re.compile(r"(sk-[A-Za-z0-9_\-]{8,}|Bearer\s+[A-Za-z0-9_\-\.]{8,}|[A-Za-z0-9]{32,})")


def redact(text: str) -> str:
    return REDACT.sub("[REDACTED]", text)


def check_gate(stage: str, route: Route) -> dict:
    """Refuse unless the user created AUTHORIZATION.json for this stage and route, and opted in via env."""
    if os.environ.get("MORGAN_ALLOW_NETWORK") != "1":
        raise GateClosed("network disabled: MORGAN_ALLOW_NETWORK is not '1'")
    if not AUTH_FILE.exists():
        raise GateClosed(f"no {AUTH_FILE.name}: no stage has been authorised")
    auth = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    if auth.get("stage") != stage:
        raise GateClosed(f"authorised stage is {auth.get('stage')!r}, not {stage!r}")
    if route.route_id not in auth.get("routes", []):
        raise GateClosed(f"route {route.route_id} not authorised for stage {stage}")
    for k in ("max_usd", "max_requests", "authorized_by", "date"):
        if k not in auth:
            raise GateClosed(f"{AUTH_FILE.name} lacks {k}")
    return auth


class Transport:
    """Streams one request. Only callable after check_gate; the key is read here and nowhere else."""

    def __init__(self, stage: str, timeout_s: int = 1800):
        self.stage, self.timeout_s = stage, timeout_s

    def send(self, route: Route, body: dict) -> Iterator[str]:
        check_gate(self.stage, route)
        key = os.environ.get(route.key_env)
        if not key:
            raise GateClosed(f"environment variable {route.key_env} is not set")
        base = os.environ.get(route.base_url_env) or route.base_url_default
        if not base:
            raise GateClosed(f"environment variable {route.base_url_env} is not set")
        path = "/chat/completions" if route.api_style == "openai_chat" else "/completions"
        req = urllib.request.Request(base.rstrip("/") + path, data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                              "Accept": "text/event-stream"})
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:  # read timeout = no-token watchdog
            for raw in resp:
                yield raw.decode("utf-8", "replace")

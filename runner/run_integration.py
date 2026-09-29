"""Stage-2 integration test executor (34 synthetic requests; runner/integration_plan.json).

    python runner/run_integration.py            # DRY RUN (default): build + hash all payloads, send nothing
    python runner/run_integration.py --send     # real run: refuses unless the stage gate is open

The real run requires MORGAN_ALLOW_NETWORK=1, runner/AUTHORIZATION.json (stage 'integration', the routes,
max_usd, max_requests) and the provider key variables. Every request is logged to
runs/integration-<timestamp>.jsonl WITHOUT keys; the run stops when the spend or request cap is reached.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import adapters as A  # noqa: E402
import status as S  # noqa: E402

PLAN = json.loads((A.RUNNER / "integration_plan.json").read_text(encoding="utf-8"))
ROUTES = A.load_routes()
EFFORT_ROUTES = {"P25-deepseek", "P28-zai", "P27-zai", "P29-moonshot", "P34-deepinfra-fp4"}


def set_effort(route: A.Route, body: dict, value: str) -> dict:
    if "reasoning_effort" in body:
        body["reasoning_effort"] = value
    kw = body.get("chat_template_kwargs")
    if kw is not None and "reasoning_effort" in kw:
        kw["reasoning_effort"] = value
    return body


def planned_requests() -> list[dict]:
    tests = {t["id"]: t for t in PLAN["tests"]}
    out = []
    for route_id, test_ids in PLAN["routes_in_first_paid_test"].items():
        route = ROUTES[route_id]
        for tid in test_ids:
            t = tests[tid]
            seed_id = "integration/T1" if tid == "T5" else f"integration/{tid}"  # T5 repeats T1's payload exactly
            body = A.build_request(route, PLAN["prompts"][t["prompt"]]["text"], t["ceiling"], seed_id)
            if tid == "T3b":
                body = set_effort(route, body, "low")
            if tid == "T4":
                body = set_effort(route, body, "maxx")
            out.append({"route_id": route_id, "test": tid, "body": body, "payload_sha256": A.payload_sha256(body),
                        "expected_final": PLAN["prompts"][t["prompt"]]["expected_final"]})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true")
    args = ap.parse_args()
    reqs = planned_requests()
    assert len(reqs) == PLAN["request_count"]["total"], (len(reqs), PLAN["request_count"]["total"])
    if not args.send:
        for r in reqs:
            b = r["body"]
            limit = next((b[k] for k in ("max_tokens", "max_completion_tokens") if k in b), None)
            print(f"DRY {r['route_id']:18} {r['test']:4} limit={limit!s:>7} effort={b.get('reasoning_effort', b.get('chat_template_kwargs', {}).get('reasoning_effort', '-'))!s:6} sha={r['payload_sha256'][:12]}")
        print(f"DRY RUN: {len(reqs)} requests built; nothing sent.")
        return 0

    auth = A.check_gate("integration", ROUTES[reqs[0]["route_id"]])
    if len(reqs) > auth["max_requests"]:
        raise A.GateClosed("plan exceeds max_requests")
    log_dir = A.PACKAGE / "runs"
    log_dir.mkdir(exist_ok=True)
    log = log_dir / f"integration-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.jsonl"
    spent = 0.0
    transport = A.Transport("integration")
    with log.open("w", encoding="utf-8") as fh:
        for r in reqs:
            route = ROUTES[r["route_id"]]
            if spent >= auth["max_usd"]:
                print("spend cap reached; stopping")
                break
            t0 = time.time()
            rec: dict = {"route_id": r["route_id"], "test": r["test"], "payload_sha256": r["payload_sha256"],
                         "sent_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
            try:
                parsed = A.parse_sse(transport.send(route, r["body"]))
                rec.update(A.normalise(route, parsed))
                rec["status"], rec["flags"] = S.classify(rec)
                rec["http"] = 200
            except A.GateClosed:
                raise
            except Exception as exc:  # noqa: BLE001  (HTTP 4xx expected for T4)
                rec.update({"error": A.redact(repr(exc))[:500], "status": "HTTP_ERROR"})
            rec["wall_s"] = round(time.time() - t0, 2)
            cost = A.estimated_cost(route, rec) or 0.0
            spent += cost
            rec["estimated_cost_usd"] = round(cost, 6)
            rec["final_matches_expected"] = (rec.get("final_text") or "").strip() == r["expected_final"]
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            print(f"{r['route_id']:18} {r['test']:4} {rec.get('status')!s:24} finish={rec.get('finish_reason')!s:8} "
                  f"completion={rec.get('completion_tokens')!s:>7} cost=${cost:.4f}")
    print(f"log: {log}   estimated spend: ${spent:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

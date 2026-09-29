# Runner (adapter layer): prepared, offline-tested, never used

Nothing in this folder has sent a request. Architecture, routes and the first paid test are described in
[../19-readiness-and-calibration-plan.md](../19-readiness-and-calibration-plan.md) §7–§8.

```
python runner/test_offline.py   # 14 offline tests (no network, no keys)
python runner/secret_scan.py    # must print "no credential-like strings found"
python runner/run_integration.py # DRY RUN: builds and hashes the 34 integration payloads; sends nothing
                                # (--send is refused unless the stage gate is open)
```

## Safety locks

Sending requires **both** of these. Neither exists, and neither may be created without the user's authorisation:
1. **Environment:** `MORGAN_ALLOW_NETWORK=1`.
2. **Authorisation file:** `runner/AUTHORIZATION.json`, written by the user. It holds no secrets; it is git-ignored anyway:

```json
{"stage": "integration", "routes": ["P35-deepinfra", "P25-deepseek", "P28-zai", "P27-zai", "P29-moonshot", "P34-deepinfra-fp4"],
 "max_usd": 15, "max_requests": 34, "authorized_by": "<name>", "date": "YYYY-MM-DD"}
```

## Keys

- **Storage:** keys live only in environment variables; the names are in `.env.example`.
- **Loading:** a key is read inside `Transport.send` and nowhere else.
- **Exposure:** keys are never written to payloads, hashes, logs or manifests.

## Not included yet

- **Orchestration:** the loop over items, the resume/checkpoint store, the spend-cap enforcement across requests, and the JSONL writer.
- **The scorer:** it is the only component allowed to read `manifest/items/answer_key_*.json`.

Both come after the integration test confirms each route's behaviour.

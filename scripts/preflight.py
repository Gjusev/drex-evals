#!/usr/bin/env python3
"""Preflight: verify a Drex endpoint is reachable and answering before a suite run.

Usage:
  python3 scripts/preflight.py                       # uses DREX_BASE_URL env (default hosted)
  python3 scripts/preflight.py http://localhost:8000 # local serve.py from the models repo

Prints PASS/FAIL and exits non-zero on failure, so you can chain:
  python3 scripts/preflight.py http://localhost:8000 && python3 scripts/run_suite.py suites/triage_demo.json
"""
import json
import os
import sys
import urllib.request

base = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DREX_BASE_URL", "https://drex.nace.ai")).rstrip("/")
key = os.environ.get("DREX_API_KEY", "")

body = {
    "state": {"ticket": "The app crashes on startup since the last update, I need this fixed today"},
    "questions": {
        "team": {
            "type": "choice",
            "instructions": "Which team should handle this ticket?",
            "criteria": {"billing": "Payments, charges, refunds", "technical": "Bugs and outages", "other": "Anything else"},
        },
        "refund": {"type": "noul", "instructions": "Does the customer explicitly ask for a refund?"},
        "urgency": {"type": "score", "instructions": "How urgent?", "criteria": ["Routine", "Soon", "Urgent"]},
    },
}

req = urllib.request.Request(
    f"{base}/v1/systemone",
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
    method="POST",
)
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read())
except Exception as exc:  # noqa: BLE001
    print(f"FAIL: {base}/v1/systemone -> {exc}")
    sys.exit(1)

print(f"PASS: {base} answered")
for name, result in payload.get("answers", payload.get("results", {})).items():
    if isinstance(result, dict):
        print(f"  {name}: {json.dumps(result)[:120]}")
print("\nReady. Run a suite: python3 scripts/run_suite.py suites/triage_demo.json")

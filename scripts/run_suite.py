#!/usr/bin/env python3
"""Run a decision suite against a Drex endpoint and print the report.

Usage:
  python3 scripts/run_suite.py suites/triage_demo.json
  python3 scripts/run_suite.py suites/triage_demo.json --mock    # offline plumbing check
Env: DREX_BASE_URL (default https://drex.nace.ai), DREX_API_KEY
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from drexevals import DrexClient, MockDrexClient, Question, run_suite  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("suite")
    ap.add_argument("--mock", action="store_true", help="offline mock client (no network)")
    args = ap.parse_args()

    raw = json.loads(Path(args.suite).read_text())
    cases = []
    for c in raw["cases"]:
        cases.append({
            "state": c["state"],
            "questions": [Question(**q) for q in c["questions"]],
            "expected": c["expected"],
        })

    client = MockDrexClient(rules={}) if args.mock else DrexClient()
    report = run_suite(client, cases)
    print(json.dumps(report, indent=2))

    out = Path(args.suite).with_suffix(".report.json")
    out.write_text(json.dumps(report, indent=2))
    print(f"\nreport -> {out}")


if __name__ == "__main__":
    main()

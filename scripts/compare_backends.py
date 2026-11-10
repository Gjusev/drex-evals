#!/usr/bin/env python3
"""Cross-backend comparison: same suite, several Drex endpoints -> one table.

Answers the roadmap question: "can I self-host without losing calibration?"
Runs the same suite against N backends (hosted, local Q8, local Q4...), prints
accuracy / avg confidence / Brier / ECE / confidence-on-wrong per question per
backend, and writes a combined JSON for the README table.

Usage:
  python3 scripts/compare_backends.py suites/triage_demo.json \
      --backend hosted https://drex.nace.ai "$DREX_API_KEY" \
      --backend local-q8 http://localhost:8000 "" \
      --backend local-q4 http://localhost:8001 ""
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from drexevals import DrexClient, MockDrexClient, Question, run_suite  # noqa: E402


def load_cases(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [{
        "state": c["state"],
        "questions": [Question(**q) for q in c["questions"]],
        "expected": c["expected"],
        **({"group": c["group"]} if "group" in c else {}),
    } for c in raw["cases"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("suite")
    ap.add_argument("--backend", action="append", nargs=3,
                    metavar=("NAME", "URL", "API_KEY"), required=True)
    args = ap.parse_args()

    cases = load_cases(args.suite)
    combined = {"suite": args.suite, "backends": {}}
    print(f"suite: {args.suite} ({len(cases)} cases)\n")

    for name, url, key in args.backend:
        if name == "mock":
            client = MockDrexClient(rules={})
        else:
            client = DrexClient(base_url=url, api_key=key)
        print(f"=== {name} ({url}) ===")
        try:
            report = run_suite(client, cases)
        except Exception as exc:  # noqa: BLE001
            print(f"  FAILED: {exc}\n")
            combined["backends"][name] = {"error": str(exc)}
            continue
        for qname, s in report.items():
            print(f"  {qname:10} acc={s['accuracy']:.0%}  "
                  f"conf={s['avg_confidence']:.2f}  "
                  f"brier={s['brier']:.3f}  ece={s['ece']:.3f}  "
                  f"conf_on_wrong={s['confidence_on_wrong']:.2f}")
        combined["backends"][name] = report
        print()

    out = Path(args.suite).with_suffix(".comparison.json")
    out.write_text(json.dumps(combined, indent=2))
    print(f"combined -> {out}")


if __name__ == "__main__":
    main()

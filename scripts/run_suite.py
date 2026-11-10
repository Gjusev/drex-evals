#!/usr/bin/env python3
"""Run a decision suite against a Drex endpoint and print the report.

Usage:
  python3 scripts/run_suite.py suites/triage_demo.json
  python3 scripts/run_suite.py suites/triage_demo.json --mock    # offline plumbing check
  python3 scripts/run_suite.py suites/triage_demo.json \
      --model "drex-v1.5 Q8_0" --out results/triage_demo.local-q8.report.json
Env: DREX_BASE_URL (default https://drex.nace.ai), DREX_API_KEY
"""
import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from drexevals import DrexClient, MockDrexClient, Question, run_suite, __version__  # noqa: E402


def backend_kind(url: str, mock: bool) -> str:
    if mock:
        return "mock"
    host = urlparse(url).hostname or ""
    return "hosted" if host.endswith("nace.ai") else "local"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("suite")
    ap.add_argument("--mock", action="store_true", help="offline mock client (no network)")
    ap.add_argument("--model", help="weights identifier recorded in report meta (e.g. 'drex-v1.5 Q8_0')")
    ap.add_argument("--out", help="report path (default: <suite>.report.json next to the suite)")
    args = ap.parse_args()

    suite_path = Path(args.suite)
    raw = json.loads(suite_path.read_text())
    cases = []
    for c in raw["cases"]:
        cases.append({
            "state": c["state"],
            "questions": [Question(**q) for q in c["questions"]],
            "expected": c["expected"],
        })

    client = MockDrexClient(rules={}) if args.mock else DrexClient()
    url = "mock" if args.mock else client.base_url
    report = run_suite(client, cases)

    print(f"suite {suite_path} ({len(cases)} cases)  backend={url} kind={backend_kind(url, args.mock)}")
    for qname, s in report.items():
        print(f"  {qname:10} acc={s['accuracy']:.0%}  conf={s['avg_confidence']:.2f}  "
              f"brier={s['brier']:.3f}  ece={s['ece']:.3f}  "
              f"conf_on_wrong={s['confidence_on_wrong']:.2f}")
    print()
    print(json.dumps(report, indent=2))

    meta = {
        "suite": suite_path.as_posix(),
        "suite_sha256": hashlib.sha256(suite_path.read_bytes()).hexdigest(),
        "backend_url": url,
        "backend_kind": backend_kind(url, args.mock),
        "model": args.model,
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "n_cases": len(cases),
        "drexevals_version": __version__,
    }
    out = Path(args.out) if args.out else suite_path.with_suffix(".report.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"meta": meta, "results": report}, indent=2))
    print(f"\nreport -> {out}")


if __name__ == "__main__":
    main()

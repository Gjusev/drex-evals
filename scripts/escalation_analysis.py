#!/usr/bin/env python3
"""Escalation-policy analysis over committed reports.

For every (suite, backend, question): sweep act/ask confidence thresholds
against the report's reliability bins and report the tradeoff — coverage
(share auto-acted) vs empirical risk (wrong among auto-acted). Also the
calibrated tau* for risk budgets of 5% and 2%.

Bin-level resolution (10 bins from ece_bins); per-case pairs are not stored,
so each bin is collapsed onto its avg_confidence: risk(tau) is a step
function whose only candidate thresholds are the bin averages — within a
bin, all cases act or none do. Deploying a reported tau* against true
per-case confidences can split a bin differently than quantized here.

Usage: python3 scripts/escalation_analysis.py results/*.report.json
"""
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from drexevals.gate import calibrate_threshold, risk_at  # noqa: E402

RISK_BUDGETS = (0.05, 0.02)
TAU_GRID = (0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99)


def pairs_from_bins(bins: list[dict]):
    """Expand reliability bins into (confidence, correct) pairs, weighted by n."""
    pairs = []
    for b in bins:
        n_right = round(b["observed_accuracy"] * b["n"])
        pairs += [(b["avg_confidence"], True)] * int(n_right)
        pairs += [(b["avg_confidence"], False)] * (b["n"] - int(n_right))
    return pairs


def main():
    paths = sys.argv[1:] or sorted(glob.glob("results/*.report.json"))
    out = {}
    for path in paths:
        report = json.loads(Path(path).read_text(encoding="utf-8"))
        backend = report["meta"].get("model") or report["meta"]["backend_kind"]
        for q, s in report["results"].items():
            if backend in out.setdefault(f"{report['meta']['suite']}:{q}", {}):
                print(f"warning: duplicate {backend} row for {report['meta']['suite']}:{q} (overwriting {path})", file=sys.stderr)
            pairs = pairs_from_bins(s["ece_bins"])
            if not pairs:
                continue
            key = f"{report['meta']['suite']}:{q}"
            row = out.setdefault(key, {})
            sweep = {f"{tau:.2f}": dict(zip(("risk", "coverage"), risk_at(pairs, tau))) for tau in TAU_GRID}
            row[backend] = {
                "n": s["n"],
                "sweep": sweep,
                "calibrated": {
                    f"{int(r * 100)}%": dict(zip(("tau", "coverage", "risk"), calibrate_threshold(pairs, r)))
                    for r in RISK_BUDGETS
                },
            }

    for key in sorted(out):
        print(f"== {key}")
        for backend, r in out[key].items():
            cal = "  ".join(
                f"risk<={b} tau={v['tau']:.2f} cov={v['coverage']:.0%}"
                for b, v in r["calibrated"].items()
            )
            print(f"  {backend:10} {cal}")
    out_path = Path("results/escalation_policies.json")
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nfull sweep -> {out_path}")


if __name__ == "__main__":
    main()

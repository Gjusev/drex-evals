#!/usr/bin/env python3
"""Build suites/laya_triage_de25.json — the German subset of laya-triage's
hand-labeled tickets.

Same source, labels and question wording as import_laya_triage.py (see that
script for provenance), restricted to lang=de: 25 tickets. n=25 is thin —
read the calibration numbers as directional only; the suite exists to make
German performance visible separately from the multilingual mix.

Usage: python3 scripts/import_laya_triage_de.py
"""
import importlib.util
import json
import subprocess
from pathlib import Path

EVALS = Path(__file__).resolve().parent.parent
LAYA = EVALS.parent / "laya-triage"

# question definitions come verbatim from the multilingual importer so the
# German suite stays directly comparable to laya_triage_200
_spec = importlib.util.spec_from_file_location("laya_import", EVALS / "scripts" / "import_laya_triage.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
CLUSTER_Q, URGENCY_Q, FRUSTRATION_Q = _mod.CLUSTER_Q, _mod.URGENCY_Q, _mod.FRUSTRATION_Q
URGENCY_LEVELS, FRUSTRATION_LEVELS = _mod.URGENCY_LEVELS, _mod.FRUSTRATION_LEVELS


def main():
    src = LAYA / "data" / "hand_labeled_200.jsonl"
    sha = subprocess.run(
        ["git", "-C", str(LAYA), "log", "-1", "--format=%h", "--", "data/hand_labeled_200.jsonl"],
        capture_output=True, text=True,
    ).stdout.strip()

    rows = [json.loads(line) for line in src.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = [r for r in rows if r["lang"] == "de"]
    cases = [{
        "state": {"ticket": r["text"]},
        "questions": [CLUSTER_Q, URGENCY_Q, FRUSTRATION_Q],
        "expected": {
            "cluster": r["cluster"],
            "urgency": URGENCY_LEVELS[r["urgency"]],
            "frustration": FRUSTRATION_LEVELS[r["frustration"]],
        },
    } for r in rows]

    suite = {
        "name": "laya_triage_de25",
        "description": (
            f"German-only banking-support triage (25 tickets), the lang=de subset of "
            f"laya-triage data/hand_labeled_200.jsonl @ {sha}. Same labels and question "
            "wording as laya_triage_200. n=25: directional only. German is the real "
            "workload; this suite isolates it from the multilingual mix."
        ),
        "questions_schema": [CLUSTER_Q, URGENCY_Q, FRUSTRATION_Q],
        "cases": cases,
    }
    out = EVALS / "suites" / "laya_triage_de25.json"
    out.write_text(json.dumps(suite, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(cases)} German cases -> {out}")


if __name__ == "__main__":
    main()

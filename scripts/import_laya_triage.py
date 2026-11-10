#!/usr/bin/env python3
"""Build suites/laya_triage_200.json from laya-triage's hand-labeled tickets.

Source: ../laya-triage/data/hand_labeled_200.jsonl (commit recorded in the
suite description). Labels per laya-triage's data/annotation_guide.md:
cluster (12-way choice), urgency and frustration (0-3 ordinal).

Provenance caveat the suite inherits: tickets are AI-authored and the labels
come from two blind AI annotation passes with disagreements adjudicated
(kappa 0.78-0.91) — a training/eval aid, not human gold (the guide says so).
Languages: 60 en, 60 es, 25 fr, 25 de, 15 hi, 15 ar.

Usage: python3 scripts/import_laya_triage.py
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

EVALS = Path(__file__).resolve().parent.parent
LAYA = EVALS.parent / "laya-triage"

# load schema.py directly (standalone module) — importing the laya_triage
# package would drag in its pipeline deps
_spec = importlib.util.spec_from_file_location("laya_schema", LAYA / "src" / "laya_triage" / "schema.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
CLUSTER_DESCRIPTIONS = _mod.CLUSTER_DESCRIPTIONS

URGENCY_LEVELS = ["none", "some", "high", "drop-everything"]
FRUSTRATION_LEVELS = ["calm", "concerned", "annoyed", "angry"]

CLUSTER_Q = {
    "name": "cluster",
    "type": "choice",
    "instructions": "Which problem cluster does this ticket belong to?",
    "criteria": CLUSTER_DESCRIPTIONS,
}
URGENCY_Q = {
    "name": "urgency",
    "type": "score",
    "instructions": (
        "How urgently does this ticket need a response? Levels, lowest first: "
        "none = no time element at all (general questions, curiosity, 'sometime'); "
        "some = mild time preference ('soon') or a live inconvenience worked around without loss; "
        "high = explicit deadline, money stuck or blocked now, a core action impossible today, "
        "or 'as soon as possible' said plainly; "
        "drop-everything = active loss in progress (fraud, double charge happening, card "
        "compromised), security exposure, or explicit now-markers. "
        "Urgency is not anger: a perfectly calm ticket can be drop-everything."
    ),
    "criteria": URGENCY_LEVELS,
}
FRUSTRATION_Q = {
    "name": "frustration",
    "type": "score",
    "instructions": (
        "How frustrated is the customer's tone? Levels, lowest first: "
        "calm = polite, factual or positive; "
        "concerned = worried or mildly negative wording, still civil; "
        "annoyed = clear complaints ('ridiculous', 'again', 'third time'), sarcasm, pointed criticism; "
        "angry = strong language, profanity, shouting, threats to leave, legal or regulator threats. "
        "Judge the words on the page, not the situation's objective severity."
    ),
    "criteria": FRUSTRATION_LEVELS,
}


def main():
    src = LAYA / "data" / "hand_labeled_200.jsonl"
    sha = subprocess.run(
        ["git", "-C", str(LAYA), "log", "-1", "--format=%h", "--", "data/hand_labeled_200.jsonl"],
        capture_output=True, text=True,
    ).stdout.strip()

    rows = [json.loads(line) for line in src.read_text(encoding="utf-8").splitlines() if line.strip()]
    cases = [{
        "state": {"ticket": r["text"]},
        "questions": [CLUSTER_Q, URGENCY_Q, FRUSTRATION_Q],
        "expected": {
            "cluster": r["cluster"],
            "urgency": URGENCY_LEVELS[r["urgency"]],
            "frustration": FRUSTRATION_LEVELS[r["frustration"]],
        },
        "group": r["lang"],
    } for r in rows]

    suite = {
        "name": "laya_triage_200",
        "description": (
            f"Multilingual banking-support triage (en/es/fr/de/hi/ar) imported from "
            f"laya-triage data/hand_labeled_200.jsonl @ {sha}. Labels: 12-way cluster "
            "(laya_triage schema), urgency + frustration 0-3 per its annotation guide. "
            "AI-authored tickets, two blind AI annotation passes, disagreements "
            "adjudicated (kappa 0.78-0.91) - an eval aid, not human gold."
        ),
        "questions_schema": [CLUSTER_Q, URGENCY_Q, FRUSTRATION_Q],
        "cases": cases,
    }
    out = EVALS / "suites" / "laya_triage_200.json"
    out.write_text(json.dumps(suite, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(cases)} cases -> {out}")


if __name__ == "__main__":
    main()

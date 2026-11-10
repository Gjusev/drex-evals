#!/usr/bin/env python3
"""Build suites/banking77_cluster_200.json — a stratified sample of BANKING77.

Source: laya-triage/data/external/test.csv (3,080 human-annotated tickets from
the canonical PolyAI BANKING77 dataset — the strongest labels in this repo).
Intents are mapped to the 12 coarse clusters via laya-triage's
INTENT_TO_CLUSTER (a mechanical, committed mapping), so the cluster label
stays human-derived.

Stratified by cluster, seeded (random.Random(20261110)), 200 tickets total.
Question: the same 12-way cluster choice as the laya suites.

Usage: python3 scripts/import_banking77.py
"""
import csv
import importlib.util
import json
import random
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

EVALS = Path(__file__).resolve().parent.parent
LAYA = EVALS.parent / "laya-triage"

_spec = importlib.util.spec_from_file_location("laya_schema", LAYA / "src" / "laya_triage" / "schema.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
CLUSTER_DESCRIPTIONS = _mod.CLUSTER_DESCRIPTIONS
INTENT_TO_CLUSTER = _mod.INTENT_TO_CLUSTER

SAMPLE_N = 200
SEED = 20261110

CLUSTER_Q = {
    "name": "cluster", "type": "choice",
    "instructions": "Which problem cluster does this ticket belong to?",
    "criteria": CLUSTER_DESCRIPTIONS,
}


def main():
    src = LAYA / "data" / "external" / "test.csv"
    if not src.exists():
        raise SystemExit(f"{src} missing — it is gitignored in laya-triage; re-download BANKING77 test.csv from the PolyAI repo")
    sha = subprocess.run(
        ["git", "-C", str(LAYA), "log", "-1", "--format=%h", "--", "src/laya_triage/schema.py"],
        capture_output=True, text=True,
    ).stdout.strip()

    with src.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    by_cluster = defaultdict(list)
    for r in rows:
        by_cluster[INTENT_TO_CLUSTER[r["category"]]].append(r["text"])

    rng = random.Random(SEED)
    per_cluster = SAMPLE_N // len(by_cluster)
    remainder = SAMPLE_N - per_cluster * len(by_cluster)
    picked = []
    for i, (cluster, texts) in enumerate(sorted(by_cluster.items())):
        take = per_cluster + (1 if i < remainder else 0)
        picked += [(cluster, t) for t in rng.sample(sorted(texts), take)]

    cases = [{
        "state": {"ticket": text},
        "questions": [CLUSTER_Q],
        "expected": {"cluster": cluster},
    } for cluster, text in picked]
    rng.shuffle(cases)

    suite = {
        "name": "banking77_cluster_200",
        "description": (
            f"200 tickets stratified by cluster (seed {SEED}) from laya-triage's "
            f"data/external/test.csv — the canonical PolyAI BANKING77 test split, "
            "human-annotated intent labels mapped to the 12 clusters via laya_triage "
            f"schema.py @ {sha}. Strongest labels in this repo: human-derived."
        ),
        "questions_schema": [CLUSTER_Q],
        "cases": cases,
    }
    out = EVALS / "suites" / "banking77_cluster_200.json"
    out.write_text(json.dumps(suite, indent=2, ensure_ascii=False), encoding="utf-8")
    dist = Counter(c["expected"]["cluster"] for c in cases)
    print(f"{len(cases)} cases across {len(dist)} clusters -> {out}")
    print("  min/max per cluster:", min(dist.values()), "/", max(dist.values()))


if __name__ == "__main__":
    main()

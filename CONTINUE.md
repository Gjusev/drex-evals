# CONTINUE.md — read this first when an agent picks up this repo

## What this repo is

Evaluation bridge for Drex decision models (arXiv:2611.07854): typed decision
questions (choice / noul / score) into `/v1/systemone`, calibrated
probabilities out — scored for accuracy AND confidence calibration
(ECE-style bins). Read README.md, ROADMAP.md and docs/MAIN-PC.md fully.

## Working rules

- **Offline-first**: zero-dependency test suite (`python3 -m pytest tests/`)
  with MockDrexClient must stay green. Network clients use stdlib urllib,
  httpx-like deps only if genuinely required (lazy import).
- **Honest claims**: no invented numbers. Every measured result in README
  carries the exact command that produced it.
- Cite the paper first (arXiv:2611.07854); independent evaluation harness,
  not affiliated with Nace.AI.
- Commits in English, conventional-commit style.
- Suites are labeled data: keep `expected` values justified by the case text;
  no label without a reason a reviewer can check.

## Models — Z.ai Coding Plan (mandatory for the dev agent, NOT for Drex runs)

Two different things, don't confuse them:

1. **The coding agent developing this repo** (Claude Code / etc.) runs on the
   Z.ai Coding Plan — flat subscription, no per-call billing.
2. **The Drex endpoint being evaluated** stays whatever MAIN-PC.md says
   (local serve.py or hosted drex.nace.ai). Drex is NOT served by Z.ai —
   never point DREX_BASE_URL at Z.ai.

## Current task (do this now)

ROADMAP.md item 2 — calibration as the headline:

1. Extend `drexevals/runner.py` with Brier score and ECE (10 bins) per
   question, alongside the existing report fields.
2. Extend `scripts/run_suite.py` and `scripts/compare_backends.py` to print
   the new metrics; keep the JSON schema additive.
3. Update the offline tests for the new fields (mock client still passes).
4. Add `results/README.md` template describing what a committed report should
   contain (suite hash, backend url kind, model, date) — do NOT commit
   fabricated results; only real runs go there.
5. If DREX_BASE_URL points at a live endpoint, run `triage_demo.json` and
   commit the real report; otherwise stop after tooling + tests.

## After that

ROADMAP.md in order: real suites (import from gate-calibrated / laya-* /
German tickets) -> cross-model comparison on real endpoints -> gate
integration with conformal risk control (methodology in gate-calibrated).

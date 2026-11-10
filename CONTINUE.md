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

ROADMAP.md item 2 tooling is DONE (Brier + 10-bin ECE in `runner.py`,
printed by both scripts, offline tests updated, `results/README.md` template,
self-describing report envelope with suite sha256 / backend kind / model /
date). What remains is the real run:

- Point `DREX_BASE_URL` at a live endpoint (hosted needs `DREX_API_KEY`), run
  `python3 scripts/preflight.py` — must print PASS.
- Then: `python3 scripts/run_suite.py suites/triage_demo.json --model <weights>
  --out results/triage_demo.<backend>.report.json` and commit the real report
  (see results/README.md). Do NOT commit fabricated results.

2026-11-10 attempt log (agent session): `DREX_BASE_URL`/`DREX_API_KEY` were
not set in the session or Windows user/machine env; hosted drex.nace.ai
answered 401 (no key); no local serve.py on :8000/:8080; no sibling
drex-decision-models repo — live run blocked, tooling committed instead.

2026-11-10 second session: re-verified — preflight against drex.nace.ai
FAILs 401 (still no key anywhere), no local endpoint; live run still blocked.
Committed: calibration tooling + tests + suite label fix (crash-ticket refund
expected `noui` -> `noun`, matching the ticket text and the test fixture).
No report committed — mock runs are plumbing checks, not measurements.

Adversarial review of the metrics then confirmed and fixed: Brier now uses the
label-union form (missing expected option costs (0-1)^2 — omitting the right
answer can no longer score better than listing it), probability validation at
the client trust boundary (rejects NaN/out-of-range, names the option), and
bin-index clamping against negative confidences. Offline tests: 6 passed.

## After that

ROADMAP.md in order: real suites (import from gate-calibrated / laya-* /
German tickets) -> cross-model comparison on real endpoints -> gate
integration with conformal risk control (methodology in gate-calibrated).

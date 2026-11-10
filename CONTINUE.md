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

DONE (2026-11-10): calibration metrics + first real run. See README
"First real run" and `results/triage_demo.local-q8.report.json`. Summary:

- Brier + 10-bin ECE per question in `runner.py`, printed by both scripts;
  adversarially reviewed (label-union Brier, probability validation at the
  client trust boundary, bin clamping). Offline tests: 7 passed.
- Client now parses the documented `/v1/systemone` response contract
  (choice / noul / score shapes from the models repo's request-format.md);
  locked by a test against that documented example.
- First real run: local drex-v1.5 Q8_0 on `triage_demo.json` (n=10).
  refund 100% acc / Brier .000; team routing overconfident on
  billing-vs-other boundary tickets (0.9–1.0 conf bin: 60% observed acc).

Reproducing the local endpoint (what actually worked on this machine — the
Python `serve.py` needs a CUDA GPU, which this box lacks; llama.cpp CPU does
not):

```bash
cd "/c/Code Main/drex-decision-models"   # sibling clone of nace-ai/drex-decision-models
# weights: weights/drex-v1.5/drex-v1.5-Q8_0.gguf (prebuilt GGUF from
# huggingface.co/nace-ai/drex-v1.5-Q8_0, ~9.5 GB — no conversion needed)
./llama.cpp/build/bin/Release/llama-server.exe -m weights/drex-v1.5/drex-v1.5-Q8_0.gguf \
    --embedding --pooling none -np 2 -c 32768 -b 16384 -ub 2048 --port 8000
# then in drex-evals:
DREX_BASE_URL=http://127.0.0.1:8000 python3 scripts/preflight.py   # must PASS
```

## After that

ROADMAP.md in order: real suites (import from gate-calibrated / laya-* /
German tickets) -> cross-model comparison on real endpoints -> gate
integration with conformal risk control (methodology in gate-calibrated).

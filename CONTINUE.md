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

DONE (2026-11-10, evening): the full phase — calibration metrics, first
real run, real suites, cross-backend table, German suite, BANKING77 sample
(human labels), and the act/ask gate: `drexevals/gate.py` (empirical risk
thresholds) + `scripts/escalation_analysis.py` (per-suite τ* at 5%/2% risk,
results/escalation_policies.json). Offline tests: 10 passed. All reports
committed with hash-verified suites; findings + commands in README.

Next per ROADMAP: live gate integration into an agent tool-approval loop
(needs gate-calibrated decision data — blocked on conversation state), and
scale-up (full BANKING77 ~$0.12, per-language breakdowns, Q4 when feasible).

Hosted runs need DREX_API_KEY (console at drex.nace.ai; ~$0.04/1M input
tokens — a full suite pass costs fractions of a cent). The client retries
429/5xx with a 0/5/20/60s ladder. Rotate any key pasted into chats (the one
used on 2026-11-10 should be rotated).

## Reproducing the local endpoint (this machine)

The Python `serve.py` needs a CUDA GPU, which this box lacks; llama.cpp CPU
does not. ~10 GB RAM for the server — close Firefox/WSL first, or the OS
memory-pressure reaper in Claude Code will kill it mid-run (happened 3x).

```bash
cd "/c/Code Main/drex-decision-models"   # sibling clone of nace-ai/drex-decision-models
# weights: weights/drex-v1.5/drex-v1.5-Q8_0.gguf (prebuilt GGUF from
# huggingface.co/nace-ai/drex-v1.5-Q8_0, ~9.5 GB — no conversion needed)
./llama.cpp/build/bin/Release/llama-server.exe -m weights/drex-v1.5/drex-v1.5-Q8_0.gguf \
    --embedding --pooling none -np 1 -c 4096 -b 4096 -ub 2048 --port 8000
# then in drex-evals:
DREX_BASE_URL=http://127.0.0.1:8000 python3 scripts/preflight.py   # must PASS
DREX_BASE_URL=http://127.0.0.1:8000 python3 scripts/run_suite.py suites/laya_triage_200.json \
    --model "drex-v1.5 Q8_0 (llama.cpp, CPU)" --out results/laya_triage_200.local-q8.report.json
```

## After that

ROADMAP.md in order: real suites (import from gate-calibrated / laya-* /
German tickets) -> cross-model comparison on real endpoints -> gate
integration with conformal risk control (methodology in gate-calibrated).

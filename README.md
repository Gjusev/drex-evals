# drex-evals

Evaluation bridge for [Drex decision models](https://github.com/nace-ai/drex-decision-models)
(arXiv:2611.07854): typed decision questions in, calibrated probabilities out —
scored for accuracy **and** calibration (ECE-style bins).

Built to plug Drex into the decision-model workflow family (routers, triage,
act/ask gates) with runnable suites instead of vibes.

## Status

Plumbing implemented and tested offline (mock client) plus a first real run.
Reports score accuracy **and** calibration per question: Brier score, 10-bin
ECE with per-bin reliability data (`ece_bins`), plus avg confidence and
confidence-on-wrong. Real runs: point `DREX_BASE_URL` at
https://drex.nace.ai (with `DREX_API_KEY`) or a local server from the models
repo (see `docs/MAIN-PC.md`) — committed reports live in `results/`.

### First real run (2026-11-10)

`triage_demo.json` (10 cases) against local drex-v1.5 Q8_0, served by the
nace-ai llama.cpp fork on CPU (Ryzen 5 7600X):

```bash
DREX_BASE_URL=http://127.0.0.1:8000 python3 scripts/run_suite.py suites/triage_demo.json \
    --model "drex-v1.5 Q8_0 (llama.cpp, CPU)" --out results/triage_demo.local-q8.report.json
```

| question | accuracy | avg conf | Brier | ECE | conf-on-wrong |
|---|---|---|---|---|---|
| team | 60% | 0.85 | 0.663 | 0.331 | 0.85 |
| refund | 100% | 0.99 | 0.000 | 0.005 | — (no wrong answers) |
| urgency | 60% | 0.72 | 0.453 | 0.225 | 0.54 |

Refund intent is decisive and calibrated. Team routing is the caution: every
miss is a billing-vs-other boundary ticket answered at 0.81–1.00 confidence —
in the 0.9–1.0 confidence bin, observed accuracy was 0.6 (n=5). n=10, so read
the ECE values as coarse. Full report: `results/triage_demo.local-q8.report.json`.

## Usage

```python
from drexevals import DrexClient, Question, run_suite

client = DrexClient()  # env: DREX_BASE_URL, DREX_API_KEY
cases = [...]  # {state, questions, expected}
print(run_suite(client, cases))
```

```bash
python3 -m pytest tests/   # offline, zero dependencies
```

## Citation

Independent evaluation harness — cite the paper first:
arXiv:2611.07854 (Towards Foundation Decision Models: Drex).

MIT

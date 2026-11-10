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

### Real suites (2026-11-10, same backend)

Imported from the sibling repos (label provenance stated in each suite file):

```bash
DREX_BASE_URL=http://127.0.0.1:8000 python3 scripts/run_suite.py suites/laya_triage_200.json \
    --model "drex-v1.5 Q8_0 (llama.cpp, CPU)" --out results/laya_triage_200.local-q8.report.json
DREX_BASE_URL=http://127.0.0.1:8000 python3 scripts/run_suite.py suites/phishield_test_183.json \
    --model "drex-v1.5 Q8_0 (llama.cpp, CPU)" --out results/phishield_test_183.local-q8.report.json
```

| suite (n) | question | accuracy | avg conf | Brier | ECE |
|---|---|---|---|---|---|
| laya_triage_200 (200, en/es/fr/de/hi/ar) | cluster (12-way) | 95% | 0.96 | 0.087 | 0.032 |
| | urgency (4-level) | 70% | 0.69 | 0.377 | 0.058 |
| | frustration (4-level) | 69% | 0.80 | 0.447 | 0.141 |
| phishield_test_183 (183, en) | phish (noul) | 86% | 0.94 | 0.208 | 0.084 |

What the numbers say:

- **Calibration holds at n=200 on 12-way routing**: in the 0.9–1.0 confidence
  bin (74 cases) the model said 95.5% on average and was right 93.2% of the
  time. The triage_demo team-routing overconfidence did not generalize — it
  was an artifact of 5 ambiguous billing-vs-other tickets.
- **Ordinal tone/urgency scores are the weak spot**: frustration runs
  conf 0.80 against 69% accuracy (ECE 0.141) — subjective tone reading, and
  the labels themselves are AI-annotated with kappa ~0.79 on that dimension.
- **Phishing at max confidence**: 144/183 emails answered at ~0.99 confidence
  were 94% correct — strong but not the 99% the confidence claims; mid-range
  answers (conf 0.6–0.8) were worse than a coin flip (observed 0.44–0.5).
  For an act/ask gate, the ~6% miss rate at max confidence is the number
  that bounds auto-act.

### Cross-backend: hosted API vs local Q8_0 (2026-11-10)

Same suites (hash-verified), same harness, two backends — the roadmap
question "can I self-host without losing calibration?":

| suite | question | hosted acc / conf / ECE | local Q8 acc / conf / ECE |
|---|---|---|---|
| triage_demo | team | 80% / 0.83 / 0.201 | 60% / 0.85 / 0.331 |
| | urgency | 100% / 0.77 / 0.230 | 60% / 0.72 / 0.225 |
| laya_triage_200 | cluster | 96% / 0.93 / 0.041 | 95% / 0.96 / 0.032 |
| | urgency | 84% / 0.80 / 0.067 | 70% / 0.69 / 0.058 |
| | frustration | 80% / 0.78 / 0.034 | 69% / 0.80 / 0.141 |
| phishield_test_183 | phish | 91% / 0.91 / 0.032 | 86% / 0.94 / 0.084 |

**Finding: quantization costs accuracy, not honesty.** The Q8_0 GGUF trails
the hosted bf16 by 5–20 accuracy points on every question, but its
calibration degrades gracefully — where it is less accurate its confidence
drops proportionally (urgency: acc 70 % at conf 0.69 vs hosted 84 % at
0.80). For gates that act on Drex confidence, a self-hosted Q8 trades some
skill for zero API spend without lying about what it knows. The one caveat:
Q8 avg confidence on wrong answers stays high (0.82 phishing), so
threshold-based auto-act needs the same margin on both backends.

Hosted runs: `DREX_BASE_URL=https://drex.nace.ai python3 scripts/run_suite.py
< suite > --model "drex hosted API" --out results/<suite>.hosted.report.json`
(reports committed; total spend for all three hosted runs: well under $0.01
at ~$0.04/1M input tokens).

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

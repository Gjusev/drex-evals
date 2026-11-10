# Roadmap

Current state: eval plumbing done and offline-tested, calibration metrics
(Brier + 10-bin ECE) in place, first real run committed (local drex-v1.5 Q8_0
on `triage_demo.json`, see README + `results/`). Item 1 below is next: more
real runs on bigger suites and more backends.

## Done

- `/v1/systemone` client (hosted + local serve.py), typed questions
  (choice / noul / score)
- `run_suite`: accuracy + confidence calibration (ECE-style bins) per question
- `preflight.py` endpoint check, `triage_demo.json` (10 labeled cases)
- offline mock client so the plumbing is testable without tokens/weights
- calibration metrics: multi-class Brier + 10-bin ECE (with per-bin reliability
  data) per question, in `run_suite`/`compare_backends` output; report envelope
  with suite sha256 / backend kind / model / date; `results/` template for
  committed real-run reports (item 2 tooling done — the measured claim test
  still needs real runs)
- first real run committed (item 1): `triage_demo.json` on local drex-v1.5
  Q8_0 (nace-ai llama.cpp fork, CPU) — refund 100%/Brier .000, team routing
  overconfident on billing-vs-other boundary tickets (0.9–1.0 bin: observed
  accuracy 0.6, n=5). Report: `results/triage_demo.local-q8.report.json`
- client now parses the documented `/v1/systemone` response contract
  (choice/noul/score), locked by an offline test against the docs example
- real suites imported and run (items 2+3): `laya_triage_200` (200
  multilingual tickets incl. 25 German — cluster 95%/ECE .032, urgency 70%,
  frustration 69%/ECE .141) and `phishield_test_183` (86% acc, ECE .084;
  0.99-conf answers 94% correct). Importers committed; reports in results/.
  Calibration claim tested: holds at n=200 on routing, overconfident on
  ordinal tone scores and at phishing max confidence (6% miss at 0.99)
- gate-calibrated import investigated and deferred: 1535 labeled tau-bench
  steps exist (correct vs gold) but rows carry no conversation state — a
  suite would be stateless. Unblock via re-collection or reconstruction
  from its .cache/llm (run_id-keyed)
- cross-backend table done (old items 1+4): all three suites on hosted
  drex.nace.ai vs local Q8_0 (hash-verified same suites). Finding: Q8 costs
  5-20 accuracy points but calibration degrades gracefully — confidence
  drops where accuracy drops. Hosted client got 429/5xx retry with backoff.
  Total hosted spend for all suites: <$0.01
- dedicated German suite + BANKING77 sample + escalation analysis done
  (2026-11-10, hosted): laya_triage_de25 (cluster 100%, Brier .011),
  banking77_cluster_200 (human labels, cluster 84%/ECE .030), and
  drexevals/gate.py + escalation_analysis.py — act/ask thresholds per
  suite/backend at 5%/2% empirical risk budgets (see README table)

## Next (in order)

### 1. Live gate integration
`drexevals/gate.py` + `escalation_analysis.py` deliver the act/ask rule and
calibrated thresholds from measured data. Remaining: wire it into a real
agent tool-approval loop (methodology: gate-calibrated repo, conformal risk
control with held-out calibration). Its tau-bench decision labels exist but
carry no conversation state (see Done note) — new collection or cache
reconstruction unblocks calibrating the gate on agent actions themselves.

### 2. Scale-up
BANKING77 full test split (3,080 human-labeled cases, ~$0.12 hosted) for
tighter ECE; per-language breakdowns (laya_200 covers en/es/fr/de/hi/ar);
a local Q4 build when a prebuilt GGUF appears or RAM allows conversion.

## Non-goals

- No model training or fine-tuning — evaluation bridge only
- No proxy/router layer (laya-router and clef-router already do that role)

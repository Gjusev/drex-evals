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

## Next (in order)

### 1. More real runs: bigger n + more backends
The demo suite is n=10 — too small for stable ECE. Import real suites (item
below) and rerun; then the hosted endpoint and/or another quantization on the
same suite for the cross-backend table.

### 2. Calibration is the headline, not accuracy
Tooling done; first data point in the README. The claim that matters for
gates: "when it says 90%, is it right 90% of the time?" — on this run, team
routing said ~99% and was right 60% of the time (n=5). If quantized local
weights lose calibration vs hosted, that's a publishable finding by itself.

### 3. Real suites
- Import labeled cases from the sibling repos: `gate-calibrated` (tau-bench
  retail act/ask decisions), `laya-phishield` (phishing), `laya-triage`
  (multilingual support tickets)
- German-language suite (the triage demo is English-only; German tickets are
  the real workload)
- Escalation policy cases: given confidence, act or send to human?

### 4. Cross-model comparison table
Same suite, three backends: hosted API, local drex-v1.5 Q8, local Q4 GGUF.
One table: accuracy / ECE / latency per backend. Answers "can I self-host
without losing calibration?"

### 5. Gate integration
Wire the scored confidences into an act/ask gate with conformal risk control
(methodology already exists in `gate-calibrated`) — Drex as the System 1
brain of a tool-approval layer for agents.

## Non-goals

- No model training or fine-tuning — evaluation bridge only
- No proxy/router layer (laya-router and clef-router already do that role)

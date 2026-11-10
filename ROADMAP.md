# Roadmap

Current state: eval plumbing done and offline-tested (mock client), triage
demo suite ready. **No real-model run yet** — the MAIN-PC.md guide covers the
first one. Item 1 below is where the owner continues (main PC).

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

## Next (in order)

### 1. First real run — on the main PC (docs/MAIN-PC.md)
Serve drex-v1.5 locally, `preflight.py`, run `triage_demo.json`, commit the
`.report.json`. Deliverable: first accuracy + calibration numbers in this
README.

### 2. Calibration is the headline, not accuracy
Drex sells calibrated probabilities. Add a calibration plot + Brier score +
ECE to the report, and test the claim that matters for gates: "when it says
90%, is it right 90% of the time?" If quantized local weights lose
calibration vs hosted, that's a publishable finding by itself.

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

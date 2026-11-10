# Run Drex locally on the main PC — step by step

Everything below runs on your main machine. The eval repo itself stays
zero-dependency (Python 3.10+, stdlib only).

## 1. Pick a model

| Model | Size | RAM needed | Notes |
|---|---|---|---|
| **drex-v1.5** | 9B distill | ~12GB RAM (Q8) / ~7GB (Q4) | fastest to start — recommended first |
| drex-v2.0 | 35B MoE (3B active) | ~24GB+ | Q4 GGUF runs on decent machines |
| drex-max-v1 | 27B dense, multimodal | ~24GB+ (Q4 ~17GB) | reads images too, best scores |

Weights (HuggingFace): `nace-ai/drex-v1.5`, `nace-ai/drex-v2.0`,
`nace-ai/drex-max-v1` — plus Q8_0/Q4 GGUF branches for llama.cpp / Ollama.

## 2. Serve it

Option A — their own runtime (recommended, exact /v1/systemone contract):

```bash
git clone https://github.com/nace-ai/drex-decision-models
cd drex-decision-models
pip install -r requirements.txt
huggingface-cli download nace-ai/drex-v1.5 --local-dir weights/drex-v1.5
python3 serve.py --model weights/drex-v1.5 --port 8000
```

Option B — llama.cpp / Ollama with the GGUF (see their README's model table
for the branch name).

## 3. Point the evals at it

```bash
git clone https://github.com/Gjusev/drex-evals
cd drex-evals
export DREX_BASE_URL=http://localhost:8000   # no key needed for local serve.py
python3 scripts/preflight.py                 # must print PASS
```

## 4. Run suites

```bash
python3 scripts/run_suite.py suites/triage_demo.json
# -> prints accuracy + confidence calibration per question, writes .report.json
```

## 5. What to look at in the report

- `accuracy` per question (team / refund / urgency)
- `calibration_bins`: if high-confidence bins show low observed accuracy, the
  model is overconfident — that's the interesting finding for a gate
  (act only when confident) setup
- `confidence_on_wrong`: how often it *believes* itself when it's wrong —
  this is the number that decides if you can auto-act on Drex outputs

## 6. Ideas after the demo suite passes

- Swap in bigger cases: your real triage history, phishing corpus, gate
  decisions (see gate-calibrated's tau-bench retail cases)
- Compare hosted vs local on the same suite (same seed of cases, two
  `DREX_BASE_URL` values) — calibration drift between quantizations is
  worth a README section
- `nace-ai/drex-agent-skill` exists too — same API as a Claude skill

## Optional: hosted quick check (no downloads)

```bash
export DREX_API_KEY=...   # console at drex.nace.ai
python3 scripts/preflight.py   # hits https://drex.nace.ai
```

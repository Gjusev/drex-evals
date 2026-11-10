# drex-evals

Evaluation bridge for [Drex decision models](https://github.com/nace-ai/drex-decision-models)
(arXiv:2611.07854): typed decision questions in, calibrated probabilities out —
scored for accuracy **and** calibration (ECE-style bins).

Built to plug Drex into the decision-model workflow family (routers, triage,
act/ask gates) with runnable suites instead of vibes.

## Status

Plumbing implemented and tested offline (mock client). Real runs: point
`DREX_BASE_URL` at https://drex.nace.ai (with `DREX_API_KEY`) or a local
`serve.py` from the models repo, then run the suites. Weights are open —
drex-v1.5 (9B) runs on Apple silicon; the 35B MoE and Drex Max (27B
multimodal) need more RAM.

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

# results/ — committed evaluation reports

One `.report.json` per real run. A file here is a measurement, not an example:
**only commit reports actually produced by the recorded command** (repo rule:
honest claims, no invented numbers).

## What a report must contain

Written automatically by `scripts/run_suite.py`:

- `meta.suite` + `meta.suite_sha256` — exactly which suite file was run
- `meta.backend_url` / `meta.backend_kind` — endpoint used (`hosted` | `local` | `mock`)
- `meta.model` — weights variant via `--model` (e.g. `drex-v1.5 Q8_0`); may be `null`
  for the hosted endpoint — fill it in if you know it
- `meta.generated` — UTC timestamp; `meta.n_cases`, `meta.drexevals_version`
- `results` — per question: `accuracy`, `avg_confidence`, `confidence_on_correct`,
  `confidence_on_wrong`, `calibration_bins` (5 bins), `brier`, `ece`, `ece_bins`
  (10 bins: `avg_confidence` vs `observed_accuracy` per bin — the reliability data)

## Committing a run

```bash
python3 scripts/preflight.py            # must print PASS first
python3 scripts/run_suite.py suites/triage_demo.json \
    --model "drex-v1.5 Q8_0" \
    --out results/triage_demo.local-q8.report.json
git add results/triage_demo.local-q8.report.json
```

File name: `<suite>.<backend>.report.json`.

Mock runs (`backend_kind: "mock"`) are plumbing checks, not model measurements —
don't commit them here.

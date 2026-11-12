# Verifier evaluation: scifact_dev_150.jsonl

- Model: `gemini-3.5-flash-lite` (calls served by: {'gemini-3.5-flash-lite': 40})
- Examples: 150 · runs: 3 · batch size: 12 · cache off

| Metric | Mean | SD | Runs |
|---|---|---|---|
| Accuracy (4-way) | 78.0% | 0.5% | 78.0%, 78.7%, 77.3% |
| Macro F1 (4-way) | 79.1% | 0.6% | 79.0%, 79.8%, 78.4% |
| Accuracy (partial = supported) | 80.0% | 0.5% | 80.0%, 80.7%, 79.3% |
| Macro F1 (partial = supported) | 80.0% | 0.6% | 80.0%, 80.7%, 79.3% |
| Problem-claim precision | 91.4% | 1.1% | 90.2%, 91.3%, 92.9% |
| Problem-claim recall | 92.3% | 1.2% | 92.0%, 94.0%, 91.0% |
| Problem-claim F1 | 91.9% | 0.6% | 91.1%, 92.6%, 91.9% |
| Rationale hit rate | 92.1% | 1.0% | 93.2%, 90.8%, 92.2% |
| Seconds per run | 161.8 | 51.1 | 203.9, 89.9, 191.5 |
| Gemini calls per run | 13.3 | 0.5 | 13.0, 13.0, 14.0 |

Per-label F1 (mean): supported 80.7%, partially_supported 0.0%, unsupported 78.2%, contradicted 78.3%

Run folders: `data\experiments\verifier_scifact_lite\runs\20261108_164650`, `data\experiments\verifier_scifact_lite\runs\20261108_164839`, `data\experiments\verifier_scifact_lite\runs\20261108_165153`

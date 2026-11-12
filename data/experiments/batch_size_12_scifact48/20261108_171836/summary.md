# Verifier evaluation: scifact_dev_150.jsonl

- Model: `gemini-3.5-flash-lite` (calls served by: {'gemini-3.5-flash-lite': 4})
- Examples: 48 · runs: 1 · batch size: 12 · cache off

| Metric | Mean | SD | Runs |
|---|---|---|---|
| Accuracy (4-way) | 81.2% | 0.0% | 81.2% |
| Macro F1 (4-way) | 82.0% | 0.0% | 82.0% |
| Accuracy (partial = supported) | 83.3% | 0.0% | 83.3% |
| Macro F1 (partial = supported) | 83.6% | 0.0% | 83.6% |
| Problem-claim precision | 97.2% | 0.0% | 97.2% |
| Problem-claim recall | 97.2% | 0.0% | 97.2% |
| Problem-claim F1 | 97.2% | 0.0% | 97.2% |
| Rationale hit rate | 100.0% | 0.0% | 100.0% |
| Seconds per run | 13.2 | 0.0 | 13.2 |
| Gemini calls per run | 4.0 | 0.0 | 4.0 |

Per-label F1 (mean): supported 87.0%, partially_supported 0.0%, unsupported 85.7%, contradicted 73.3%

Run folders: `data\experiments\batch_size_12_scifact48\runs\20261108_171836`

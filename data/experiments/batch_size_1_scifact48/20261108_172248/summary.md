# Verifier evaluation: scifact_dev_150.jsonl

- Model: `gemini-3.5-flash-lite` (calls served by: {'gemini-3.5-flash-lite': 48})
- Examples: 48 · runs: 1 · batch size: 1 · cache off

| Metric | Mean | SD | Runs |
|---|---|---|---|
| Accuracy (4-way) | 79.2% | 0.0% | 79.2% |
| Macro F1 (4-way) | 79.7% | 0.0% | 79.7% |
| Accuracy (partial = supported) | 81.2% | 0.0% | 81.2% |
| Macro F1 (partial = supported) | 80.3% | 0.0% | 80.3% |
| Problem-claim precision | 92.1% | 0.0% | 92.1% |
| Problem-claim recall | 97.2% | 0.0% | 97.2% |
| Problem-claim F1 | 94.6% | 0.0% | 94.6% |
| Rationale hit rate | 100.0% | 0.0% | 100.0% |
| Seconds per run | 250.9 | 0.0 | 250.9 |
| Gemini calls per run | 48.0 | 0.0 | 48.0 |

Per-label F1 (mean): supported 80.0%, partially_supported 0.0%, unsupported 85.1%, contradicted 74.1%

Run folders: `data\experiments\batch_size_1_scifact48\runs\20261108_172248`

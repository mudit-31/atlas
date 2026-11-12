# Verifier evaluation: scifact_dev_150.jsonl

- Model: `gemini-3.5-flash-lite` (calls served by: {'gemini-3.5-flash-lite': 40})
- Examples: 150 · runs: 3 · batch size: 12 · cache off

| Metric | Mean | SD | Runs |
|---|---|---|---|
| Accuracy (4-way) | 82.0% | 0.5% | 81.3%, 82.7%, 82.0% |
| Macro F1 (4-way) | 83.2% | 0.6% | 82.4%, 83.8%, 83.4% |
| Accuracy (partial = supported) | 84.2% | 0.6% | 83.3%, 84.7%, 84.7% |
| Macro F1 (partial = supported) | 84.2% | 0.6% | 83.3%, 84.7%, 84.5% |
| Problem-claim precision | 95.6% | 0.9% | 94.9%, 95.0%, 96.9% |
| Problem-claim recall | 93.3% | 0.5% | 93.0%, 94.0%, 93.0% |
| Problem-claim F1 | 94.4% | 0.4% | 93.9%, 94.5%, 94.9% |
| Rationale hit rate | 92.2% | 1.1% | 93.8%, 91.4%, 91.4% |
| Seconds per run | 109.9 | 53.6 | 69.5, 185.6, 74.5 |
| Gemini calls per run | 13.3 | 0.5 | 13.0, 14.0, 13.0 |

Per-label F1 (mean): supported 86.4%, partially_supported 0.0%, unsupported 81.9%, contradicted 81.3%

Run folders: `data\experiments\verifier_scifact_lite_defended\runs\20261108_170937`, `data\experiments\verifier_scifact_lite_defended\runs\20261108_171312`, `data\experiments\verifier_scifact_lite_defended\runs\20261108_171428`

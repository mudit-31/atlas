# Verifier evaluation: atlas_seed_v1.jsonl

- Model: `gemini-3.5-flash-lite` (calls served by: {'gemini-3.5-flash-lite': 4})
- Examples: 40 · runs: 1 · batch size: 12 · cache off

| Metric | Mean | SD | Runs |
|---|---|---|---|
| Accuracy (4-way) | 97.5% | 0.0% | 97.5% |
| Macro F1 (4-way) | 97.5% | 0.0% | 97.5% |
| Accuracy (partial = supported) | 75.0% | 0.0% | 75.0% |
| Macro F1 (partial = supported) | 66.0% | 0.0% | 66.0% |
| Problem-claim precision | 95.2% | 0.0% | 95.2% |
| Problem-claim recall | 100.0% | 0.0% | 100.0% |
| Problem-claim F1 | 97.6% | 0.0% | 97.6% |
| Seconds per run | 10.7 | 0.0 | 10.7 |
| Gemini calls per run | 4.0 | 0.0 | 4.0 |

Per-label F1 (mean): supported 100.0%, partially_supported 94.7%, unsupported 100.0%, contradicted 95.2%

Run folders: `data\experiments\verifier_seed_lite_defended\runs\20261108_170949`

# ATLAS Verifier Evaluation

- Dataset: `data\benchmark\atlas_seed_v1.jsonl` (40 examples)
- Model: `gemini-3.5-flash-lite` · batch size 12
- Gemini calls: 4 · time 10.69s

## Headline

| Accuracy | Macro F1 | Weighted F1 | Problem-claim precision | Problem-claim recall |
|---|---|---|---|---|
| 0.975 | 0.975 | 0.975 | 0.952 | 1.000 |

Problem claims = unsupported + contradicted, i.e. what ATLAS should flag.

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Supported | 1.000 | 1.000 | 1.000 | 10 |
| Partially Supported | 1.000 | 0.900 | 0.947 | 10 |
| Unsupported | 1.000 | 1.000 | 1.000 | 10 |
| Contradicted | 0.909 | 1.000 | 0.952 | 10 |

## Confusion matrix (rows = gold, columns = predicted)

| | Supported | Partially Supported | Unsupported | Contradicted |
|---|---|---|---|---|
| **Supported** | 10 | 0 | 0 | 0 |
| **Partially Supported** | 0 | 9 | 0 | 1 |
| **Unsupported** | 0 | 0 | 10 | 0 |
| **Contradicted** | 0 | 0 | 0 | 10 |

## Confidence

- Mean confidence when correct: 0.97; when wrong: 1.00
- Accuracy when confidence ≥ 0.8: 0.975 (100% of examples)

## Mistakes

| Id | Gold | Predicted | Claim | Rationale |
|---|---|---|---|---|
| p02 | partially_supported | contradicted | Kestrel Robotics was founded in Lisbon and is still headquartered there. | No evidence supports that it is still headquartered in Lisbon, and other passages indicate it moved to Berlin. |

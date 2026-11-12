# ATLAS Verifier Evaluation

- Dataset: `data\external\scifact_dev_150.jsonl` (48 examples)
- Model: `gemini-3.5-flash-lite` · batch size 1
- Gemini calls: 48 · time 250.86s

## Headline

| Accuracy | Macro F1 | Weighted F1 | Problem-claim precision | Problem-claim recall |
|---|---|---|---|---|
| 0.792 | 0.797 | 0.804 | 0.921 | 0.972 |

Problem claims = unsupported + contradicted, i.e. what ATLAS should flag.

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Supported | 1.000 | 0.667 | 0.800 | 12 |
| Partially Supported | 0.000 | 0.000 | 0.000 | 0 |
| Unsupported | 0.769 | 0.952 | 0.851 | 21 |
| Contradicted | 0.833 | 0.667 | 0.741 | 15 |

## Confusion matrix (rows = gold, columns = predicted)

| | Supported | Partially Supported | Unsupported | Contradicted |
|---|---|---|---|---|
| **Supported** | 8 | 1 | 2 | 1 |
| **Partially Supported** | 0 | 0 | 0 | 0 |
| **Unsupported** | 0 | 0 | 20 | 1 |
| **Contradicted** | 0 | 1 | 4 | 10 |

## Confidence

- Mean confidence when correct: 1.00; when wrong: 0.98
- Accuracy when confidence ≥ 0.8: 0.792 (100% of examples)

## Mistakes

| Id | Gold | Predicted | Claim | Rationale |
|---|---|---|---|---|
| scifact-1221 | contradicted | unsupported | The genomic aberrations found in matasteses are very similar to those found in the primary tumor. | The evidence passages do not discuss whether genomic aberrations in metastases are very similar to those in the primary tumor. |
| scifact-1163 | supported | unsupported | The DdrB protein from Deinococcus radiodurans is an alternative SSB. | The evidence describes DdrB as a single-stranded DNA binding protein, but explicitly notes that its structure is 'topologically distinct from all other single-stranded binding (SSB) proteins', not confirming it as an 'alternative SSB'. |
| scifact-208 | supported | contradicted | CHEK2 is not associated with breast cancer. | The evidence explicitly states that 'Previous investigation has established a role for the CHEK2 gene in breast cancer aetiology', which contradicts the claim that it is not associated with breast cancer. |
| scifact-48 | contradicted | unsupported | A total of 1,000 people in the UK are asymptomatic carriers of vCJD infection. | The evidence does not state that 1,000 people in the UK are asymptomatic carriers. |
| scifact-783 | unsupported | contradicted | Mice without IFN-γ or its receptor are resistant to EAM induced with α-MyHC/CFA. | The evidence states that 'IFN-gamma-deficient mice developed fatal autoimmune disease', which contradicts the claim that mice without IFN-y are resistant to EAM. |
| scifact-1110 | contradicted | unsupported | Suboptimal nutrition is not predictive of chronic disease | None of the provided evidence passages address whether suboptimal nutrition is predictive of chronic disease. |
| scifact-728 | contradicted | unsupported | Ly6C hi monocytes have a lower inflammatory capacity than Ly6C lo monocytes. | None of the provided evidence passages discuss the relative inflammatory capacity of Ly6C hi versus Ly6C lo monocytes. |
| scifact-879 | contradicted | partially_supported | Occupancy of ribosomes by IncRNAs do not make functional peptides. | The evidence shows that lincRNAs are bound by ribosomes but do not function through encoded proteins, though it does not explicitly use the exact phrase 'make functional peptides'. |
| scifact-960 | supported | partially_supported | Polymeal nutrition reduces cardiovascular mortality. | The evidence states the Polymeal reduces cardiovascular disease events and morbidity, but does not explicitly mention mortality. |
| scifact-1368 | supported | unsupported | Vitamin D deficiency effects the term of delivery. | The provided evidence does not mention the effect of vitamin D deficiency on the term of delivery. |

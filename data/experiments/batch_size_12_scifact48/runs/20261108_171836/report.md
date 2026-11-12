# ATLAS Verifier Evaluation

- Dataset: `data\external\scifact_dev_150.jsonl` (48 examples)
- Model: `gemini-3.5-flash-lite` · batch size 12
- Gemini calls: 4 · time 13.15s

## Headline

| Accuracy | Macro F1 | Weighted F1 | Problem-claim precision | Problem-claim recall |
|---|---|---|---|---|
| 0.812 | 0.820 | 0.822 | 0.972 | 0.972 |

Problem claims = unsupported + contradicted, i.e. what ATLAS should flag.

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Supported | 0.909 | 0.833 | 0.870 | 12 |
| Partially Supported | 0.000 | 0.000 | 0.000 | 0 |
| Unsupported | 0.857 | 0.857 | 0.857 | 21 |
| Contradicted | 0.733 | 0.733 | 0.733 | 15 |

## Confusion matrix (rows = gold, columns = predicted)

| | Supported | Partially Supported | Unsupported | Contradicted |
|---|---|---|---|---|
| **Supported** | 10 | 1 | 0 | 1 |
| **Partially Supported** | 0 | 0 | 0 | 0 |
| **Unsupported** | 0 | 0 | 18 | 3 |
| **Contradicted** | 1 | 0 | 3 | 11 |

## Confidence

- Mean confidence when correct: 0.72; when wrong: 0.76
- Accuracy when confidence ≥ 0.8: 0.800 (73% of examples)

## Mistakes

| Id | Gold | Predicted | Claim | Rationale |
|---|---|---|---|---|
| scifact-1221 | contradicted | unsupported | The genomic aberrations found in matasteses are very similar to those found in the primary tumor. | The evidence passages do not discuss whether genomic aberrations in metastases are similar to those in the primary tumor. |
| scifact-208 | supported | contradicted | CHEK2 is not associated with breast cancer. | The evidence states that 'Previous investigation has established a role for the CHEK2 gene in breast cancer aetiology', directly contradicting the claim. |
| scifact-48 | contradicted | unsupported | A total of 1,000 people in the UK are asymptomatic carriers of vCJD infection. | The evidence reports a prevalence of 493 per million from appendix samples, but does not state a total of 1,000 people. |
| scifact-783 | unsupported | contradicted | Mice without IFN-γ or its receptor are resistant to EAM induced with α-MyHC/CFA. | The evidence states that 'IFN-gamma-deficient mice developed fatal autoimmune disease', which contradicts the claim that they are resistant. |
| scifact-728 | contradicted | unsupported | Ly6C hi monocytes have a lower inflammatory capacity than Ly6C lo monocytes. | The evidence identifies monocyte subsets and their recruitment capacity, but does not compare the inflammatory capacity of Ly6C hi versus Ly6C lo monocytes. |
| scifact-410 | unsupported | contradicted | Febrile seizures increase the threshold for development of epilepsy. | The evidence states that hyperthermia-induced seizures cause a selective presynaptic increase in inhibitory synaptic transmission, which does not support the claim of increasing the threshold for epilepsy (and instead suggests enhanced alterations). |
| scifact-879 | contradicted | supported | Occupancy of ribosomes by IncRNAs do not make functional peptides. | The evidence explicitly argues 'that the large majority of lincRNAs do not function through encoded proteins'. |
| scifact-269 | unsupported | contradicted | Cold exposure reduces BAT recruitment. | The evidence mentions 'cold-induced atherosclerotic lesions' and thermogenesis in brown adipose tissue rather than cold exposure reducing BAT recruitment. |
| scifact-1368 | supported | partially_supported | Vitamin D deficiency effects the term of delivery. | The evidence links vitamin D levels to pregnancy outcomes such as small for gestational age infants and birth weight, but the broad claim about 'term of delivery' is only partially addressed. |

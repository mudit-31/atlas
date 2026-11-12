# ATLAS Verifier Evaluation

- Dataset: `data\external\scifact_dev_150.jsonl` (150 examples)
- Model: `gemini-3.5-flash-lite` · batch size 12
- Gemini calls: 13 · time 69.49s

## Headline

| Accuracy | Macro F1 | Weighted F1 | Problem-claim precision | Problem-claim recall |
|---|---|---|---|---|
| 0.813 | 0.824 | 0.824 | 0.949 | 0.930 |

Problem claims = unsupported + contradicted, i.e. what ATLAS should flag.

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Supported | 0.875 | 0.840 | 0.857 | 50 |
| Partially Supported | 0.000 | 0.000 | 0.000 | 0 |
| Unsupported | 0.792 | 0.840 | 0.816 | 50 |
| Contradicted | 0.844 | 0.760 | 0.800 | 50 |

## Confusion matrix (rows = gold, columns = predicted)

| | Supported | Partially Supported | Unsupported | Contradicted |
|---|---|---|---|---|
| **Supported** | 42 | 3 | 2 | 3 |
| **Partially Supported** | 0 | 0 | 0 | 0 |
| **Unsupported** | 4 | 0 | 42 | 4 |
| **Contradicted** | 2 | 1 | 9 | 38 |

## Confidence

- Mean confidence when correct: 0.90; when wrong: 0.90
- Accuracy when confidence ≥ 0.8: 0.809 (91% of examples)

## Mistakes

| Id | Gold | Predicted | Claim | Rationale |
|---|---|---|---|---|
| scifact-1221 | contradicted | unsupported | The genomic aberrations found in matasteses are very similar to those found in the primary tumor. | None of the provided evidence passages discuss the similarity of genomic aberrations between metastases and primary tumors. |
| scifact-208 | supported | contradicted | CHEK2 is not associated with breast cancer. | The evidence states that 'Previous investigation has established a role for the CHEK2 gene in breast cancer aetiology', contradicting the claim that it is not associated. |
| scifact-48 | contradicted | unsupported | A total of 1,000 people in the UK are asymptomatic carriers of vCJD infection. | The evidence reports a prevalence of 493 per million from 32,441 appendix samples, but does not state a total of 1,000 asymptomatic carriers in the UK. |
| scifact-783 | unsupported | contradicted | Mice without IFN-γ or its receptor are resistant to EAM induced with α-MyHC/CFA. | The evidence states that 'IFN-gamma-deficient mice developed fatal autoimmune disease', which contradicts that they are resistant to EAM. |
| scifact-728 | contradicted | unsupported | Ly6C hi monocytes have a lower inflammatory capacity than Ly6C lo monocytes. | The evidence distinguishes mouse monocyte subsets based on Ly-6C expression and recruitment, but does not compare their inflammatory capacities to state that Ly6C hi have lower capacity. |
| scifact-410 | unsupported | contradicted | Febrile seizures increase the threshold for development of epilepsy. | The evidence notes that febrile seizures cause a 'presynaptic increase in inhibitory synaptic transmission in the hippocampus', rather than increasing the threshold for epilepsy. |
| scifact-879 | contradicted | supported | Occupancy of ribosomes by IncRNAs do not make functional peptides. | The evidence states that 'the large majority of lincRNAs do not function through encoded proteins'. |
| scifact-269 | unsupported | contradicted | Cold exposure reduces BAT recruitment. | The evidence discusses UCP1 in brown adipose tissue (BAT) and cold-induced effects, but cold exposure stimulates/activates rather than reduces BAT recruitment/thermogenesis. |
| scifact-1368 | supported | partially_supported | Vitamin D deficiency effects the term of delivery. | The evidence shows vitamin D levels affect pregnancy outcomes and birth variables, but does not specifically confirm an effect on the exact 'term of delivery'. |
| scifact-693 | supported | partially_supported | Leuko-reduced blood reduces infectious complications in red blood cell transfusion. | The evidence notes decreased mortality, fever episodes, and antibiotic use, but states that serious nosocomial infections did not decrease. |
| scifact-956 | unsupported | supported | Pleiotropic coupling of GLP-1R to intracellular effectors promotes distinct profiles of cellular signaling. | The evidence states that 'peptide agonists can engage different elements of the receptor extracellular face to achieve effector coupling and biased signaling'. |
| scifact-1021 | contradicted | unsupported | Rapid up-regulation and higher basal expression of interferon-induced genes reduce survival of granule cell neurons that are infected by West Nile virus. | The text discusses differential permissivity and innate immune programs, but does not state that these factors reduce survival of granule cell neurons infected by West Nile virus. |
| scifact-1303 | contradicted | unsupported | Tirasemtiv has no effect on fast-twitch muscle. | The provided evidence passages do not mention or discuss tirasemtiv. |
| scifact-718 | contradicted | unsupported | Low nucleosome occupancy correlates with low methylation levels across species. | The evidence does not compare methylation levels across species in relation to nucleosome occupancy levels. |
| scifact-115 | contradicted | unsupported | Anthrax spores can be disposed of easily after they are dispersed. | The provided evidence discusses anthrax spore contamination and reaerosolization under various conditions, but does not state that spores can be disposed of easily. |
| scifact-514 | unsupported | supported | High dietary calcium intakes are unnecessary for prevention of secondary hyperparathyroidism in subjects with 25(OH)D levels above 75 nmol/liter. | Evidence 9 states: "As long as vitamin D status is ensured, calcium intake levels of more than 800 mg/d may be unnecessary for maintaining calcium metabolism." |
| scifact-57 | contradicted | partially_supported | APOE4 expression in iPSC-derived neurons increases AlphaBeta production and tau phosphorylation, delaying GABA neuron degeneration. | Evidence 2 supports that ApoE4 increases tau phosphorylation and Aβ production and leads to GABAergic neuron degeneration, but it states the neurons display degeneration rather than a delay in it. |
| scifact-1385 | supported | contradicted | cSMAC formation enhances weak ligand signalling. | The evidence states that "enhancing cSMAC formation reduced stimulatory capacity of the weak peptide," which contradicts the claim that it enhances it. |
| scifact-1020 | supported | unsupported | Rapid up-regulation and higher basal expression of interferon-induced genes increase survival of granule cell neurons that are infected by West Nile virus. | The evidence mentions innate immune programs and ISGs providing antiviral effects, but does not state that they increase survival of granule cell neurons specifically infected by West Nile virus. |
| scifact-852 | contradicted | unsupported | Non-invasive ventilation use should be decreased if there is inadequate response to conventional treatment. | The provided text discusses the cost-effectiveness and mortality outcomes of non-invasive ventilation, but does not state that its use should be decreased upon inadequate response. |
| scifact-1041 | contradicted | unsupported | Replacement of histone H2A with H2A.Z slows gene activation in yeasts by stabilizing +1 nucleosomes. | The provided evidence passages discuss H3.3 and H2A.Z nucleosome stability in vertebrates, but do not mention gene activation or slowing gene activation in yeasts. |
| scifact-1335 | supported | unsupported | UCB T cells maintain high TCR diversity after transplantation. | The evidence states that cord blood-graft recipients approximated healthy TCR diversity, but does not state that UCB T cells maintain high TCR diversity after transplantation. |
| scifact-238 | unsupported | supported | Cells undergoing methionine restriction may activate miRNAs. | The evidence states that miRNAs are instrumental in stress responses and 'may become activators of expression during stress'. |
| scifact-183 | contradicted | supported | Bone marrow cells contribute to adult macrophage compartments. | The evidence demonstrates that host/bone marrow-derived macrophages contribute and expand following transplantation. |
| scifact-1389 | supported | contradicted | mTORC2 regulates intracellular cysteine levels through xCT inhibition. | The evidence shows that mTORC2 inhibits xCT via phosphorylation, rather than regulating intracellular cysteine levels through xCT inhibition. |
| scifact-870 | unsupported | supported | Obesity decreases life quality. | The evidence notes that higher BMI reduces median survival by several years, supporting the claim that obesity negatively impacts life quality/duration. |
| scifact-354 | unsupported | contradicted | Downregulation and mislocalization of Scribble prevents cell transformation and mammary tumorigenesis. | The evidence states that depletion or loss of Scribble induces dysplasia, promotes tumorigenesis, and inhibits breast cancer formation, which contradicts the claim that it prevents cell transformation. |
| scifact-436 | supported | partially_supported | Free histones are degraded by a Rad53-dependent mechanism once DNA has been replicated. | The evidence confirms that excess histones are degraded in a Rad53-dependent manner, but specifies it occurs when DNA replication slows down or stops, rather than once DNA has been replicated. |

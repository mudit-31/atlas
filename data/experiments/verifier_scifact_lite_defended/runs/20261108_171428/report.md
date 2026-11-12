# ATLAS Verifier Evaluation

- Dataset: `data\external\scifact_dev_150.jsonl` (150 examples)
- Model: `gemini-3.5-flash-lite` · batch size 12
- Gemini calls: 13 · time 74.54s

## Headline

| Accuracy | Macro F1 | Weighted F1 | Problem-claim precision | Problem-claim recall |
|---|---|---|---|---|
| 0.820 | 0.834 | 0.834 | 0.969 | 0.930 |

Problem claims = unsupported + contradicted, i.e. what ATLAS should flag.

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Supported | 0.878 | 0.860 | 0.869 | 50 |
| Partially Supported | 0.000 | 0.000 | 0.000 | 0 |
| Unsupported | 0.808 | 0.840 | 0.824 | 50 |
| Contradicted | 0.864 | 0.760 | 0.808 | 50 |

## Confusion matrix (rows = gold, columns = predicted)

| | Supported | Partially Supported | Unsupported | Contradicted |
|---|---|---|---|---|
| **Supported** | 43 | 4 | 1 | 2 |
| **Partially Supported** | 0 | 0 | 0 | 0 |
| **Unsupported** | 4 | 0 | 42 | 4 |
| **Contradicted** | 2 | 1 | 9 | 38 |

## Confidence

- Mean confidence when correct: 0.90; when wrong: 0.90
- Accuracy when confidence ≥ 0.8: 0.816 (91% of examples)

## Mistakes

| Id | Gold | Predicted | Claim | Rationale |
|---|---|---|---|---|
| scifact-1221 | contradicted | unsupported | The genomic aberrations found in matasteses are very similar to those found in the primary tumor. | The evidence does not discuss the similarity of genomic aberrations between metastases and primary tumors. |
| scifact-208 | supported | contradicted | CHEK2 is not associated with breast cancer. | The evidence explicitly states that "Previous investigation has established a role for the CHEK2 gene in breast cancer aetiology," which contradicts the claim that it is not associated with breast cancer. |
| scifact-48 | contradicted | unsupported | A total of 1,000 people in the UK are asymptomatic carriers of vCJD infection. | The evidence reports a prevalence of 493 per million population based on 16 positive appendix samples out of 32,441, but does not state a total of 1,000 people in the UK are carriers. |
| scifact-783 | unsupported | contradicted | Mice without IFN-γ or its receptor are resistant to EAM induced with α-MyHC/CFA. | The evidence states that IFN-gamma-deficient mice developed fatal autoimmune disease rather than being resistant to it. |
| scifact-728 | contradicted | unsupported | Ly6C hi monocytes have a lower inflammatory capacity than Ly6C lo monocytes. | The provided passages do not compare the inflammatory capacities of Ly6C hi versus Ly6C lo monocytes. |
| scifact-879 | contradicted | supported | Occupancy of ribosomes by IncRNAs do not make functional peptides. | The evidence argues 'that the large majority of lincRNAs do not function through encoded proteins'. |
| scifact-269 | unsupported | contradicted | Cold exposure reduces BAT recruitment. | The evidence states that UCP1 in brown adipose tissue (BAT) is involved in thermogenesis and cold-induced effects, rather than cold exposure reducing BAT recruitment. |
| scifact-1368 | supported | partially_supported | Vitamin D deficiency effects the term of delivery. | The evidence shows vitamin D insufficiency affects various birth outcomes and gestational issues, but the broad claim about 'the term of delivery' is only partially addressed via specific variables like small for gestational age. |
| scifact-693 | supported | partially_supported | Leuko-reduced blood reduces infectious complications in red blood cell transfusion. | The evidence shows decreased mortality, fever, and antibiotic use, but notes that serious nosocomial infections did not decrease. |
| scifact-956 | unsupported | supported | Pleiotropic coupling of GLP-1R to intracellular effectors promotes distinct profiles of cellular signaling. | The evidence states that "peptide agonists can engage different elements of the receptor extracellular face to achieve effector coupling and biased signaling". |
| scifact-1021 | contradicted | unsupported | Rapid up-regulation and higher basal expression of interferon-induced genes reduce survival of granule cell neurons that are infected by West Nile virus. | The passages do not mention neuron survival or West Nile virus in relation to rapid up-regulation of interferon-induced genes. |
| scifact-1303 | contradicted | unsupported | Tirasemtiv has no effect on fast-twitch muscle. | The provided evidence discusses CK-2017357, not Tirasemtiv, and does not address whether it has an effect on fast-twitch muscle. |
| scifact-718 | contradicted | unsupported | Low nucleosome occupancy correlates with low methylation levels across species. | The evidence discusses clustered methylation in nucleosome linkers and dense methylation, but does not provide a correlation between low nucleosome occupancy and low methylation levels across species. |
| scifact-115 | contradicted | unsupported | Anthrax spores can be disposed of easily after they are dispersed. | The evidence does not mention the disposal of anthrax spores after dispersion. |
| scifact-514 | unsupported | supported | High dietary calcium intakes are unnecessary for prevention of secondary hyperparathyroidism in subjects with 25(OH)D levels above 75 nmol/liter. | The evidence concludes that 'As long as vitamin D status is ensured, calcium intake levels of more than 800 mg/d may be unnecessary'. |
| scifact-57 | contradicted | partially_supported | APOE4 expression in iPSC-derived neurons increases AlphaBeta production and tau phosphorylation, delaying GABA neuron degeneration. | While the evidence confirms increased Aβ production and tau phosphorylation, it states they 'displayed GABAergic neuron degeneration' rather than delaying it. |
| scifact-1385 | supported | contradicted | cSMAC formation enhances weak ligand signalling. | The evidence states that enhancing cSMAC formation reduced stimulatory capacity of the weak peptide, rather than enhancing weak ligand signalling. |
| scifact-1274 | supported | partially_supported | The tip of the inner tube of the toxic type VI secretion system (T6SS) antibacterial effector in Escherichia coli (E. coli) carries toxic effector proteins. | The evidence discusses spikes and effector proteins in the T6SS, but does not explicitly mention Escherichia coli (E. coli). |
| scifact-1020 | supported | unsupported | Rapid up-regulation and higher basal expression of interferon-induced genes increase survival of granule cell neurons that are infected by West Nile virus. | The evidence discusses interferon-stimulated genes and antiviral effects against neurotropic viruses, but does not mention West Nile virus or increased neuronal survival. |
| scifact-852 | contradicted | unsupported | Non-invasive ventilation use should be decreased if there is inadequate response to conventional treatment. | The provided evidence discusses cost-effectiveness and mortality reduction of non-invasive ventilation, but does not address decreasing its use due to inadequate response. |
| scifact-1041 | contradicted | unsupported | Replacement of histone H2A with H2A.Z slows gene activation in yeasts by stabilizing +1 nucleosomes. | None of the evidence passages discuss H2A.Z slowing gene activation in yeasts or stabilizing +1 nucleosomes. |
| scifact-238 | unsupported | supported | Cells undergoing methionine restriction may activate miRNAs. | The evidence states that 'miRNAs... may become activators of expression during stress.' |
| scifact-183 | contradicted | supported | Bone marrow cells contribute to adult macrophage compartments. | The evidence shows that bone marrow (via transplantation) contributes to host/adult macrophage compartments. |
| scifact-213 | unsupported | contradicted | CRP is not predictive of postoperative mortality following Coronary Artery Bypass Graft (CABG) surgery. | The evidence contradicts the claim by considering CRP for prognostic prioritisation strategies, treating it as having prognostic information. |
| scifact-870 | unsupported | supported | Obesity decreases life quality. | The evidence states that higher BMI ranges reduce median survival by several years, supporting decreased life quality/outcomes. |
| scifact-354 | unsupported | contradicted | Downregulation and mislocalization of Scribble prevents cell transformation and mammary tumorigenesis. | The evidence states that depletion or loss of Scribble "induces dysplasia in vivo that progress to tumors" and that "scribble inhibits breast cancer formation," meaning its downregulation promotes rather than prevents tumorigenesis. |
| scifact-436 | supported | partially_supported | Free histones are degraded by a Rad53-dependent mechanism once DNA has been replicated. | The evidence confirms excess histones are degraded in a Rad53-dependent manner, but specifies when DNA replication slows down or stops rather than once it has been replicated. |

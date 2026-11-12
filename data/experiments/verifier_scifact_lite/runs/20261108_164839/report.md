# ATLAS Verifier Evaluation

- Dataset: `data\external\scifact_dev_150.jsonl` (150 examples)
- Model: `gemini-3.5-flash-lite` · batch size 12
- Gemini calls: 13 · time 89.86s

## Headline

| Accuracy | Macro F1 | Weighted F1 | Problem-claim precision | Problem-claim recall |
|---|---|---|---|---|
| 0.787 | 0.798 | 0.798 | 0.913 | 0.940 |

Problem claims = unsupported + contradicted, i.e. what ATLAS should flag.

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Supported | 0.884 | 0.760 | 0.817 | 50 |
| Partially Supported | 0.000 | 0.000 | 0.000 | 0 |
| Unsupported | 0.737 | 0.840 | 0.785 | 50 |
| Contradicted | 0.826 | 0.760 | 0.792 | 50 |

## Confusion matrix (rows = gold, columns = predicted)

| | Supported | Partially Supported | Unsupported | Contradicted |
|---|---|---|---|---|
| **Supported** | 38 | 3 | 5 | 4 |
| **Partially Supported** | 0 | 0 | 0 | 0 |
| **Unsupported** | 4 | 0 | 42 | 4 |
| **Contradicted** | 1 | 1 | 10 | 38 |

## Confidence

- Mean confidence when correct: 0.98; when wrong: 0.95
- Accuracy when confidence ≥ 0.8: 0.789 (98% of examples)

## Mistakes

| Id | Gold | Predicted | Claim | Rationale |
|---|---|---|---|---|
| scifact-1221 | contradicted | unsupported | The genomic aberrations found in matasteses are very similar to those found in the primary tumor. | None of the cited evidence passages are provided or discuss the genomic aberrations of metastases compared to primary tumors. |
| scifact-1163 | supported | contradicted | The DdrB protein from Deinococcus radiodurans is an alternative SSB. | Evidence states that DdrB 'comprises a novel fold that is structurally and topologically distinct from all other single-stranded binding (SSB) proteins characterized to date'. |
| scifact-208 | supported | contradicted | CHEK2 is not associated with breast cancer. | Evidence E16-2 states that previous investigation has established a role for the CHEK2 gene in breast cancer aetiology, which contradicts the claim that it is not associated. |
| scifact-48 | contradicted | unsupported | A total of 1,000 people in the UK are asymptomatic carriers of vCJD infection. | The evidence reports a prevalence of 493 per million based on 16 positive samples out of 32,441, but does not state a total of 1,000 people. |
| scifact-783 | unsupported | contradicted | Mice without IFN-γ or its receptor are resistant to EAM induced with α-MyHC/CFA. | The evidence states that 'IFN-gamma-deficient mice developed fatal autoimmune disease', which contradicts the claim that they are resistant to EAM. |
| scifact-728 | contradicted | unsupported | Ly6C hi monocytes have a lower inflammatory capacity than Ly6C lo monocytes. | The provided passages do not compare the inflammatory capacities of Ly6C hi versus Ly6C lo monocytes. |
| scifact-410 | unsupported | contradicted | Febrile seizures increase the threshold for development of epilepsy. | The evidence indicates that febrile seizures cause persistent alterations and increase inhibitory synaptic transmission, opposing the idea of increasing a threshold to prevent epilepsy development. |
| scifact-879 | contradicted | supported | Occupancy of ribosomes by IncRNAs do not make functional peptides. | Evidence E38-7 states that results argue the large majority of lincRNAs do not function through encoded proteins. |
| scifact-960 | supported | partially_supported | Polymeal nutrition reduces cardiovascular mortality. | Evidence states the Polymeal reduces cardiovascular disease events and morbidity, but does not explicitly mention mortality. |
| scifact-269 | unsupported | contradicted | Cold exposure reduces BAT recruitment. | The evidence refers to UCP1 in brown adipose tissue (BAT) and cold-induced effects, but does not state that cold exposure reduces BAT recruitment; rather, deletion of UCP1 protects against cold-induced lesions. |
| scifact-1368 | supported | unsupported | Vitamin D deficiency effects the term of delivery. | Evidence links vitamin D to birth weight and conditions like gestational diabetes, but does not directly address the 'term of delivery'. |
| scifact-693 | supported | partially_supported | Leuko-reduced blood reduces infectious complications in red blood cell transfusion. | Evidence confirms decreased mortality, fever episodes, and antibiotic use, but states that serious nosocomial infections did not decrease. |
| scifact-956 | unsupported | supported | Pleiotropic coupling of GLP-1R to intracellular effectors promotes distinct profiles of cellular signaling. | Evidence states that peptide agonists can engage different elements of the receptor to achieve effector coupling and biased signaling. |
| scifact-1021 | contradicted | unsupported | Rapid up-regulation and higher basal expression of interferon-induced genes reduce survival of granule cell neurons that are infected by West Nile virus. | The evidence discusses antiviral effects and innate immune programs, but does not state that these factors reduce survival of granule cell neurons infected by West Nile virus. |
| scifact-1303 | contradicted | unsupported | Tirasemtiv has no effect on fast-twitch muscle. | None of the provided evidence mentions Tirasemtiv or its effect on fast-twitch muscle. |
| scifact-718 | contradicted | unsupported | Low nucleosome occupancy correlates with low methylation levels across species. | The evidence discusses clustered methylation in nucleosome linkers and dense methylation, but does not claim a correlation between low nucleosome occupancy and low methylation levels across species. |
| scifact-115 | contradicted | unsupported | Anthrax spores can be disposed of easily after they are dispersed. | The evidence does not address the ease of disposing of anthrax spores after dispersion. |
| scifact-1019 | supported | unsupported | Rapid phosphotransfer rates govern fidelity in two component systems | The evidence mentions phosphotransfer rates and specificity but does not state that rapid rates govern fidelity. |
| scifact-514 | unsupported | supported | High dietary calcium intakes are unnecessary for prevention of secondary hyperparathyroidism in subjects with 25(OH)D levels above 75 nmol/liter. | The evidence concludes that 'calcium intake levels of more than 800 mg/d may be unnecessary for maintaining calcium metabolism' as long as vitamin D status is ensured (with 25(OH)D levels indicated via serum thresholds). |
| scifact-1385 | supported | contradicted | cSMAC formation enhances weak ligand signalling. | Evidence shows that the inability to form cSMAC underlies increased proliferation, and enhancing cSMAC formation reduced stimulatory capacity of the weak peptide. |
| scifact-1020 | supported | unsupported | Rapid up-regulation and higher basal expression of interferon-induced genes increase survival of granule cell neurons that are infected by West Nile virus. | While the evidence discusses ISGs in neurons, it does not mention West Nile virus or the survival of infected granule cell neurons. |
| scifact-852 | contradicted | unsupported | Non-invasive ventilation use should be decreased if there is inadequate response to conventional treatment. | None of the provided evidence addresses decreasing the use of non-invasive ventilation due to inadequate response to conventional treatment. |
| scifact-268 | unsupported | supported | Cold exposure increases BAT recruitment. | Evidence refers to 'cold-induced atherosclerotic lesions' and mentions 'uncoupling protein 1... involved in thermogenesis in brown adipose tissue (BAT)' in the context of cold-acclimated mice, supporting cold exposure and BAT recruitment. |
| scifact-1041 | contradicted | unsupported | Replacement of histone H2A with H2A.Z slows gene activation in yeasts by stabilizing +1 nucleosomes. | None of the provided evidence discusses the replacement of histone H2A with H2A.Z or its effect on gene activation and +1 nucleosomes in yeasts. |
| scifact-1335 | supported | unsupported | UCB T cells maintain high TCR diversity after transplantation. | None of the provided evidence discusses UCB T cells maintaining high TCR diversity. |
| scifact-238 | unsupported | supported | Cells undergoing methionine restriction may activate miRNAs. | The evidence states that "miRNAs... may become activators of expression during stress." |
| scifact-1389 | supported | contradicted | mTORC2 regulates intracellular cysteine levels through xCT inhibition. | The evidence states that mTORC2 phosphorylates xCT, "inhibiting its activity", rather than regulating intracellular cysteine levels through xCT inhibition. |
| scifact-770 | supported | unsupported | Metastatic colorectal cancer treated with a single agent fluoropyrimidines resulted in reduced efficacy and lower quality of life when compared with oxaliplatin-based chemotherapy in elderly patients. | None of the provided evidence passages address the efficacy or quality of life of single agent fluoropyrimidines compared with oxaliplatin-based chemotherapy. |
| scifact-847 | contradicted | partially_supported | New drugs for tuberculosis often do not penetrate the necrotic portion of a tuberculosis lesion in high concentrations. | The evidence states that moxifloxacin does not diffuse well in caseum, but does not state this as a general rule for 'new drugs for tuberculosis' broadly. |
| scifact-1336 | contradicted | unsupported | UCB T cells reduce TCR diversity after transplantation. | The evidence discusses TCR diversity after allo-HSCT and cord blood-graft recipients approximating healthy diversity, but does not state that UCB T cells reduce TCR diversity. |
| scifact-354 | unsupported | contradicted | Downregulation and mislocalization of Scribble prevents cell transformation and mammary tumorigenesis. | The evidence shows that downregulation and mislocalization of Scribble promotes cell transformation, dysplasia, and breast cancer formation rather than preventing them. |
| scifact-436 | supported | partially_supported | Free histones are degraded by a Rad53-dependent mechanism once DNA has been replicated. | The evidence confirms excess histones are degraded in a Rad53-dependent manner, but does not specifically mention that this occurs 'once DNA has been replicated', instead mentioning it when DNA replication slows down or stops. |

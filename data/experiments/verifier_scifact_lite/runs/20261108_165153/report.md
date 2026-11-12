# ATLAS Verifier Evaluation

- Dataset: `data\external\scifact_dev_150.jsonl` (150 examples)
- Model: `gemini-3.5-flash-lite` · batch size 12
- Gemini calls: 14 · time 191.49s

## Headline

| Accuracy | Macro F1 | Weighted F1 | Problem-claim precision | Problem-claim recall |
|---|---|---|---|---|
| 0.773 | 0.784 | 0.784 | 0.929 | 0.910 |

Problem claims = unsupported + contradicted, i.e. what ATLAS should flag.

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Supported | 0.833 | 0.800 | 0.816 | 50 |
| Partially Supported | 0.000 | 0.000 | 0.000 | 0 |
| Unsupported | 0.736 | 0.780 | 0.757 | 50 |
| Contradicted | 0.822 | 0.740 | 0.779 | 50 |

## Confusion matrix (rows = gold, columns = predicted)

| | Supported | Partially Supported | Unsupported | Contradicted |
|---|---|---|---|---|
| **Supported** | 40 | 3 | 5 | 2 |
| **Partially Supported** | 0 | 0 | 0 | 0 |
| **Unsupported** | 5 | 0 | 39 | 6 |
| **Contradicted** | 3 | 1 | 9 | 37 |

## Confidence

- Mean confidence when correct: 0.98; when wrong: 0.96
- Accuracy when confidence ≥ 0.8: 0.775 (98% of examples)

## Mistakes

| Id | Gold | Predicted | Claim | Rationale |
|---|---|---|---|---|
| scifact-1221 | contradicted | unsupported | The genomic aberrations found in matasteses are very similar to those found in the primary tumor. | None of the provided evidence sources discuss this claim. |
| scifact-882 | contradicted | supported | Omnivores produce less trimethylamine N-oxide from dietary I-carnitine than vegetarians. | Evidence 2-3 states that omnivorous human subjects produced less TMAO than did vegans or vegetarians, which is the product of dietary L-carnitine. |
| scifact-208 | supported | contradicted | CHEK2 is not associated with breast cancer. | The evidence states that 'Previous investigation has established a role for the CHEK2 gene in breast cancer aetiology', which contradicts the claim that it is not associated with breast cancer. |
| scifact-48 | contradicted | unsupported | A total of 1,000 people in the UK are asymptomatic carriers of vCJD infection. | The evidence reports a prevalence of 493 per million and mentions 177 vCJD cases, but does not state a total number of 1,000 asymptomatic carriers in the UK. |
| scifact-783 | unsupported | contradicted | Mice without IFN-γ or its receptor are resistant to EAM induced with α-MyHC/CFA. | The evidence states that 'IFN-gamma-deficient mice developed fatal autoimmune disease', which contradicts the claim that they are resistant to EAM. |
| scifact-1110 | contradicted | unsupported | Suboptimal nutrition is not predictive of chronic disease | The evidence discusses global disease burden and various risk factors like high BMI and undernutrition, but does not state that suboptimal nutrition is not predictive of chronic disease. |
| scifact-728 | contradicted | unsupported | Ly6C hi monocytes have a lower inflammatory capacity than Ly6C lo monocytes. | The evidence identifies mouse monocyte subpopulations based on differential expression of markers, but does not compare the inflammatory capacity of Ly6C hi and Ly6C lo monocytes. |
| scifact-410 | unsupported | contradicted | Febrile seizures increase the threshold for development of epilepsy. | The evidence shows that febrile seizures cause persistent alterations and increase inhibitory synaptic transmission, leading to views against the 'benign' nature, rather than increasing the threshold for development of epilepsy. |
| scifact-879 | contradicted | supported | Occupancy of ribosomes by IncRNAs do not make functional peptides. | Evidence E38-7 states that these results argue that the large majority of lincRNAs do not function through encoded proteins. |
| scifact-960 | supported | partially_supported | Polymeal nutrition reduces cardiovascular mortality. | Evidence shows the Polymeal reduces cardiovascular disease events and morbidity, but does not explicitly mention mortality. |
| scifact-269 | unsupported | contradicted | Cold exposure reduces BAT recruitment. | Evidence mentions cold-induced lesions and thermogenesis in brown adipose tissue (BAT), but does not state that cold exposure reduces BAT recruitment; rather, deletion of UCP1 protects against cold-induced lesions. |
| scifact-1368 | supported | unsupported | Vitamin D deficiency effects the term of delivery. | The evidence lists outcomes like gestational diabetes and birth weight but does not address the 'term of delivery'. |
| scifact-693 | supported | partially_supported | Leuko-reduced blood reduces infectious complications in red blood cell transfusion. | Evidence shows leukoreduction decreases mortality, fever, and antibiotic use, but specifically states that 'serious nosocomial infections did not decrease'. |
| scifact-956 | unsupported | supported | Pleiotropic coupling of GLP-1R to intracellular effectors promotes distinct profiles of cellular signaling. | Evidence 6 states that peptide agonists can engage different elements of the receptor to achieve effector coupling and biased signaling. |
| scifact-1021 | contradicted | unsupported | Rapid up-regulation and higher basal expression of interferon-induced genes reduce survival of granule cell neurons that are infected by West Nile virus. | The evidence mentions antiviral effects and interferon-stimulated genes, but does not state that they reduce survival of granule cell neurons infected by West Nile virus. |
| scifact-1303 | contradicted | unsupported | Tirasemtiv has no effect on fast-twitch muscle. | None of the provided evidence mentions Tirasemtiv or its effect on fast-twitch muscle. |
| scifact-1272 | unsupported | supported | The single flash-evoked ERG b-wave is generated by activity of ON-bipolar cells. | Evidence shows that mice lacking mGluR6 in retinal ON bipolar cells show a loss of ON responses, demonstrating the b-wave's generation by ON-bipolar cells. |
| scifact-718 | contradicted | unsupported | Low nucleosome occupancy correlates with low methylation levels across species. | The evidence mentions dense methylation disfavoring nucleosomes in certain linkers, but does not state a general correlation across species between low nucleosome occupancy and low methylation levels. |
| scifact-115 | contradicted | unsupported | Anthrax spores can be disposed of easily after they are dispersed. | None of the provided evidence passages discuss the ease of disposing of anthrax spores after dispersion. |
| scifact-1019 | supported | unsupported | Rapid phosphotransfer rates govern fidelity in two component systems | The evidence does not state that rapid phosphotransfer rates govern fidelity in two-component systems, although it discusses phosphotransfer and specificity. |
| scifact-514 | unsupported | supported | High dietary calcium intakes are unnecessary for prevention of secondary hyperparathyroidism in subjects with 25(OH)D levels above 75 nmol/liter. | Evidence states that 'As long as vitamin D status is ensured, calcium intake levels of more than 800 mg/d may be unnecessary'. |
| scifact-1385 | supported | contradicted | cSMAC formation enhances weak ligand signalling. | The evidence shows that enhancing cSMAC formation reduced the stimulatory capacity of the weak peptide, rather than enhancing its weak ligand signalling. |
| scifact-1020 | supported | unsupported | Rapid up-regulation and higher basal expression of interferon-induced genes increase survival of granule cell neurons that are infected by West Nile virus. | The evidence mentions interferon-stimulated genes mediating antiviral effects in granule cell neurons, but does not explicitly mention West Nile virus or increased survival due to rapid up-regulation and higher basal expression. |
| scifact-852 | contradicted | unsupported | Non-invasive ventilation use should be decreased if there is inadequate response to conventional treatment. | None of the provided evidence passages mention decreasing non-invasive ventilation use in response to inadequate conventional treatment. |
| scifact-268 | unsupported | supported | Cold exposure increases BAT recruitment. | Evidence confirms that cold exposure stimulates atherosclerotic plaque growth and involves thermogenesis in brown adipose tissue (BAT). |
| scifact-1335 | supported | unsupported | UCB T cells maintain high TCR diversity after transplantation. | The provided evidence passages do not mention UCB T cells maintaining high TCR diversity. |
| scifact-238 | unsupported | supported | Cells undergoing methionine restriction may activate miRNAs. | Evidence states that miRNAs 'may become activators of expression during stress' (E122-2). |
| scifact-183 | contradicted | supported | Bone marrow cells contribute to adult macrophage compartments. | Evidence states that 'after bone marrow transplantation, host macrophages retained the capacity to expand' (E124-4). |
| scifact-213 | unsupported | contradicted | CRP is not predictive of postoperative mortality following Coronary Artery Bypass Graft (CABG) surgery. | Evidence refers to the prognostic information conferred by C reactive protein as a basis for prioritisation strategies, contradicting the claim that it is not predictive (E127-11). |
| scifact-770 | supported | unsupported | Metastatic colorectal cancer treated with a single agent fluoropyrimidines resulted in reduced efficacy and lower quality of life when compared with oxaliplatin-based chemotherapy in elderly patients. | None of the provided evidence passages address this comparison regarding single agent fluoropyrimidines resulting in reduced efficacy and quality of life compared with oxaliplatin-based chemotherapy. |
| scifact-847 | contradicted | partially_supported | New drugs for tuberculosis often do not penetrate the necrotic portion of a tuberculosis lesion in high concentrations. | The evidence states that a specific new drug (moxifloxacin) does not diffuse well in caseum (the necrotic portion), but does not broadly establish this for 'new drugs' generally. |
| scifact-354 | unsupported | contradicted | Downregulation and mislocalization of Scribble prevents cell transformation and mammary tumorigenesis. | The evidence states that loss, depletion, or deregulation of Scribble promotes dysplastic and neoplastic growth and inhibits breast cancer formation, rather than preventing cell transformation. |
| scifact-411 | unsupported | contradicted | Febrile seizures reduce the threshold for development of epilepsy. | The evidence states that the contribution of febrile seizures to the development of epilepsy later in life remains controversial, which contradicts the claim that they reduce the threshold. |
| scifact-436 | supported | partially_supported | Free histones are degraded by a Rad53-dependent mechanism once DNA has been replicated. | The evidence states that excess histones are degraded in a Rad53-dependent manner, but does not specify that this happens strictly 'once DNA has been replicated'. |

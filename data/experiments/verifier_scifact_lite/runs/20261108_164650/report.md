# ATLAS Verifier Evaluation

- Dataset: `data\external\scifact_dev_150.jsonl` (150 examples)
- Model: `gemini-3.5-flash-lite` · batch size 12
- Gemini calls: 13 · time 203.91s

## Headline

| Accuracy | Macro F1 | Weighted F1 | Problem-claim precision | Problem-claim recall |
|---|---|---|---|---|
| 0.780 | 0.790 | 0.790 | 0.902 | 0.920 |

Problem claims = unsupported + contradicted, i.e. what ATLAS should flag.

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Supported | 0.841 | 0.740 | 0.787 | 50 |
| Partially Supported | 0.000 | 0.000 | 0.000 | 0 |
| Unsupported | 0.754 | 0.860 | 0.804 | 50 |
| Contradicted | 0.822 | 0.740 | 0.779 | 50 |

## Confusion matrix (rows = gold, columns = predicted)

| | Supported | Partially Supported | Unsupported | Contradicted |
|---|---|---|---|---|
| **Supported** | 37 | 3 | 5 | 5 |
| **Partially Supported** | 0 | 0 | 0 | 0 |
| **Unsupported** | 4 | 0 | 43 | 3 |
| **Contradicted** | 3 | 1 | 9 | 37 |

## Confidence

- Mean confidence when correct: 0.98; when wrong: 0.96
- Accuracy when confidence ≥ 0.8: 0.782 (98% of examples)

## Mistakes

| Id | Gold | Predicted | Claim | Rationale |
|---|---|---|---|---|
| scifact-1221 | contradicted | unsupported | The genomic aberrations found in matasteses are very similar to those found in the primary tumor. | None of the provided evidence sources discuss this claim. |
| scifact-882 | contradicted | supported | Omnivores produce less trimethylamine N-oxide from dietary I-carnitine than vegetarians. | Evidence 3 explicitly states that 'Omnivorous human subjects produced more TMAO than did vegans or vegetarians following ingestion of L-carnitine'. |
| scifact-1163 | supported | contradicted | The DdrB protein from Deinococcus radiodurans is an alternative SSB. | Evidence 6 states that DdrB 'comprises a novel fold that is structurally and topologically distinct from all other single-stranded binding (SSB) proteins characterized to date'. |
| scifact-208 | supported | contradicted | CHEK2 is not associated with breast cancer. | The evidence states that 'Previous investigation has established a role for the CHEK2 gene in breast cancer aetiology', contradicting the claim that it is not associated with breast cancer. |
| scifact-48 | contradicted | unsupported | A total of 1,000 people in the UK are asymptomatic carriers of vCJD infection. | The evidence reports an overall prevalence of 493 per million population based on 16 positive samples out of 32,441, but does not state a total of 1,000 people. |
| scifact-783 | unsupported | contradicted | Mice without IFN-γ or its receptor are resistant to EAM induced with α-MyHC/CFA. | The evidence states that 'IFN-gamma-deficient mice developed fatal autoimmune disease', which contradicts the claim that they are resistant to EAM. |
| scifact-1110 | contradicted | unsupported | Suboptimal nutrition is not predictive of chronic disease | The provided text lists global disease burdens and risk factors like childhood undernutrition, but does not state whether suboptimal nutrition is predictive of chronic disease. |
| scifact-728 | contradicted | unsupported | Ly6C hi monocytes have a lower inflammatory capacity than Ly6C lo monocytes. | The provided text does not compare the inflammatory capacities of Ly6C hi versus Ly6C lo monocytes. |
| scifact-879 | contradicted | supported | Occupancy of ribosomes by IncRNAs do not make functional peptides. | Evidence E38-7 states that the large majority of lincRNAs do not function through encoded proteins. |
| scifact-269 | unsupported | contradicted | Cold exposure reduces BAT recruitment. | The evidence discusses thermogenesis in brown adipose tissue (BAT) and cold exposure increasing plaque growth and cold-induced lesions, rather than reducing BAT recruitment. |
| scifact-1368 | supported | unsupported | Vitamin D deficiency effects the term of delivery. | The evidence lists pregnancy outcomes and birth variables such as gestational diabetes and birth weight, but does not address the 'term of delivery'. |
| scifact-693 | supported | partially_supported | Leuko-reduced blood reduces infectious complications in red blood cell transfusion. | Evidence shows leukoreduction reduced mortality but indicates 'serious nosocomial infections did not decrease', making the claim only partially supported. |
| scifact-956 | unsupported | supported | Pleiotropic coupling of GLP-1R to intracellular effectors promotes distinct profiles of cellular signaling. | Evidence indicates peptide agonists engage receptor elements 'to achieve effector coupling and biased signaling'. |
| scifact-1021 | contradicted | unsupported | Rapid up-regulation and higher basal expression of interferon-induced genes reduce survival of granule cell neurons that are infected by West Nile virus. | The evidence mentions innate immune programs and ISGs mediating antiviral effects, but does not state that they reduce survival of granule cell neurons infected by West Nile virus. |
| scifact-1303 | contradicted | unsupported | Tirasemtiv has no effect on fast-twitch muscle. | None of the evidence passages mention Tirasemtiv or its effect on fast-twitch muscle. |
| scifact-718 | contradicted | unsupported | Low nucleosome occupancy correlates with low methylation levels across species. | The evidence does not correlate low nucleosome occupancy with low methylation levels across species. |
| scifact-115 | contradicted | unsupported | Anthrax spores can be disposed of easily after they are dispersed. | None of the provided passages address the disposal of anthrax spores after dispersion. |
| scifact-1019 | supported | unsupported | Rapid phosphotransfer rates govern fidelity in two component systems | The text discusses specificity determinants and rapid phosphotransfer, but does not state that rapid phosphotransfer rates govern fidelity. |
| scifact-514 | unsupported | supported | High dietary calcium intakes are unnecessary for prevention of secondary hyperparathyroidism in subjects with 25(OH)D levels above 75 nmol/liter. | The conclusion explicitly states that 'As long as vitamin D status is ensured, calcium intake levels of more than 800 mg/d may be unnecessary'. |
| scifact-1385 | supported | contradicted | cSMAC formation enhances weak ligand signalling. | The evidence shows that the inability to form cSMAC could underlie increased proliferation, and enhancing cSMAC formation reduced stimulatory capacity. |
| scifact-1274 | supported | unsupported | The tip of the inner tube of the toxic type VI secretion system (T6SS) antibacterial effector in Escherichia coli (E. coli) carries toxic effector proteins. | The evidence discusses the VgrG spike and PAAR proteins forming a sharp extension, but does not mention the tip of the inner tube of the T6SS in E. coli carrying toxic effector proteins. |
| scifact-1020 | supported | partially_supported | Rapid up-regulation and higher basal expression of interferon-induced genes increase survival of granule cell neurons that are infected by West Nile virus. | The evidence confirms that interferon-stimulated genes mediate antiviral effects and correlate with enhanced antiviral responses in granule cell neurons, but does not specifically mention West Nile virus. |
| scifact-852 | contradicted | unsupported | Non-invasive ventilation use should be decreased if there is inadequate response to conventional treatment. | None of the provided evidence discusses decreasing non-invasive ventilation use due to inadequate response to conventional treatment. |
| scifact-268 | unsupported | supported | Cold exposure increases BAT recruitment. | Evidence states that UCP1 in brown adipose tissue (BAT) is involved in cold-induced/associated changes, and refers to cold-induced lesions and thermogenesis. |
| scifact-1335 | supported | unsupported | UCB T cells maintain high TCR diversity after transplantation. | None of the provided evidence passages discuss UCB T cells maintaining high TCR diversity. |
| scifact-238 | unsupported | supported | Cells undergoing methionine restriction may activate miRNAs. | The evidence states that 'miRNAs... may become activators of expression during stress'. |
| scifact-183 | contradicted | supported | Bone marrow cells contribute to adult macrophage compartments. | The evidence states that after bone marrow transplantation, host macrophages retained capacity to expand. |
| scifact-533 | supported | contradicted | Hyperfibrinogenemia increases rates of femoropopliteal bypass thrombosis. | The evidence shows higher patency (less thrombosis/occlusion) in patients with lower fibrinogen concentrations, meaning hyperfibrinogenemia increases occlusion. |
| scifact-1389 | supported | contradicted | mTORC2 regulates intracellular cysteine levels through xCT inhibition. | The evidence states that mTORC2 phosphorylates xCT to inhibit its activity, rather than regulating cysteine levels through xCT inhibition. |
| scifact-770 | supported | unsupported | Metastatic colorectal cancer treated with a single agent fluoropyrimidines resulted in reduced efficacy and lower quality of life when compared with oxaliplatin-based chemotherapy in elderly patients. | None of the provided evidence passages address metastatic colorectal cancer or single agent fluoropyrimidines resulting in reduced efficacy and quality of life compared with oxaliplatin. |
| scifact-847 | contradicted | partially_supported | New drugs for tuberculosis often do not penetrate the necrotic portion of a tuberculosis lesion in high concentrations. | While the evidence mentions that a specific drug (moxifloxacin) does not diffuse well in caseum, it does not broadly state this for 'new drugs for tuberculosis'. |
| scifact-354 | unsupported | contradicted | Downregulation and mislocalization of Scribble prevents cell transformation and mammary tumorigenesis. | The evidence states that Scribble inhibits breast cancer formation and that its downregulation and mislocalization promotes tumorigenesis, rather than preventing it. |
| scifact-436 | supported | partially_supported | Free histones are degraded by a Rad53-dependent mechanism once DNA has been replicated. | Evidence E149-2 confirms excess histones are degraded in a Rad53-dependent manner, but the condition 'once DNA has been replicated' differs from the evidence stating it occurs when DNA replication slows down or stops. |

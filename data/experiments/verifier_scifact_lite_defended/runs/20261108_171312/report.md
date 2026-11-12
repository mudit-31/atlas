# ATLAS Verifier Evaluation

- Dataset: `data\external\scifact_dev_150.jsonl` (150 examples)
- Model: `gemini-3.5-flash-lite` · batch size 12
- Gemini calls: 14 · time 185.56s

## Headline

| Accuracy | Macro F1 | Weighted F1 | Problem-claim precision | Problem-claim recall |
|---|---|---|---|---|
| 0.827 | 0.838 | 0.838 | 0.950 | 0.940 |

Problem claims = unsupported + contradicted, i.e. what ATLAS should flag.

## Per label

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Supported | 0.894 | 0.840 | 0.866 | 50 |
| Partially Supported | 0.000 | 0.000 | 0.000 | 0 |
| Unsupported | 0.782 | 0.860 | 0.819 | 50 |
| Contradicted | 0.886 | 0.780 | 0.830 | 50 |

## Confusion matrix (rows = gold, columns = predicted)

| | Supported | Partially Supported | Unsupported | Contradicted |
|---|---|---|---|---|
| **Supported** | 42 | 3 | 3 | 2 |
| **Partially Supported** | 0 | 0 | 0 | 0 |
| **Unsupported** | 3 | 1 | 43 | 3 |
| **Contradicted** | 2 | 0 | 9 | 39 |

## Confidence

- Mean confidence when correct: 0.89; when wrong: 0.82
- Accuracy when confidence ≥ 0.8: 0.833 (88% of examples)

## Mistakes

| Id | Gold | Predicted | Claim | Rationale |
|---|---|---|---|---|
| scifact-1221 | contradicted | unsupported | The genomic aberrations found in matasteses are very similar to those found in the primary tumor. | The evidence does not mention the genomic aberrations of metastases compared to primary tumors. |
| scifact-208 | supported | contradicted | CHEK2 is not associated with breast cancer. | The evidence explicitly states that '[p]revious investigation has established a role for the CHEK2 gene in breast cancer aetiology', contradicting the claim that it is not associated with breast cancer. |
| scifact-48 | contradicted | unsupported | A total of 1,000 people in the UK are asymptomatic carriers of vCJD infection. | The evidence states an overall prevalence of 493 per million population, but does not state a total of 1,000 people in the UK are asymptomatic carriers. |
| scifact-783 | unsupported | contradicted | Mice without IFN-γ or its receptor are resistant to EAM induced with α-MyHC/CFA. | The evidence states that 'IFN-gamma-deficient mice developed fatal autoimmune disease', meaning they are not resistant. |
| scifact-728 | contradicted | unsupported | Ly6C hi monocytes have a lower inflammatory capacity than Ly6C lo monocytes. | The evidence mentions monocyte subsets and inflammatory conditions, but does not compare the inflammatory capacity of Ly6C hi versus Ly6C lo monocytes. |
| scifact-879 | contradicted | supported | Occupancy of ribosomes by IncRNAs do not make functional peptides. | The evidence states that 'the large majority of lincRNAs do not function through encoded proteins.' |
| scifact-269 | unsupported | contradicted | Cold exposure reduces BAT recruitment. | The evidence states that cold exposure stimulates atherosclerotic plaque growth and involves thermogenesis in brown adipose tissue (BAT), rather than reducing BAT recruitment. |
| scifact-1368 | supported | partially_supported | Vitamin D deficiency effects the term of delivery. | The evidence notes associations with birthweight and bacterial vaginosis, but does not explicitly mention the general term of delivery. |
| scifact-693 | supported | partially_supported | Leuko-reduced blood reduces infectious complications in red blood cell transfusion. | The evidence shows leukoreduction decreases mortality, fever, and antibiotic use, but notes that serious nosocomial infections did not decrease. |
| scifact-956 | unsupported | supported | Pleiotropic coupling of GLP-1R to intracellular effectors promotes distinct profiles of cellular signaling. | The evidence states that peptide agonists 'achieve effector coupling and biased signaling'. |
| scifact-1021 | contradicted | unsupported | Rapid up-regulation and higher basal expression of interferon-induced genes reduce survival of granule cell neurons that are infected by West Nile virus. | The evidence discusses innate immune programs and antiviral effects of ISGs in granule cell neurons, but does not address neuron survival being reduced by these factors. |
| scifact-718 | contradicted | unsupported | Low nucleosome occupancy correlates with low methylation levels across species. | The evidence discusses dense methylation in nucleosome linkers and clustered methylation, but does not claim that low nucleosome occupancy correlates with low methylation levels across species. |
| scifact-115 | contradicted | unsupported | Anthrax spores can be disposed of easily after they are dispersed. | The provided evidence passages do not mention the disposal of anthrax spores. |
| scifact-514 | unsupported | partially_supported | High dietary calcium intakes are unnecessary for prevention of secondary hyperparathyroidism in subjects with 25(OH)D levels above 75 nmol/liter. | Evidence supports that calcium intake levels above 800 mg/d may be unnecessary if vitamin D status is ensured, but does not explicitly mention 75 nmol/liter (which equals 30 ng/mL, while evidence groups used >18 ng/mL). |
| scifact-1385 | supported | contradicted | cSMAC formation enhances weak ligand signalling. | Evidence shows that 'enhancing cSMAC formation reduced stimulatory capacity of the weak peptide', which contradicts the claim that it enhances signaling. |
| scifact-1274 | supported | unsupported | The tip of the inner tube of the toxic type VI secretion system (T6SS) antibacterial effector in Escherichia coli (E. coli) carries toxic effector proteins. | The evidence does not mention E. coli regarding this specific tip-carrying mechanism. |
| scifact-1020 | supported | unsupported | Rapid up-regulation and higher basal expression of interferon-induced genes increase survival of granule cell neurons that are infected by West Nile virus. | The evidence mentions antiviral effects of ISGs in neurons, but does not mention West Nile virus or increased survival via these mechanisms. |
| scifact-852 | contradicted | unsupported | Non-invasive ventilation use should be decreased if there is inadequate response to conventional treatment. | The provided text discusses the cost-effectiveness and mortality outcomes of non-invasive ventilation, but does not state that its use should be decreased. |
| scifact-1041 | contradicted | unsupported | Replacement of histone H2A with H2A.Z slows gene activation in yeasts by stabilizing +1 nucleosomes. | The evidence discusses H3.3 nucleosomes and salt-dependent disruption of H2A.Z, but does not state that H2A replacement with H2A.Z slows gene activation in yeasts. |
| scifact-146 | supported | unsupported | Autologous transplantation of mesenchymal stem cells has lower rates of rejection than induction therapy with anti-interleukin-2 receptor antibodies. | The evidence compares autologous MSCs with anti-IL-2 receptor antibody induction therapy, but does not mention rejection rates of MSC transplantation versus antibody induction itself being lower. |
| scifact-238 | unsupported | supported | Cells undergoing methionine restriction may activate miRNAs. | Evidence explicitly states that 'miRNAs... may become activators of expression during stress'. |
| scifact-183 | contradicted | supported | Bone marrow cells contribute to adult macrophage compartments. | Evidence shows that bone marrow (host macrophages after transplantation) contributes to macrophage compartments. |
| scifact-870 | unsupported | supported | Obesity decreases life quality. | Evidence shows obesity (high BMI) reduces median survival by several years, reflecting decreased life quality/outcomes. |
| scifact-847 | contradicted | unsupported | New drugs for tuberculosis often do not penetrate the necrotic portion of a tuberculosis lesion in high concentrations. | The text discusses penetration of specific drugs like rifampicin and moxifloxacin into lesions, but does not state that new drugs for tuberculosis often fail to penetrate necrotic portions in high concentrations. |
| scifact-354 | unsupported | contradicted | Downregulation and mislocalization of Scribble prevents cell transformation and mammary tumorigenesis. | The evidence states that 'scribble inhibits breast cancer formation and that deregulation of polarity pathways promotes dysplastic and neoplastic growth', which contradicts the claim that downregulation prevents transformation and tumorigenesis. |
| scifact-436 | supported | partially_supported | Free histones are degraded by a Rad53-dependent mechanism once DNA has been replicated. | The evidence confirms excess histones are degraded in a Rad53-dependent manner, but the detail that this happens specifically 'once DNA has been replicated' is not supported by the passages. |

# Planted-error test

- 10 real reports (Tavily + `gemini-3.5-flash-lite` for writing, extraction and verification)
- 71 planted errors, 54 untouched controls, shuffled together

| Metric | Value |
|---|---|
| Content errors detected (unsupported or contradicted) | 91.9% (57/62) |
| ...of which labelled contradicted | 72.6% |
| All planted errors detected (incl. wrong citations) | 90.1% |
| False alarms on untouched claims | 0.0% (0/54) |

| Error type | Planted | Detected | Rate | Verdicts |
|---|---|---|---|---|
| date | 6 | 6 | 100.0% | {'contradicted': 6} |
| entity | 19 | 14 | 73.7% | {'unsupported': 3, 'contradicted': 11, 'supported': 2, 'partially_supported': 3} |
| fabricated | 10 | 10 | 100.0% | {'unsupported': 9, 'contradicted': 1} |
| negation | 19 | 19 | 100.0% | {'contradicted': 19} |
| number | 8 | 8 | 100.0% | {'contradicted': 8} |
| wrong_citation | 9 | 7 | 77.8% | {'supported': 9} |

## Writer faithfulness (pass 1, before planting)

- 125 claims across 10 reports (12.5 per report)
- Verdict share: partially_supported 2.4%, supported 97.6%
- Mean trust score 94.5/100 · mean pipeline time 23.3s per report

## Missed errors

| Type | Original | Planted | Verdict |
|---|---|---|---|
| wrong_citation | The James Webb Space Telescope has studied exoplanet weather and planetary atmospheres. | The James Webb Space Telescope has studied exoplanet weather and planetary atmospheres. | supported |
| entity | Casgevy is indicated for the treatment of transfusion-dependent beta thalassemia. | Casgevy is indicated for the treatment of sickle cell anemia. | supported |
| wrong_citation | Casgevy is indicated for the treatment of sickle cell disease. | Casgevy is indicated for the treatment of sickle cell disease. | supported |
| entity | Intermittent fasting can improve glucose homeostasis, lipid profiles, blood sugar control, and chronic illness control. | Intermittent fasting can improve glucose homeostasis, lipid profiles, blood sugar control, and oncology control. | partially_supported |
| entity | Researchers face obstacles in accurately determining what people are actually eating during dietary interventions. | Physicians face obstacles in accurately determining what people are actually eating during dietary interventions. | supported |
| entity | COP28 resulted in an agreement to transition away from fossil fuels in energy systems. | COP28 resulted in an agreement to transition away from fossil fuels in the aviation sector. | partially_supported |
| entity | Nuclear fusion occurs when light nuclei, such as hydrogen isotopes, combine to form heavier elements like helium, releasing vast amounts of energy. | Nuclear fusion occurs when light nuclei, such as hydrogen isotopes, combine to form heavier elements like iron, releasing vast amounts of energy. | partially_supported |

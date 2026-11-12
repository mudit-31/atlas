# Planted-error test

- 10 real reports (Tavily + `gemini-3.5-flash-lite` for writing, extraction and verification)
- 74 planted errors, 55 untouched controls, shuffled together

| Metric | Value |
|---|---|
| Content errors detected (unsupported or contradicted) | 90.8% (59/65) |
| ...of which labelled contradicted | 66.1% |
| All planted errors detected (incl. wrong citations) | 91.9% |
| False alarms on untouched claims | 0.0% (0/55) |

| Error type | Planted | Detected | Rate | Verdicts |
|---|---|---|---|---|
| date | 7 | 6 | 85.7% | {'supported': 1, 'contradicted': 6} |
| entity | 20 | 16 | 80.0% | {'contradicted': 10, 'unsupported': 6, 'supported': 2, 'partially_supported': 2} |
| fabricated | 10 | 10 | 100.0% | {'unsupported': 10} |
| negation | 20 | 19 | 95.0% | {'contradicted': 19, 'supported': 1} |
| number | 8 | 8 | 100.0% | {'contradicted': 8} |
| wrong_citation | 9 | 9 | 100.0% | {'supported': 9} |

## Writer faithfulness (pass 1, before planting)

- 125 claims across 10 reports (12.5 per report)
- Verdict share: supported 98.4%, unsupported 0.8%, partially_supported 0.8%
- Mean trust score 99.2/100 · mean pipeline time 8.6s per report

## Missed errors

| Type | Original | Planted | Verdict |
|---|---|---|---|
| entity | The EU AI Act classifies AI systems according to their risk, regulating high-risk applications while prohibiting unacceptable risks and leaving minimal-risk systems unregulated. | The UN AI Act classifies AI systems according to their risk, regulating high-risk applications while prohibiting unacceptable risks and leaving minimal-risk systems unregulated. | supported |
| negation | The downturn in the United States housing market exposed widespread vulnerabilities tied to subprime lending and risky borrowing. | The downturn in the United States housing market concealed widespread vulnerabilities tied to subprime lending and risky borrowing. | supported |
| date | Excessively loose monetary policy in the United States during 2002-2004, low interest rates, lax lending standards, excessive leverage, and the underpricing of risk created large global imbalances that led to the crisis. | Excessively loose monetary policy in the United States during 2006-2008, low interest rates, lax lending standards, excessive leverage, and the underpricing of risk created large global imbalances that led to the crisis. | supported |
| entity | Researchers face obstacles in accurately determining what people are actually eating during dietary interventions. | Physicians face obstacles in accurately determining what people are actually eating during dietary interventions. | supported |
| entity | The landing process involved a precise, phased descent of the Vikram lander, carrying the Pragyan rover. | The landing process involved a precise, phased descent of the Vikram lander, carrying the Rashid rover. | partially_supported |
| entity | Nuclear fusion occurs when light nuclei, such as hydrogen isotopes, combine to form heavier elements like helium, releasing vast amounts of energy. | Nuclear fusion occurs when light nuclei, such as hydrogen isotopes, combine to form heavier elements like iron, releasing vast amounts of energy. | partially_supported |

# ATLAS: Measured Results

Every number below comes from a saved result file under `data/experiments/`. All runs used `gemini-3.5-flash-lite` with **fallback models disabled**: each `results.json` records `served_by`, so no number came from a different model than the one named. Cache was off for every repeated run. Measured 8 November 2026.

How to reproduce: [Reproducing](#reproducing) at the end.

---

## 1. Verifier accuracy on SciFact (external, expert-labelled)

SciFact ([Wadden et al., 2020](https://arxiv.org/abs/2004.14974)) is a public benchmark of scientific claims labelled by experts against paper abstracts. ATLAS used a class-balanced sample of **150 dev claims** (50 supported, 50 contradicted, 50 not-enough-info → "unsupported"), with each cited abstract split into sentence passages (9.3 per claim on average). Seed 13; sampling code is in `atlas/experiments/scifact.py`.

| Metric (3 runs, mean ± SD) | Original prompt | Injection-hardened prompt |
|---|---|---|
| Accuracy | 78.0% ± 0.5% | **82.0% ± 0.5%** |
| Macro F1 | 79.1% ± 0.6% | **83.2% ± 0.6%** |
| Problem-claim precision (unsupported + contradicted) | 91.4% ± 1.1% | **95.6% ± 0.9%** |
| Problem-claim recall | 92.3% ± 1.2% | **93.3% ± 0.5%** |
| Rationale hit rate¹ | 92.1% ± 1.0% | 92.2% ± 1.1% |
| Gemini calls per 150 claims | 13.3 | 13.3 |

¹ Of correct supported/contradicted verdicts, the share where the verifier cited a gold rationale sentence: right answer for the right reason.

The hardened prompt is better in every run: its worst run (81.3%) beats the original's best (78.7%).

Sources: `data/experiments/verifier_scifact_lite/20261108_165153_2/`, `data/experiments/verifier_scifact_lite_defended/20261108_171428_2/`

## 2. Planted-error detection on real reports

ATLAS generated **10 real reports** from live web search (EV sales, JWST, EU AI Act, 2008 crisis, CRISPR therapies, UPI, intermittent fasting, COP28, Chandrayaan-3, fusion). From claims the verifier judged supported, the harness planted controlled errors (number, date, entity, negation, fabricated claim, wrong citation). It re-verified them **shuffled together with the untouched originals**, so the verifier couldn't tell which were planted. Every planted error was audited by hand.

Results with the hardened verifier (current system):

| Error type | Planted | Detected | Rate |
|---|---|---|---|
| Number changed | 8 | 8 | 100% |
| Fabricated claim | 10 | 10 | 100% |
| Wrong citation | 9 | 9 | 100% |
| Negation | 20 | 19 | 95.0% |
| Date changed | 7 | 6 | 85.7% |
| Entity swapped | 20 | 16 | 80.0% |
| **All content errors** | **65** | **59** | **90.8%** |
| **All planted errors** | **74** | **68** | **91.9%** |
| **False alarms on 55 untouched claims** | — | 0 | **0.0%** |

- **Writer faithfulness:** 125 claims across the 10 reports; 98.4% judged supported, 0.8% partially supported, 0.8% unsupported.
- **Cost per report:** 3 Gemini calls + 1 Tavily credit. Uncached pipeline time averaged 23.3 s per report (from the first, uncached run).
- **Earlier run, original prompt:** 91.9% of content errors detected (57/62), 0/54 false alarms. One planted "error" in that run was actually true ("Casgevy is indicated for sickle cell anemia"); excluding it gives 93.4%. No invalid plants were found in the hardened run.

Sources: `data/experiments/planted_errors/20261108_171751/` (current), `data/experiments/planted_errors/20261108_170031_pre_defense/`

## 3. Prompt-injection red-team

There were 50 claims whose honest label is unsupported or contradicted: 20 ATLAS seed and 30 SciFact. Instructions were planted to force a "supported" verdict. Attack success means the claim was labelled supported or partially supported.

| Attack | Original prompt | Hardened prompt |
|---|---|---|
| None (baseline error rate) | 4.0% | 4.0% |
| Note to "automated fact-checkers" in a source | 2.0% | 4.0% |
| Fake closing tag + `[SYSTEM OVERRIDE]` in a source | **50.0%** | **4.0%** |
| Instruction appended to the claim text | **28.0%** | **6.0%** |
| Cross-claim: injection in 1 claim per batch, measured on the *other* claims | **24.4%** | **2.2%** |

**Finding:** batching 12 claims per call (a cost optimisation) let a single poisoned web page flip verdicts on unrelated claims in the same request.

**Fix:** claims and evidence are now sent as escaped JSON between data markers, the markers are stripped from the content so they can't be spoofed, and the system prompt declares everything inside them to be untrusted data. Residual successes under the hardened prompt are mostly the same two SciFact claims the verifier also gets wrong with no attack at all.

Sources: `data/experiments/prompt_injection/20261108_170444/`, `data/experiments/prompt_injection_defended/20261108_170805/`

## 4. Retrieval recall (BM25, no API calls)

There were 188 SciFact dev claims with gold evidence, searched against the **full 5,183-abstract corpus** (16,386 chunks):

| k | Gold abstract in top k | Gold rationale sentence in top k |
|---|---|---|
| 1 | 64.4% | 36.7% |
| 4 (ATLAS default) | 81.9% | 64.4% |
| 8 | 90.4% | 75.0% |
| 20 | 93.1% | 82.5% |

Index build took 1.1 s; mean query time was 2.6 ms. This is harder than ATLAS's normal setting, where retrieval searches only the ~6 sources fetched for a question.

Source: `data/experiments/retrieval_scifact/20261108_164022/`

## 5. Batch size

The same 48 SciFact claims, hardened prompt, 1 run each:

| Claims per call | Accuracy | Macro F1 | Gemini calls | Prompt tokens | Wall time |
|---|---|---|---|---|---|
| 12 (ATLAS default) | 81.3% (39/48) | 82.0% | **4** | **35,912** | **13 s** |
| 1 | 79.2% (38/48) | 79.7% | 48 | 53,952 | 251 s² |

Batching uses **12× fewer API calls and 33% fewer prompt tokens with no measured loss in accuracy**. The 1-claim difference is within noise at n = 48.

² Includes waiting on the 10-requests-per-minute client limit.

Sources: `data/experiments/batch_size_12_scifact48/20261108_171836/`, `data/experiments/batch_size_1_scifact48/20261108_172248/`

## 6. Seed benchmark (synthetic)

There are 40 examples written by an AI assistant (not human-labelled) using fictional entities. Accuracy was 97.5% with `gemini-3.6-flash` in 3/3 runs (original prompt) and 97.5% with `gemini-3.5-flash-lite` (hardened prompt, 1 run). It's too easy to separate models, so treat it as a smoke test only.

Sources: `data/experiments/verifier_seed_lite_defended/`; the `gemini-3.6-flash` runs are local only in `data/eval_runs/` (gitignored).

---

## Limitations

- **Single model family.** Writer, extractor and verifier are all `gemini-3.5-flash-lite`, so they may share blind spots. A comparison against `gemini-3.6-flash` was not possible: its free tier allows 20 requests per day, verified from the API's own quota error.
- **Generated errors.** The planted errors were written by the same model family and audited by one reviewer (Claude), not by independent humans.
- **Small samples.** There are 10 reports and 50 injection claims; per-type planted counts are 7–20, so single misses move rates by 5–14 points.
- **Self-reported confidence.** Confidence isn't calibrated: wrong verdicts still carried 0.9+ confidence on the seed benchmark.
- **Known miss pattern.** Swapping one item inside a list or compound claim (helium → iron, Pragyan → Rashid) tends to get "partially supported" instead of being flagged.
- **Defence tested only on the known attacks.** The injection defence was tested against these 4 attack styles only; adaptive attacks weren't tried.

## Reproducing

```bash
# SciFact data (3 MB, CC BY-NC 2.0) -> data/external/scifact/
curl -L -o data/external/scifact/data.tar.gz https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz
tar -xzf data/external/scifact/data.tar.gz -C data/external/scifact
```

```bash
python -m atlas experiment scifact-build
```

```bash
python -m atlas experiment retrieval
```

```bash
python -m atlas experiment verifier --dataset data/external/scifact_dev_150.jsonl --runs 3
```

```bash
python -m atlas experiment planted
```

```bash
python -m atlas experiment injection
```

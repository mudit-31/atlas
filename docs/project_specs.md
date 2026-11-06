# ATLAS Project Specification (v2)

## Goal

Given a research question, produce a cited report and a claim-by-claim verification of that report, with measurable reliability. Run within the free tiers of the Gemini API and Tavily.

## Functional requirements

| ID | Requirement | Implemented in |
|---|---|---|
| F1 | Search the web for a question and keep each source's title, URL and full text. | `atlas/search.py` |
| F2 | Generate a Markdown report (Summary, Key Findings, Limitations) using only the sources, with inline `[n]` citations. | `atlas/report.py` |
| F3 | Build the Sources list from search results, never from model output. | `atlas/report.py` |
| F4 | Extract atomic, self-contained factual claims and their cited source ids. | `atlas/claims.py` |
| F5 | Retrieve evidence passages per claim, always including the cited sources. | `atlas/retrieval.py` |
| F6 | Label each claim supported / partially supported / unsupported / contradicted, with confidence, evidence ids and a rationale. | `atlas/verify.py` |
| F7 | Compute trust score, citation coverage, citation accuracy and mean confidence. | `atlas/scoring.py` |
| F8 | Save every run as JSON, Markdown and standalone HTML. | `atlas/pipeline.py`, `atlas/render.py` |
| F9 | Fact-check arbitrary user-supplied text. | `Atlas.verify_text` |
| F10 | Evaluate the verifier on labelled JSONL data: accuracy, per-label P/R/F1, macro/weighted F1, problem-claim detection, confusion matrix, calibration. | `atlas/evaluation/` |
| F11 | CLI (`research`, `verify`, `evaluate`) and a web UI. | `atlas/cli.py`, `app.py` |

## Non-functional requirements

| ID | Requirement | How |
|---|---|---|
| N1 | Use few API calls: about 3 Gemini calls and 1 Tavily credit per report. | Batched verification, local BM25, Flash-Lite extraction |
| N2 | Never exceed the per-minute rate limit. | Sliding-window limiter (`GEMINI_RPM`) |
| N3 | Survive transient errors and quota limits. | Retries honouring `retryDelay`; model fallback chain |
| N4 | Make repeated work free. | Disk cache keyed by full request |
| N5 | Degrade gracefully. | Regex claim fallback; claims that get no verdict are flagged rather than failing the run |
| N6 | Tests run offline with no keys. | Dependency injection of fake LLM and searcher |
| N7 | Configuration through environment variables only. | `atlas/config.py`, `.env.example` |

## Verdict definitions

| Label | Definition |
|---|---|
| Supported | Evidence states or clearly entails the claim, including every number, date, name and qualifier. |
| Partially supported | Evidence backs the main point, but a detail is missing or not confirmed. |
| Unsupported | Evidence does not address the claim, or is too vague to confirm it. |
| Contradicted | Evidence states something incompatible with the claim. |

## Out of scope for v2

- Multi-agent planning and sub-query decomposition
- Follow-up searches for unsupported claims
- Hosted deployment and user accounts

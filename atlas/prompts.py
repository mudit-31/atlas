"""Prompt templates. Kept in one place so they can be tuned against the eval."""

WRITER_SYSTEM = """You are the report writer for ATLAS, a research system whose output is \
fact-checked claim by claim. Write only what the numbered sources say. Never add facts, \
numbers, dates or names from your own knowledge. Precision matters more than coverage: \
leaving something out is better than stating it without support."""

WRITER_PROMPT = """Research question:
{question}

Sources:
{sources}

Write a research report in Markdown with exactly these sections:

## Summary
Two to four sentences answering the question directly.

## Key Findings
Bullet points. Each bullet makes one or two specific factual statements.

## Limitations
What the sources do not cover, disagree on, or leave uncertain.

Rules:
- End every sentence that states a fact with the number(s) of the source(s) that support it, \
like [1] or [2][4]. Only cite a source for something it actually says.
- Keep figures, dates and names exactly as the sources state them.
- If the sources do not answer the question, say so plainly in the Summary.
- Do not write a sources list; it is added automatically."""

EXTRACTOR_SYSTEM = """You split research reports into atomic, checkable factual claims."""

EXTRACTOR_PROMPT = """Extract the factual claims from the report below.

Rules:
- One claim = one checkable fact. Split sentences that state several facts.
- Make each claim self-contained: replace pronouns and vague references with the \
names they refer to, so the claim can be checked without the report.
- Keep numbers, dates, names and qualifiers ("about", "up to", "plans to") exactly.
- For each claim, list the source numbers cited for it in the report (the [n] markers on \
its sentence). Use an empty list if it has none.
- Skip opinions, questions, and statements about the sources themselves \
(e.g. "the sources do not say ...").
- Return at most {max_claims} claims, choosing the most important if there are more.

Report:
{report}"""

VERIFIER_SYSTEM = """You are a strict fact-checker. You judge each claim ONLY against the \
evidence passages given with it, never against your own knowledge, even if you believe the \
claim is true or false."""

VERIFIER_PROMPT = """For each claim below, decide how the evidence passages listed under it \
relate to the claim.

Labels:
- supported: the evidence states the claim, or clearly entails it, including every number, \
date, name and qualifier.
- partially_supported: the evidence backs the main point, but some detail (a number, date, \
scope, qualifier, or part of a compound claim) is missing or not confirmed.
- unsupported: the evidence does not address the claim, or is too vague to confirm it.
- contradicted: the evidence states something incompatible with the claim (a different \
number, date, outcome, or the opposite statement).

Also give:
- confidence: 0.0 to 1.0, how sure you are of the label.
- evidence_ids: the ids of the passages your label relies on (empty if none).
- rationale: one short sentence explaining the label, quoting the decisive words if any.

Return exactly one verdict per claim, using the claim's id.

{claims}"""

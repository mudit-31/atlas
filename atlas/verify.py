"""Claim verification: judge claims against evidence, many claims per call."""

from __future__ import annotations

import json
import logging

from pydantic import BaseModel

from .llm import LLM, LLMError
from .prompts import VERIFIER_PROMPT, VERIFIER_SYSTEM
from .schemas import Claim, ClaimVerdict, Evidence, Label

logger = logging.getLogger(__name__)


class _Verdict(BaseModel):
    claim_id: str
    label: Label
    confidence: float
    evidence_ids: list[str]
    rationale: str


class _VerdictBatch(BaseModel):
    verdicts: list[_Verdict]


DATA_BEGIN = "BEGIN_UNTRUSTED_DATA"
DATA_END = "END_UNTRUSTED_DATA"


def format_claims_for_verifier(items: list[tuple[Claim, list[Evidence]]]) -> str:
    """Serialise claims and evidence as a JSON array inside data markers.

    JSON escaping means text inside a claim or passage (fake closing tags,
    "system" headers, quotes) cannot break out of its field, and the markers
    are stripped from the data so they cannot be spoofed.
    """
    def clean(text: str) -> str:
        return text.replace(DATA_BEGIN, "").replace(DATA_END, "")

    payload = [
        {
            "claim_id": claim.id,
            "claim": clean(claim.text),
            "cited_sources": claim.cited_sources,
            "evidence": [
                {"id": ev.chunk_id, "source": ev.source_id, "text": clean(ev.text)} for ev in evidence
            ],
        }
        for claim, evidence in items
    ]
    return f"{DATA_BEGIN}\n{json.dumps(payload, ensure_ascii=False, indent=1)}\n{DATA_END}"


def _no_evidence_verdict(claim: Claim) -> ClaimVerdict:
    return ClaimVerdict(
        claim=claim,
        label=Label.UNSUPPORTED,
        confidence=0.9,
        rationale="No passage in the retrieved sources relates to this claim.",
        evidence=[],
    )


def _judge_batch(
    llm: LLM, model: str, batch: list[tuple[Claim, list[Evidence]]]
) -> dict[str, ClaimVerdict]:
    prompt = VERIFIER_PROMPT.format(claims=format_claims_for_verifier(batch))
    result = llm.generate_json(prompt, _VerdictBatch, model=model, system=VERIFIER_SYSTEM)
    by_id = {claim.id: (claim, evidence) for claim, evidence in batch}
    verdicts: dict[str, ClaimVerdict] = {}
    for v in result.verdicts:
        cid = v.claim_id.strip()
        if cid not in by_id and f"C{cid}" in by_id:  # model dropped the "C" prefix
            cid = f"C{cid}"
        if cid not in by_id or cid in verdicts:
            continue
        claim, evidence = by_id[cid]
        valid = {e.chunk_id for e in evidence}
        verdicts[cid] = ClaimVerdict(
            claim=claim,
            label=v.label,
            confidence=min(1.0, max(0.0, float(v.confidence))),
            rationale=v.rationale.strip(),
            evidence=evidence,
            cited_evidence_ids=[e for e in v.evidence_ids if e in valid],
        )
    return verdicts


def judge_claims(
    llm: LLM,
    model: str,
    items: list[tuple[Claim, list[Evidence]]],
    batch_size: int = 12,
) -> list[ClaimVerdict]:
    """Verify (claim, evidence) pairs. Claims with no evidence are labelled
    unsupported locally; the rest are sent in batches of `batch_size`."""
    results: dict[str, ClaimVerdict] = {}
    pending: list[tuple[Claim, list[Evidence]]] = []
    for claim, evidence in items:
        if evidence:
            pending.append((claim, evidence))
        else:
            results[claim.id] = _no_evidence_verdict(claim)

    batch_size = max(1, batch_size)
    for start in range(0, len(pending), batch_size):
        batch = pending[start : start + batch_size]
        try:
            got = _judge_batch(llm, model, batch)
        except LLMError as exc:
            logger.error("Verification batch failed: %s", exc)
            got = {}
        missing = [item for item in batch if item[0].id not in got]
        if missing and got:
            # The model skipped some claims; ask once more for just those.
            try:
                got.update(_judge_batch(llm, model, missing))
            except LLMError as exc:
                logger.error("Retry for skipped claims failed: %s", exc)
        for claim, evidence in batch:
            results[claim.id] = got.get(claim.id) or ClaimVerdict(
                claim=claim,
                label=Label.UNSUPPORTED,
                confidence=0.0,
                rationale="The verifier did not return a verdict for this claim.",
                evidence=evidence,
                error="no_verdict",
            )

    return [results[claim.id] for claim, _ in items]

"""Report-level trust metrics computed from claim verdicts (no API calls)."""

from __future__ import annotations

from .schemas import LABEL_ORDER, ClaimVerdict, Label, TrustSummary

# Contribution of each label to the trust score. Contradictions count
# against the report, not just as missing support.
LABEL_WEIGHTS = {
    Label.SUPPORTED: 1.0,
    Label.PARTIALLY_SUPPORTED: 0.5,
    Label.UNSUPPORTED: 0.0,
    Label.CONTRADICTED: -0.5,
}


def summarize(verdicts: list[ClaimVerdict]) -> TrustSummary:
    total = len(verdicts)
    counts = {label.value: 0 for label in LABEL_ORDER}
    for v in verdicts:
        counts[v.label.value] += 1

    if total == 0:
        return TrustSummary(
            total_claims=0,
            counts=counts,
            trust_score=0.0,
            citation_coverage=0.0,
            citation_accuracy=None,
            mean_confidence=0.0,
        )

    raw = sum(LABEL_WEIGHTS[v.label] for v in verdicts) / total
    trust = round(100 * min(1.0, max(0.0, raw)), 1)

    cited = [v for v in verdicts if v.claim.cited_sources]
    coverage = round(len(cited) / total, 3)

    accuracy: float | None = None
    if cited:
        backed = 0
        for v in cited:
            if v.label not in (Label.SUPPORTED, Label.PARTIALLY_SUPPORTED):
                continue
            used = {e.source_id for e in v.evidence if e.chunk_id in v.cited_evidence_ids}
            if used & set(v.claim.cited_sources):
                backed += 1
        accuracy = round(backed / len(cited), 3)

    return TrustSummary(
        total_claims=total,
        counts=counts,
        trust_score=trust,
        citation_coverage=coverage,
        citation_accuracy=accuracy,
        mean_confidence=round(sum(v.confidence for v in verdicts) / total, 3),
    )

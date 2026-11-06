"""Data models shared across the pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class Label(str, Enum):
    """Verification verdict for a single claim."""

    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"

    @property
    def display(self) -> str:
        return self.value.replace("_", " ").title()


LABEL_ORDER: list[Label] = [
    Label.SUPPORTED,
    Label.PARTIALLY_SUPPORTED,
    Label.UNSUPPORTED,
    Label.CONTRADICTED,
]


class Source(BaseModel):
    """A retrieved web document. `id` is the 1-based citation number."""

    id: int
    title: str = ""
    url: str = ""
    snippet: str = ""
    content: str = ""
    score: float | None = None

    @property
    def text(self) -> str:
        """Best available text: full page content, else the search snippet."""
        return self.content or self.snippet


class Chunk(BaseModel):
    """A passage of a source, the unit of evidence shown to the verifier."""

    id: str  # e.g. "S2-C4"
    source_id: int
    text: str


class Claim(BaseModel):
    id: str  # e.g. "C7"
    text: str
    cited_sources: list[int] = Field(default_factory=list)
    section: str = ""


class Evidence(BaseModel):
    chunk_id: str
    source_id: int
    text: str
    score: float = 0.0


class ClaimVerdict(BaseModel):
    claim: Claim
    label: Label
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""
    evidence: list[Evidence] = Field(default_factory=list)
    # Chunks the verifier actually relied on (subset of `evidence`).
    cited_evidence_ids: list[str] = Field(default_factory=list)
    error: str | None = None


class TrustSummary(BaseModel):
    total_claims: int
    counts: dict[str, int]
    trust_score: float  # 0-100
    citation_coverage: float  # share of claims with at least one citation
    citation_accuracy: float | None  # share of cited claims backed by a cited source
    mean_confidence: float


class Usage(BaseModel):
    llm_calls: int = 0
    llm_cache_hits: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0
    calls_by_model: dict[str, int] = Field(default_factory=dict)
    search_calls: int = 0
    search_cache_hits: int = 0
    search_credits: int = 0


class ResearchResult(BaseModel):
    question: str
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    report_markdown: str
    sources: list[Source]
    verdicts: list[ClaimVerdict]
    summary: TrustSummary
    usage: Usage
    elapsed_seconds: float = 0.0
    models: dict[str, str] = Field(default_factory=dict)

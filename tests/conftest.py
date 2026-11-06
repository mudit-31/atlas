"""Shared fakes so tests never call real APIs."""

from __future__ import annotations

import re

import pytest

from atlas.config import Settings
from atlas.schemas import Source

REPORT_BODY = """## Summary
Veltrix Energy opened the Halden solar farm with a capacity of 420 megawatts [1].

## Key Findings
- The farm can power about 150,000 homes [1].
- The farm cost 2 billion euros [2].
- The farm was built in 1990 [1].

## Limitations
The sources do not discuss future plans.

## Sources
1. made-up list the model should not be trusted with
"""

SOURCES = [
    Source(
        id=1,
        title="Veltrix switches on Halden",
        url="https://example.com/halden",
        snippet="Halden solar farm opens.",
        content=(
            "Veltrix Energy switched on its Halden solar farm in March 2024. "
            "The site has a capacity of 420 megawatts and can power about 150,000 homes. "
            "Construction began in 2022."
        ),
    ),
    Source(
        id=2,
        title="Energy news roundup",
        url="https://example.com/roundup",
        snippet="Wind and solar news.",
        content="Offshore wind auctions in the North Sea attracted record bids this year.",
    ),
]

CLAIM_LABELS = {
    "420 megawatts": ("supported", 0.95),
    "150,000 homes": ("supported", 0.9),
    "2 billion": ("unsupported", 0.8),
    "1990": ("contradicted", 0.85),
}


class FakeLLM:
    """Returns canned outputs based on the requested schema."""

    def __init__(self, drop_claim: str | None = None) -> None:
        self.calls: list[tuple[str, str]] = []
        self.drop_claim = drop_claim

    def generate_text(self, prompt, *, model, system=None):
        self.calls.append(("text", model))
        return REPORT_BODY

    def generate_json(self, prompt, schema, *, model, system=None):
        self.calls.append((schema.__name__, model))
        if schema.__name__ == "_ExtractedClaims":
            return schema.model_validate(
                {
                    "claims": [
                        {"text": "The Halden solar farm has a capacity of 420 megawatts.", "cited_sources": [1], "section": "Summary"},
                        {"text": "The Halden solar farm can power about 150,000 homes.", "cited_sources": [1, 9], "section": "Key Findings"},
                        {"text": "The Halden solar farm cost 2 billion euros.", "cited_sources": [2], "section": "Key Findings"},
                        {"text": "The Halden solar farm was built in 1990.", "cited_sources": [1], "section": "Key Findings"},
                    ]
                }
            )
        if schema.__name__ == "_VerdictBatch":
            first_batch = sum(1 for kind, _ in self.calls if kind == "_VerdictBatch") == 1
            verdicts = []
            for cid, text in re.findall(r"### Claim (\S+)\nClaim: (.*)", prompt):
                if self.drop_claim and self.drop_claim in text and first_batch:
                    continue
                label, conf = next(
                    (v for k, v in CLAIM_LABELS.items() if k in text), ("unsupported", 0.5)
                )
                ids = re.findall(r"^\[(\S+)\]", prompt.split(f"### Claim {cid}\n", 1)[1], re.M)
                verdicts.append(
                    {
                        "claim_id": cid,
                        "label": label,
                        "confidence": conf,
                        "evidence_ids": ids[:1] if label != "unsupported" else [],
                        "rationale": f"fake verdict for {cid}",
                    }
                )
            return schema.model_validate({"verdicts": verdicts})
        raise AssertionError(f"unexpected schema {schema.__name__}")


class FakeSearcher:
    def __init__(self, sources=None) -> None:
        self.sources = sources or SOURCES
        self.queries: list[str] = []

    def search(self, query, max_results):
        self.queries.append(query)
        return self.sources[:max_results]


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(
        google_api_key="test-key",
        tavily_api_key="test-key",
        gemini_rpm=0,
        cache_dir=tmp_path / "cache",
        output_dir=tmp_path / "outputs",
        eval_dir=tmp_path / "evals",
    )

"""Claim extraction: split a report into atomic, checkable claims."""

from __future__ import annotations

import logging
import re

from pydantic import BaseModel

from .config import Settings
from .llm import LLM, LLMError
from .prompts import EXTRACTOR_PROMPT, EXTRACTOR_SYSTEM
from .report import strip_sources_section
from .schemas import Claim

logger = logging.getLogger(__name__)

_CITATION_RE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


class _ExtractedClaim(BaseModel):
    text: str
    cited_sources: list[int]
    section: str


class _ExtractedClaims(BaseModel):
    claims: list[_ExtractedClaim]


def _normalise(text: str) -> str:
    return re.sub(r"\W+", " ", text.lower()).strip()


def _finalise(raw: list[tuple[str, list[int], str]], valid_ids: set[int], limit: int) -> list[Claim]:
    claims: list[Claim] = []
    seen: set[str] = set()
    for text, cited, section in raw:
        text = _CITATION_RE.sub("", text).strip()
        text = re.sub(r"\s+", " ", text).strip(" -*")
        key = _normalise(text)
        if len(key) < 8 or key in seen:
            continue
        seen.add(key)
        cited_ids = sorted({c for c in cited if c in valid_ids}) if valid_ids else sorted(set(cited))
        claims.append(Claim(id=f"C{len(claims) + 1}", text=text, cited_sources=cited_ids, section=section))
        if len(claims) >= limit:
            break
    return claims


def extract_claims_heuristic(report: str, valid_ids: set[int], limit: int) -> list[Claim]:
    """No-API fallback: every sentence that carries a [n] citation is a claim."""
    body = strip_sources_section(report)
    raw: list[tuple[str, list[int], str]] = []
    section = ""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            section = stripped.lstrip("#").strip()
            continue
        if not stripped:
            continue
        stripped = re.sub(r"^[-*+]\s+|^\d+\.\s+", "", stripped)
        for sentence in _SENTENCE_RE.split(stripped):
            cites = [int(n) for group in _CITATION_RE.findall(sentence) for n in group.split(",")]
            if cites:
                raw.append((sentence, cites, section))
    return _finalise(raw, valid_ids, limit)


def extract_claims(llm: LLM, settings: Settings, report: str, valid_ids: set[int]) -> list[Claim]:
    body = strip_sources_section(report)
    prompt = EXTRACTOR_PROMPT.format(max_claims=settings.max_claims, report=body)
    try:
        result = llm.generate_json(
            prompt, _ExtractedClaims, model=settings.extractor_model, system=EXTRACTOR_SYSTEM
        )
    except LLMError as exc:
        logger.warning("LLM claim extraction failed (%s); using citation-based fallback.", exc)
        return extract_claims_heuristic(report, valid_ids, settings.max_claims)

    raw = [(c.text, c.cited_sources, c.section) for c in result.claims]
    claims = _finalise(raw, valid_ids, settings.max_claims)
    if not claims:
        logger.warning("Extractor returned no claims; using citation-based fallback.")
        return extract_claims_heuristic(report, valid_ids, settings.max_claims)
    return claims

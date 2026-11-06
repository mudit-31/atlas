"""Report generation: one Gemini call turns sources into a cited report."""

from __future__ import annotations

import re

from .config import Settings
from .llm import LLM
from .prompts import WRITER_PROMPT, WRITER_SYSTEM
from .schemas import Source

_SOURCES_HEADING_RE = re.compile(r"^#{1,6}\s*(sources|references)\b.*$", re.IGNORECASE | re.MULTILINE)


def format_sources_for_writer(sources: list[Source], chars_per_source: int) -> str:
    blocks = []
    for s in sources:
        text = s.text[:chars_per_source].strip()
        blocks.append(f"[{s.id}] {s.title}\nURL: {s.url}\n{text}")
    return "\n\n---\n\n".join(blocks)


def strip_sources_section(markdown: str) -> str:
    """Remove a trailing Sources/References section if the model wrote one."""
    match = _SOURCES_HEADING_RE.search(markdown)
    return markdown[: match.start()].rstrip() if match else markdown.rstrip()


def sources_section(sources: list[Source]) -> str:
    lines = ["## Sources", ""]
    for s in sources:
        title = s.title or s.url or f"Source {s.id}"
        lines.append(f"{s.id}. [{title}]({s.url})" if s.url else f"{s.id}. {title}")
    return "\n".join(lines)


def generate_report(llm: LLM, settings: Settings, question: str, sources: list[Source]) -> str:
    prompt = WRITER_PROMPT.format(
        question=question,
        sources=format_sources_for_writer(sources, settings.writer_chars_per_source),
    )
    body = llm.generate_text(prompt, model=settings.writer_model, system=WRITER_SYSTEM)
    body = strip_sources_section(body)
    # The source list is built from search results, never by the model, so
    # titles and URLs can't be hallucinated.
    return f"# {question.strip()}\n\n{body}\n\n{sources_section(sources)}\n"

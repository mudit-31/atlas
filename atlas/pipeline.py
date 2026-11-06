"""End-to-end orchestration: search -> write -> extract -> retrieve -> verify -> score."""

from __future__ import annotations

import json
import logging
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Callable

from .claims import extract_claims
from .config import Settings
from .llm import LLM, GeminiLLM
from .report import generate_report
from .retrieval import BM25Index, build_chunks
from .schemas import ResearchResult, Source, Usage
from .scoring import summarize
from .search import Searcher, TavilySearcher
from .verify import judge_claims

logger = logging.getLogger(__name__)

Progress = Callable[[str], None]


def _noop(_: str) -> None:
    pass


class Atlas:
    """The ATLAS pipeline. Pass `llm`/`searcher` to swap in fakes for tests."""

    def __init__(
        self,
        settings: Settings | None = None,
        llm: LLM | None = None,
        searcher: Searcher | None = None,
        usage: Usage | None = None,
    ) -> None:
        self.settings = settings or Settings.from_env()
        self.usage = usage or Usage()
        self.llm = llm if llm is not None else GeminiLLM(self.settings, self.usage)
        self.searcher = searcher if searcher is not None else TavilySearcher(self.settings, self.usage)

    # ------------------------------------------------------------------ public

    def research(self, question: str, progress: Progress = _noop) -> ResearchResult:
        """Research a question and return a verified report."""
        question = question.strip()
        if not question:
            raise ValueError("The research question is empty.")
        started = time.perf_counter()

        progress("Searching the web")
        sources = self.searcher.search(question, self.settings.max_sources)

        progress("Writing the report")
        report = generate_report(self.llm, self.settings, question, sources)

        return self._verify(question, report, sources, started, progress)

    def verify_text(self, text: str, question: str, progress: Progress = _noop) -> ResearchResult:
        """Fact-check any existing text (e.g. another chatbot's answer).

        Evidence comes from a web search on `question`; claims in `text`
        are checked against it regardless of what the text cites.
        """
        if not text.strip():
            raise ValueError("The text to verify is empty.")
        started = time.perf_counter()
        progress("Searching the web for evidence")
        sources = self.searcher.search(question.strip(), self.settings.max_sources)
        return self._verify(question.strip(), text, sources, started, progress)

    # ---------------------------------------------------------------- internal

    def _verify(
        self,
        question: str,
        report: str,
        sources: list[Source],
        started: float,
        progress: Progress,
    ) -> ResearchResult:
        s = self.settings
        progress("Extracting claims")
        claims = extract_claims(self.llm, s, report, {src.id for src in sources})

        progress("Finding evidence")
        index = BM25Index(build_chunks(sources, s.chunk_chars, s.chunk_overlap))
        items = [(claim, index.evidence_for(claim, s.evidence_per_claim)) for claim in claims]

        progress(f"Verifying {len(claims)} claims")
        verdicts = judge_claims(self.llm, s.verifier_model, items, s.verify_batch_size)

        progress("Scoring")
        return ResearchResult(
            question=question,
            report_markdown=report,
            sources=sources,
            verdicts=verdicts,
            summary=summarize(verdicts),
            usage=self.usage.model_copy(deep=True),
            elapsed_seconds=round(time.perf_counter() - started, 2),
            models={
                "writer": s.writer_model,
                "extractor": s.extractor_model,
                "verifier": s.verifier_model,
            },
        )


def slugify(text: str, max_len: int = 50) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text).strip("-")
    return text[:max_len].rstrip("-") or "report"


def save_result(result: ResearchResult, output_dir: Path) -> Path:
    """Write result.json, report.md and report.html into a new run folder."""
    from .render import render_html, render_markdown

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(output_dir) / f"{stamp}_{slugify(result.question)}"
    suffix = 1
    while run_dir.exists():
        suffix += 1
        run_dir = Path(output_dir) / f"{stamp}_{slugify(result.question)}_{suffix}"
    run_dir.mkdir(parents=True)

    (run_dir / "result.json").write_text(
        json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (run_dir / "report.md").write_text(render_markdown(result), encoding="utf-8")
    (run_dir / "report.html").write_text(render_html(result), encoding="utf-8")
    logger.info("Saved run to %s", run_dir)
    return run_dir

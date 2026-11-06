"""Web search via Tavily, with caching to save free-tier credits."""

from __future__ import annotations

import logging
from typing import Protocol

from .cache import DiskCache, make_key
from .config import Settings
from .schemas import Source, Usage

logger = logging.getLogger(__name__)

CREDITS_PER_DEPTH = {"basic": 1, "fast": 1, "ultra-fast": 1, "advanced": 2}


class SearchError(RuntimeError):
    pass


class Searcher(Protocol):
    def search(self, query: str, max_results: int) -> list[Source]: ...


class TavilySearcher:
    def __init__(
        self, settings: Settings, usage: Usage | None = None, client: object | None = None
    ) -> None:
        self.settings = settings
        self.usage = usage if usage is not None else Usage()
        self.cache = DiskCache(settings.cache_dir, "search", enabled=settings.cache_enabled)
        if client is None:
            from tavily import TavilyClient

            client = TavilyClient(api_key=settings.require_tavily())
        self.client = client

    def search(self, query: str, max_results: int) -> list[Source]:
        depth = self.settings.search_depth
        key = make_key("tavily", query, max_results, depth)
        cached = self.cache.get(key)
        if cached is not None:
            self.usage.search_cache_hits += 1
            return [Source.model_validate(item) for item in cached]

        logger.info("Searching Tavily (%s, %d results): %s", depth, max_results, query)
        try:
            response = self.client.search(
                query=query,
                search_depth=depth,
                max_results=max_results,
                include_raw_content="markdown",
            )
        except Exception as exc:  # the SDK raises several unrelated types
            raise SearchError(f"Tavily search failed: {exc}") from exc

        self.usage.search_calls += 1
        self.usage.search_credits += CREDITS_PER_DEPTH.get(depth, 1)

        sources = parse_results(response, self.settings.max_source_chars)
        if not sources:
            raise SearchError(f"Tavily returned no results for: {query!r}")
        self.cache.set(key, [s.model_dump() for s in sources])
        return sources


def parse_results(response: dict, max_chars: int) -> list[Source]:
    sources: list[Source] = []
    seen_urls: set[str] = set()
    for item in response.get("results", []) or []:
        url = item.get("url") or ""
        if url and url in seen_urls:
            continue
        seen_urls.add(url)
        raw = (item.get("raw_content") or "").strip()
        sources.append(
            Source(
                id=len(sources) + 1,
                title=(item.get("title") or "").strip(),
                url=url,
                snippet=(item.get("content") or "").strip(),
                content=raw[:max_chars],
                score=item.get("score"),
            )
        )
    return sources

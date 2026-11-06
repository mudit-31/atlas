"""Local evidence retrieval: chunk sources, rank chunks per claim with BM25.

This runs entirely on the CPU, so finding evidence for each claim costs no
API calls and no embedding quota.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from .schemas import Chunk, Claim, Evidence, Source

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[.,][0-9]+)*")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")

STOPWORDS = frozenset(
    """a an and are as at be been but by can could did do does for from had has have he her
    his how i if in into is it its may might more most no not of on or our she should so
    such than that the their them then there these they this those to was we were what
    when where which while who will with would you your also about after over under""".split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


def _clean(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)  # markdown images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # markdown links -> text
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, max_chars: int = 700, overlap: int = 120) -> list[str]:
    """Split text into ~max_chars passages on sentence boundaries, with overlap."""
    text = _clean(text)
    if not text:
        return []
    sentences: list[str] = []
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = " ".join(paragraph.split())
        if paragraph:
            sentences.extend(s for s in _SENTENCE_RE.split(paragraph) if s.strip())

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        while len(sentence) > max_chars:  # hard-split very long "sentences"
            head, sentence = sentence[:max_chars], sentence[max_chars:]
            if current:
                chunks.append(current)
                current = ""
            chunks.append(head)
        if current and len(current) + 1 + len(sentence) > max_chars:
            chunks.append(current)
            tail = current[-overlap:] if overlap > 0 else ""
            # Start the overlap at a word boundary.
            tail = tail[tail.find(" ") + 1 :] if " " in tail else tail
            current = f"{tail} {sentence}".strip() if tail else sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def build_chunks(sources: list[Source], max_chars: int = 700, overlap: int = 120) -> list[Chunk]:
    chunks: list[Chunk] = []
    for source in sources:
        pieces = chunk_text(source.text, max_chars, overlap)
        if not pieces and source.snippet:
            pieces = [source.snippet]
        for i, piece in enumerate(pieces, 1):
            chunks.append(Chunk(id=f"S{source.id}-C{i}", source_id=source.id, text=piece))
    return chunks


class BM25Index:
    """Okapi BM25 over a fixed list of chunks."""

    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75) -> None:
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.docs = [Counter(tokenize(c.text)) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = (sum(self.lengths) / len(self.lengths)) if self.lengths else 0.0
        df: Counter[str] = Counter()
        for doc in self.docs:
            df.update(doc.keys())
        n = len(chunks)
        self.idf = {term: math.log(1 + (n - f + 0.5) / (f + 0.5)) for term, f in df.items()}

    def score(self, query: str) -> list[float]:
        terms = tokenize(query)
        scores = [0.0] * len(self.chunks)
        if not terms or not self.avg_len:
            return scores
        for i, doc in enumerate(self.docs):
            norm = self.k1 * (1 - self.b + self.b * self.lengths[i] / self.avg_len)
            total = 0.0
            for term in terms:
                tf = doc.get(term)
                if tf:
                    total += self.idf[term] * tf * (self.k1 + 1) / (tf + norm)
            scores[i] = total
        return scores

    def evidence_for(self, claim: Claim, k: int = 4) -> list[Evidence]:
        """Top-k chunks for a claim, always including the best chunk from each
        source the claim cites (so citation accuracy can be judged)."""
        if not self.chunks:
            return []
        scores = self.score(claim.text)
        ranked = sorted(range(len(self.chunks)), key=lambda i: scores[i], reverse=True)

        picked: list[int] = []
        for source_id in claim.cited_sources:
            best = next((i for i in ranked if self.chunks[i].source_id == source_id), None)
            if best is not None and best not in picked:
                picked.append(best)
        for i in ranked:
            if len(picked) >= k:
                break
            if i not in picked and scores[i] > 0:
                picked.append(i)

        picked.sort(key=lambda i: scores[i], reverse=True)
        return [
            Evidence(
                chunk_id=self.chunks[i].id,
                source_id=self.chunks[i].source_id,
                text=self.chunks[i].text,
                score=round(scores[i], 3),
            )
            for i in picked
        ]

"""SciFact: an external, expert-labelled benchmark (Wadden et al., EMNLP 2020).

* `build_benchmark` turns the SciFact dev split into an ATLAS JSONL dataset
  (SUPPORT -> supported, CONTRADICT -> contradicted, NEI -> unsupported), using
  each claim's cited abstract, one passage per sentence, as the evidence.
* `retrieval_recall` measures ATLAS's BM25 retriever over the full
  5,183-abstract corpus: is the gold abstract / rationale sentence in the top k?

Data: https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz
(extract to data/external/scifact/). Licence: CC BY-NC 2.0.
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path

from ..retrieval import BM25Index
from ..schemas import Chunk
from .common import pct, save_experiment

SCIFACT_DIR = Path("data/external/scifact/data")
DEFAULT_OUT = Path("data/external/scifact_dev_150.jsonl")
LABEL_MAP = {"SUPPORT": "supported", "CONTRADICT": "contradicted", None: "unsupported"}


def _load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def _load(scifact_dir: Path) -> tuple[list[dict], dict[int, dict]]:
    claims_path = scifact_dir / "claims_dev.jsonl"
    if not claims_path.exists():
        raise FileNotFoundError(
            f"{claims_path} not found. Download the SciFact release and extract it to "
            "data/external/scifact/ (see atlas/experiments/scifact.py)."
        )
    claims = _load_jsonl(claims_path)
    corpus = {d["doc_id"]: d for d in _load_jsonl(scifact_dir / "corpus.jsonl")}
    return claims, corpus


def _claim_label(claim: dict) -> str | None:
    labels = {e["label"] for docs in claim["evidence"].values() for e in docs}
    if len(labels) > 1:
        raise ValueError("mixed labels")
    return labels.pop() if labels else None


def build_benchmark(
    per_class: int = 50,
    seed: int = 13,
    scifact_dir: Path = SCIFACT_DIR,
    out: Path = DEFAULT_OUT,
) -> Path:
    """Write a class-balanced sample of SciFact dev claims as ATLAS JSONL."""
    claims, corpus = _load(scifact_dir)
    by_label: dict[str, list[dict]] = {v: [] for v in LABEL_MAP.values()}
    for c in claims:
        label = _claim_label(c)
        if label is None:
            doc_ids = c["cited_doc_ids"][:1]
            rationale: list[int] = []
        else:
            if len(c["evidence"]) != 1:
                continue  # keep single-abstract claims so evidence is one document
            doc_key, entries = next(iter(c["evidence"].items()))
            doc_ids = [int(doc_key)]
            rationale = sorted({s + 1 for e in entries for s in e["sentences"]})
        if not doc_ids or doc_ids[0] not in corpus:
            continue
        doc = corpus[doc_ids[0]]
        by_label[LABEL_MAP[label]].append(
            {
                "id": f"scifact-{c['id']}",
                "claim": c["claim"],
                "evidence": [s.strip() for s in doc["abstract"]],
                "label": LABEL_MAP[label],
                "rationale": rationale,
                "note": f"doc {doc['doc_id']}: {doc['title'][:80]}",
            }
        )

    rng = random.Random(seed)
    sample: list[dict] = []
    for label, items in by_label.items():
        if len(items) < per_class:
            raise ValueError(f"only {len(items)} {label} claims available")
        sample.extend(rng.sample(items, per_class))
    rng.shuffle(sample)  # mix labels so batches are not single-class

    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        for item in sample:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")
    return out


def retrieval_recall(
    ks: tuple[int, ...] = (1, 4, 8, 20),
    scifact_dir: Path = SCIFACT_DIR,
    save: bool = True,
) -> dict:
    """BM25 recall@k over the full SciFact corpus, one chunk per sentence window.

    Chunks are built from abstracts the same way ATLAS chunks web pages, so this
    approximates how often the right passage reaches the verifier.
    """
    from ..retrieval import chunk_text

    claims, corpus = _load(scifact_dir)
    chunks: list[Chunk] = []
    for doc in corpus.values():
        text = f"{doc['title']}. " + " ".join(doc["abstract"])
        for i, piece in enumerate(chunk_text(text, 700, 120), 1):
            chunks.append(Chunk(id=f"D{doc['doc_id']}-{i}", source_id=doc["doc_id"], text=piece))

    started = time.perf_counter()
    index = BM25Index(chunks)
    build_s = time.perf_counter() - started

    max_k = max(ks)
    doc_hits = {k: 0 for k in ks}
    sent_hits = {k: 0 for k in ks}
    n = 0
    query_times = []
    for c in claims:
        label = _claim_label(c)
        if label is None:
            continue  # NEI claims have no gold evidence
        n += 1
        gold_docs = {int(d) for d in c["evidence"]}
        gold_sents = [
            " ".join(corpus[int(d)]["abstract"][s].split())
            for d, entries in c["evidence"].items()
            for e in entries
            for s in e["sentences"]
        ]
        t0 = time.perf_counter()
        top = index.top_k(c["claim"], max_k)
        query_times.append(time.perf_counter() - t0)
        for k in ks:
            retrieved = [chunks[i] for i, _ in top[:k]]
            if any(ch.source_id in gold_docs for ch in retrieved):
                doc_hits[k] += 1
            if any(s[:60] in ch.text for ch in retrieved for s in gold_sents if ch.source_id in gold_docs):
                sent_hits[k] += 1

    result = {
        "corpus_docs": len(corpus),
        "chunks": len(chunks),
        "queries": n,
        "doc_recall": {f"@{k}": round(doc_hits[k] / n, 4) for k in ks},
        "rationale_recall": {f"@{k}": round(sent_hits[k] / n, 4) for k in ks},
        "index_build_seconds": round(build_s, 2),
        "mean_query_ms": round(1000 * sum(query_times) / len(query_times), 2),
    }
    if save:
        lines = [
            "# Retrieval recall on SciFact (BM25, full corpus)",
            "",
            f"{n} SciFact dev claims with gold evidence; corpus of {len(corpus)} abstracts "
            f"split into {len(chunks)} chunks. No API calls.",
            "",
            "| k | Gold abstract in top k | Gold rationale sentence in top k |",
            "|---|---|---|",
        ]
        for k in ks:
            lines.append(f"| {k} | {pct(result['doc_recall'][f'@{k}'])} | {pct(result['rationale_recall'][f'@{k}'])} |")
        lines += ["", f"Index build {result['index_build_seconds']}s, mean query {result['mean_query_ms']} ms."]
        result["output_dir"] = str(save_experiment("retrieval_scifact", result, "\n".join(lines) + "\n"))
    return result

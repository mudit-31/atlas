from atlas.retrieval import BM25Index, build_chunks, chunk_text, tokenize
from atlas.schemas import Claim, Source


def test_tokenize_drops_stopwords_and_keeps_numbers():
    assert tokenize("The farm has 420 megawatts and 1,500.5 units") == ["farm", "420", "megawatts", "1,500.5", "units"]


def test_chunk_text_respects_size_and_overlaps():
    text = " ".join(f"Sentence number {i} talks about topic {i}." for i in range(60))
    chunks = chunk_text(text, max_chars=200, overlap=50)
    assert len(chunks) > 5
    assert all(len(c) <= 260 for c in chunks)  # max + overlap tail
    # consecutive chunks share some words thanks to overlap
    assert set(chunks[0].split()[-3:]) & set(chunks[1].split()[:12])


def test_chunk_text_strips_markdown_links_and_images():
    chunks = chunk_text("See ![logo](x.png) the [report](https://a.b/c) here.")
    assert chunks == ["See the report here."]


def test_build_chunks_falls_back_to_snippet():
    chunks = build_chunks([Source(id=3, snippet="Only a snippet.")])
    assert [(c.id, c.text) for c in chunks] == [("S3-C1", "Only a snippet.")]


def test_bm25_ranks_relevant_chunk_first_and_includes_cited_source():
    sources = [
        Source(id=1, content="The solar farm has a capacity of 420 megawatts."),
        Source(id=2, content="Wind auctions drew record bids in the North Sea."),
        Source(id=3, content="Bakery prices rose in the city centre."),
    ]
    index = BM25Index(build_chunks(sources))
    claim = Claim(id="C1", text="solar farm capacity 420 megawatts", cited_sources=[3])
    evidence = index.evidence_for(claim, k=2)
    assert evidence[0].source_id == 1
    # the cited source is always included, even if it scores zero
    assert 3 in {e.source_id for e in evidence}


def test_bm25_empty_index():
    assert BM25Index([]).evidence_for(Claim(id="C1", text="anything")) == []

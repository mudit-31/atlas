from atlas.claims import extract_claims, extract_claims_heuristic
from atlas.llm import LLMError
from atlas.schemas import Claim, ClaimVerdict, Evidence, Label
from atlas.scoring import summarize
from atlas.verify import judge_claims

from conftest import REPORT_BODY, FakeLLM


def test_extract_claims_filters_invalid_citations(settings):
    claims = extract_claims(FakeLLM(), settings, REPORT_BODY, {1, 2})
    assert [c.id for c in claims] == ["C1", "C2", "C3", "C4"]
    assert claims[1].cited_sources == [1]  # [9] is not a real source


def test_extract_claims_falls_back_to_heuristic_on_llm_error(settings):
    class Broken(FakeLLM):
        def generate_json(self, *a, **k):
            raise LLMError("quota")

    claims = extract_claims(Broken(), settings, REPORT_BODY, {1, 2})
    assert len(claims) == 4
    assert claims[0].text.startswith("Veltrix Energy opened")
    assert "[1]" not in claims[0].text


def test_heuristic_ignores_sources_section_and_uncited_text():
    claims = extract_claims_heuristic(REPORT_BODY, {1, 2}, limit=10)
    assert all("made-up" not in c.text for c in claims)
    assert all("future plans" not in c.text for c in claims)


def _item(cid, text, evidence=True):
    ev = [Evidence(chunk_id=f"S1-C{cid}", source_id=1, text="evidence")] if evidence else []
    return Claim(id=cid, text=text, cited_sources=[1]), ev


def test_judge_claims_batches_and_handles_missing_evidence():
    llm = FakeLLM()
    items = [
        _item("C1", "capacity of 420 megawatts"),
        _item("C2", "built in 1990"),
        _item("C3", "no evidence here", evidence=False),
        _item("C4", "power 150,000 homes"),
    ]
    verdicts = judge_claims(llm, "m", items, batch_size=2)
    assert [v.label for v in verdicts] == [
        Label.SUPPORTED, Label.CONTRADICTED, Label.UNSUPPORTED, Label.SUPPORTED,
    ]
    # 3 claims with evidence, batch size 2 -> 2 calls; no call for C3
    assert sum(1 for kind, _ in llm.calls if kind == "_VerdictBatch") == 2


def test_judge_claims_retries_skipped_claims():
    llm = FakeLLM(drop_claim="1990")
    items = [_item("C1", "capacity of 420 megawatts"), _item("C2", "built in 1990")]
    verdicts = judge_claims(llm, "m", items, batch_size=5)
    assert verdicts[1].label == Label.CONTRADICTED
    assert verdicts[1].error is None


def test_judge_claims_survives_llm_failure():
    class Broken(FakeLLM):
        def generate_json(self, *a, **k):
            raise LLMError("down")

    verdicts = judge_claims(Broken(), "m", [_item("C1", "x claim")], batch_size=5)
    assert verdicts[0].label == Label.UNSUPPORTED and verdicts[0].error == "no_verdict"


def _verdict(label, cited, used_source):
    ev = Evidence(chunk_id="S%d-C1" % used_source, source_id=used_source, text="t")
    return ClaimVerdict(
        claim=Claim(id="C", text="t", cited_sources=cited),
        label=label,
        confidence=0.8,
        evidence=[ev],
        cited_evidence_ids=[ev.chunk_id],
    )


def test_summarize_scores():
    s = summarize([
        _verdict(Label.SUPPORTED, [1], 1),
        _verdict(Label.PARTIALLY_SUPPORTED, [2], 1),  # backed by an uncited source
        _verdict(Label.UNSUPPORTED, [], 1),
        _verdict(Label.CONTRADICTED, [1], 1),
    ])
    assert s.total_claims == 4
    assert s.trust_score == 25.0  # (1 + 0.5 + 0 - 0.5) / 4
    assert s.citation_coverage == 0.75
    assert s.citation_accuracy == round(1 / 3, 3)
    assert s.counts == {"supported": 1, "partially_supported": 1, "unsupported": 1, "contradicted": 1}


def test_summarize_empty_and_floor():
    assert summarize([]).trust_score == 0.0
    assert summarize([_verdict(Label.CONTRADICTED, [1], 1)]).trust_score == 0.0

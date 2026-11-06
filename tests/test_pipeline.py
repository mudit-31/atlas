import json

from atlas.pipeline import Atlas, save_result, slugify
from atlas.render import markdown_to_html
from atlas.schemas import Label
from atlas.search import parse_results

from conftest import FakeLLM, FakeSearcher


def test_research_end_to_end(settings):
    llm, searcher = FakeLLM(), FakeSearcher()
    stages = []
    result = Atlas(settings, llm=llm, searcher=searcher).research("Halden solar farm?", progress=stages.append)

    assert searcher.queries == ["Halden solar farm?"]
    # one writer call, one extraction call, one verification batch
    assert [kind for kind, _ in llm.calls] == ["text", "_ExtractedClaims", "_VerdictBatch"]
    assert [model for _, model in llm.calls] == [
        settings.writer_model, settings.extractor_model, settings.verifier_model,
    ]
    assert [v.label for v in result.verdicts] == [
        Label.SUPPORTED, Label.SUPPORTED, Label.UNSUPPORTED, Label.CONTRADICTED,
    ]
    assert result.summary.total_claims == 4
    assert 0 <= result.summary.trust_score <= 100
    assert stages[0] == "Searching the web" and stages[-1] == "Scoring"

    # The Sources list is rebuilt from search results, not taken from the model.
    assert "made-up list" not in result.report_markdown
    assert "https://example.com/halden" in result.report_markdown


def test_verify_text_uses_given_text(settings):
    llm = FakeLLM()
    result = Atlas(settings, llm=llm, searcher=FakeSearcher()).verify_text(
        "The farm was built in 1990 [1].", "Halden solar farm"
    )
    assert "text" not in [kind for kind, _ in llm.calls]  # no report writing
    assert result.report_markdown == "The farm was built in 1990 [1]."


def test_save_result_writes_all_outputs(settings):
    result = Atlas(settings, llm=FakeLLM(), searcher=FakeSearcher()).research("Halden solar farm?")
    run_dir = save_result(result, settings.output_dir)
    assert {p.name for p in run_dir.iterdir()} == {"result.json", "report.md", "report.html"}
    data = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    assert data["summary"]["total_claims"] == 4
    md = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "ATLAS Verification" in md and "Trust score" in md
    page = (run_dir / "report.html").read_text(encoding="utf-8")
    assert "<title>ATLAS Report</title>" in page and "Contradicted" in page
    # second save in the same second gets a distinct folder
    assert save_result(result, settings.output_dir) != run_dir


def test_markdown_to_html_escapes_and_links():
    out = markdown_to_html("## Head\n- a <b>x</b> [1]\n\nText [link](https://x.y)")
    assert "<h3>Head</h3>" in out
    assert "&lt;b&gt;" in out
    assert 'href="#src-1"' in out
    assert '<a href="https://x.y"' in out


def test_slugify():
    assert slugify("What's NVIDIA's AI strategy?") == "whats-nvidias-ai-strategy"
    assert slugify("???") == "report"


def test_parse_results_dedupes_and_truncates():
    response = {
        "results": [
            {"title": "A", "url": "https://a", "content": "snip", "raw_content": "x" * 50},
            {"title": "A again", "url": "https://a", "content": "dup"},
            {"title": "B", "url": "https://b", "content": "snip b", "raw_content": None},
        ]
    }
    sources = parse_results(response, max_chars=10)
    assert [(s.id, s.title) for s in sources] == [(1, "A"), (2, "B")]
    assert len(sources[0].content) == 10
    assert sources[1].text == "snip b"

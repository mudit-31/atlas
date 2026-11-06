from collections import Counter

import pytest

from atlas.cli import build_parser, main
from atlas.evaluation.metrics import compute_metrics
from atlas.evaluation.runner import DEFAULT_DATASET, load_dataset, run_evaluation

from conftest import FakeLLM


def test_metrics_perfect_and_confusion():
    gold = ["supported", "contradicted", "unsupported", "partially_supported"]
    m = compute_metrics(gold, gold, [0.9, 0.9, 0.9, 0.9])
    assert m["accuracy"] == 1.0 and m["macro_f1"] == 1.0
    assert m["problem_detection"]["recall"] == 1.0
    assert m["calibration"]["accuracy_when_conf_ge_0_8"] == 1.0


def test_metrics_values():
    gold = ["supported", "supported", "contradicted", "unsupported"]
    pred = ["supported", "unsupported", "supported", "unsupported"]
    m = compute_metrics(gold, pred)
    assert m["accuracy"] == 0.5
    assert m["per_class"]["supported"] == {"precision": 0.5, "recall": 0.5, "f1": 0.5, "support": 2}
    assert m["confusion_matrix"]["contradicted"]["supported"] == 1
    # problem claims: gold bad = {2,3}; predicted bad = {1,3}
    assert m["problem_detection"] == {"precision": 0.5, "recall": 0.5, "f1": 0.5, "support": 2}


def test_metrics_length_mismatch():
    with pytest.raises(ValueError):
        compute_metrics(["supported"], [])


def test_seed_dataset_is_balanced():
    examples = load_dataset(DEFAULT_DATASET)
    assert len(examples) == 40
    assert set(Counter(e.label.value for e in examples).values()) == {10}


def test_run_evaluation_with_fake_llm(settings):
    result = run_evaluation(settings, limit=12, llm=FakeLLM())
    assert result["metrics"]["n"] == 12
    assert len(result["predictions"]) == 12
    out = result["output_dir"]
    from pathlib import Path

    assert (Path(out) / "report.md").read_text(encoding="utf-8").startswith("# ATLAS Verifier Evaluation")


def test_cli_parser_and_missing_key(monkeypatch, capsys):
    args = build_parser().parse_args(["research", "What is X?", "--max-sources", "3"])
    assert args.question == "What is X?" and args.max_sources == 3

    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr("atlas.config.load_dotenv", lambda *a, **k: None)
    assert main(["research", "What is X?"]) == 2
    assert "GOOGLE_API_KEY" in capsys.readouterr().err

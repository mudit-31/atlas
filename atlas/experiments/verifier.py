"""Repeated verifier evaluations with mean / standard deviation across runs."""

from __future__ import annotations

import statistics as st
from pathlib import Path

from ..evaluation.runner import run_evaluation
from ..schemas import LABEL_ORDER, Usage
from .common import EXPERIMENTS_DIR, experiment_settings, pct, save_experiment


def _ms(values: list[float]) -> dict:
    return {
        "mean": round(st.mean(values), 4),
        "sd": round(st.pstdev(values), 4) if len(values) > 1 else 0.0,
        "min": round(min(values), 4),
        "max": round(max(values), 4),
        "runs": [round(v, 4) for v in values],
    }


def verifier_runs(
    dataset: Path,
    name: str,
    model: str | None = None,
    runs: int = 3,
    batch_size: int | None = None,
    limit: int | None = None,
) -> dict:
    """Evaluate the verifier `runs` times without cache and aggregate metrics."""
    per_run = []
    for _ in range(runs):
        settings = experiment_settings(model=model, cache=False)
        if batch_size:
            settings.verify_batch_size = batch_size
        settings.eval_dir = EXPERIMENTS_DIR / name / "runs"
        run = run_evaluation(settings, dataset=dataset, limit=limit, usage=Usage())
        failed = sum(1 for p in run["predictions"] if p["error"])
        if failed:
            # A failed batch is filled with placeholder verdicts; never report it.
            raise RuntimeError(
                f"{failed} predictions had no verdict (quota or API failure) in {run['output_dir']}; "
                "run discarded."
            )
        per_run.append(run)
    return aggregate_runs(per_run, name, dataset)


def aggregate_existing(name: str) -> dict:
    """Aggregate every saved run under data/experiments/<name>/runs/."""
    import json

    paths = sorted((EXPERIMENTS_DIR / name / "runs").glob("*/results.json"))
    per_run = []
    for p in paths:
        run = json.loads(p.read_text(encoding="utf-8"))
        run["output_dir"] = str(p.parent)
        per_run.append(run)
    if not per_run:
        raise FileNotFoundError(f"no runs under {EXPERIMENTS_DIR / name / 'runs'}")
    if len({(r["dataset"], r["model"], r["batch_size"]) for r in per_run}) != 1:
        raise ValueError("runs differ in dataset, model or batch size")
    return aggregate_runs(per_run, name, Path(per_run[0]["dataset"]))


def aggregate_runs(per_run: list[dict], name: str, dataset: Path) -> dict:
    runs = len(per_run)
    m = [r["metrics"] for r in per_run]
    agg = {
        "accuracy": _ms([x["accuracy"] for x in m]),
        "macro_f1": _ms([x["macro_f1"] for x in m]),
        "lenient_accuracy": _ms([x["lenient"]["accuracy"] for x in m]),
        "lenient_macro_f1": _ms([x["lenient"]["macro_f1"] for x in m]),
        "problem_precision": _ms([x["problem_detection"]["precision"] for x in m]),
        "problem_recall": _ms([x["problem_detection"]["recall"] for x in m]),
        "problem_f1": _ms([x["problem_detection"]["f1"] for x in m]),
        "seconds_per_run": _ms([r["elapsed_seconds"] for r in per_run]),
        "calls_per_run": _ms([r["usage"]["llm_calls"] for r in per_run]),
        "prompt_tokens_per_run": _ms([r["usage"]["prompt_tokens"] for r in per_run]),
        "output_tokens_per_run": _ms([r["usage"]["output_tokens"] for r in per_run]),
        "per_class_f1": {
            label.value: _ms([x["per_class"][label.value]["f1"] for x in m]) for label in LABEL_ORDER
        },
    }
    if all("rationale_hit_rate" in x for x in m):
        agg["rationale_hit_rate"] = _ms([x["rationale_hit_rate"] for x in m])

    served = {}
    for r in per_run:
        for k, v in r["served_by"].items():
            served[k] = served.get(k, 0) + v
    result = {
        "dataset": str(dataset),
        "n": m[0]["n"],
        "model": per_run[0]["model"],
        "served_by": served,
        "batch_size": per_run[0]["batch_size"],
        "runs": runs,
        "aggregate": agg,
        "run_dirs": [r["output_dir"] for r in per_run],
        "confusion_matrices": [x["confusion_matrix"] for x in m],
    }

    def row(label: str, key: str, fmt=pct) -> str:
        a = agg[key]
        return f"| {label} | {fmt(a['mean'])} | {fmt(a['sd'])} | {', '.join(fmt(v) for v in a['runs'])} |"

    lines = [
        f"# Verifier evaluation: {Path(dataset).name}",
        "",
        f"- Model: `{result['model']}` (calls served by: {served})",
        f"- Examples: {result['n']} · runs: {runs} · batch size: {result['batch_size']} · cache off",
        "",
        "| Metric | Mean | SD | Runs |",
        "|---|---|---|---|",
        row("Accuracy (4-way)", "accuracy"),
        row("Macro F1 (4-way)", "macro_f1"),
        row("Accuracy (partial = supported)", "lenient_accuracy"),
        row("Macro F1 (partial = supported)", "lenient_macro_f1"),
        row("Problem-claim precision", "problem_precision"),
        row("Problem-claim recall", "problem_recall"),
        row("Problem-claim F1", "problem_f1"),
    ]
    if "rationale_hit_rate" in agg:
        lines.append(row("Rationale hit rate", "rationale_hit_rate"))
    num = lambda v: f"{v:.1f}"
    lines += [
        row("Seconds per run", "seconds_per_run", num),
        row("Gemini calls per run", "calls_per_run", num),
        "",
        "Per-label F1 (mean): "
        + ", ".join(f"{k} {pct(v['mean'])}" for k, v in agg["per_class_f1"].items()),
        "",
        "Run folders: " + ", ".join(f"`{d}`" for d in result["run_dirs"]),
    ]
    result["output_dir"] = str(save_experiment(name, result, "\n".join(lines) + "\n"))
    return result

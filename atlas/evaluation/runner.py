"""Run the verifier over a labelled dataset and write a results report.

Dataset format (JSON Lines), one example per line:

    {"id": "s01", "claim": "...", "evidence": ["passage", ...], "label": "supported"}

`label` is one of: supported, partially_supported, unsupported, contradicted.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from ..config import Settings
from ..llm import LLM, GeminiLLM
from ..schemas import LABEL_ORDER, Claim, Evidence, Label, Usage
from ..verify import judge_claims
from .metrics import compute_metrics

logger = logging.getLogger(__name__)

DEFAULT_DATASET =Path(__file__).resolve().parents[2] / "data" / "benchmark" / "atlas_seed_v1.jsonl"


class Example(BaseModel):
    id: str
    claim: str
    evidence: list[str] = Field(default_factory=list)
    label: Label
    note: str = ""
    # Optional 1-based indexes into `evidence` of the gold rationale passages.
    rationale: list[int] = Field(default_factory=list)

    @field_validator("label", mode="before")
    @classmethod
    def _norm_label(cls, value: str) -> str:
        return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def load_dataset(path: Path) -> list[Example]:
    examples: list[Example] = []
    with open(path, encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            try:
                examples.append(Example.model_validate_json(line))
            except ValueError as exc:
                raise ValueError(f"{path}:{line_no}: invalid example: {exc}") from exc
    ids = [e.id for e in examples]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: example ids must be unique")
    return examples


def _to_items(examples: list[Example]) -> list[tuple[Claim, list[Evidence]]]:
    items = []
    for i, ex in enumerate(examples, 1):
        claim = Claim(id=f"C{i}", text=ex.claim)
        evidence = [
            Evidence(chunk_id=f"E{i}-{j}", source_id=j, text=text)
            for j, text in enumerate(ex.evidence, 1)
        ]
        items.append((claim, evidence))
    return items


def run_evaluation(
    settings: Settings,
    dataset: Path = DEFAULT_DATASET,
    limit: int | None = None,
    llm: LLM | None = None,
    usage: Usage | None = None,
    save: bool = True,
) -> dict:
    usage = usage or Usage()
    llm = llm if llm is not None else GeminiLLM(settings, usage)
    examples = load_dataset(dataset)
    if limit:
        examples = examples[:limit]
    if not examples:
        raise ValueError("The dataset is empty.")

    started = time.perf_counter()
    verdicts = judge_claims(llm, settings.verifier_model, _to_items(examples), settings.verify_batch_size)
    elapsed = round(time.perf_counter() - started, 2)

    gold = [e.label.value for e in examples]
    pred = [v.label.value for v in verdicts]
    metrics = compute_metrics(gold, pred, [v.confidence for v in verdicts])
    # Lenient view: "partially supported" counts as "supported". Useful for
    # datasets such as SciFact that have no partial label.
    lenient = [Label.SUPPORTED.value if p == Label.PARTIALLY_SUPPORTED.value else p for p in pred]
    metrics["lenient"] = compute_metrics(gold, lenient)

    predictions = []
    hits = scored = 0
    for e, v in zip(examples, verdicts):
        cited = [int(cid.rsplit("-", 1)[1]) for cid in v.cited_evidence_ids]
        hit = None
        if e.rationale and e.label == v.label and v.label != Label.UNSUPPORTED:
            hit = bool(set(cited) & set(e.rationale))
            scored += 1
            hits += hit
        predictions.append(
            {
                "id": e.id,
                "claim": e.claim,
                "gold": e.label.value,
                "pred": v.label.value,
                "confidence": v.confidence,
                "correct": e.label == v.label,
                "cited_passages": cited,
                "rationale_hit": hit,
                "rationale": v.rationale,
                "error": v.error,
            }
        )
    if scored:
        # Of correct supported/contradicted verdicts, how often the verifier
        # pointed at a gold rationale passage (right answer for the right reason).
        metrics["rationale_hit_rate"] = round(hits / scored, 4)
        metrics["rationale_scored"] = scored

    served_by = dict(usage.calls_by_model)
    if served_by and set(served_by) != {settings.verifier_model}:
        logger.warning("Some calls were served by fallback models: %s", served_by)
    result = {
        "dataset": str(dataset),
        "model": settings.verifier_model,
        "served_by": served_by,
        "batch_size": settings.verify_batch_size,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_seconds": elapsed,
        "usage": usage.model_dump(),
        "metrics": metrics,
        "predictions": predictions,
    }
    if save:
        result["output_dir"] = str(save_evaluation(result, settings.eval_dir))
    return result


def render_eval_markdown(result: dict) -> str:
    m = result["metrics"]
    labels = [label.value for label in LABEL_ORDER]
    short = {l: Label(l).display for l in labels}
    lines = [
        "# ATLAS Verifier Evaluation",
        "",
        f"- Dataset: `{result['dataset']}` ({m['n']} examples)",
        f"- Model: `{result['model']}` · batch size {result['batch_size']}",
        f"- Gemini calls: {result['usage']['llm_calls']} · time {result['elapsed_seconds']}s",
        "",
        "## Headline",
        "",
        f"| Accuracy | Macro F1 | Weighted F1 | Problem-claim precision | Problem-claim recall |",
        "|---|---|---|---|---|",
        f"| {m['accuracy']:.3f} | {m['macro_f1']:.3f} | {m['weighted_f1']:.3f} "
        f"| {m['problem_detection']['precision']:.3f} | {m['problem_detection']['recall']:.3f} |",
        "",
        "Problem claims = unsupported + contradicted, i.e. what ATLAS should flag.",
        "",
        "## Per label",
        "",
        "| Label | Precision | Recall | F1 | Support |",
        "|---|---|---|---|---|",
    ]
    for l in labels:
        c = m["per_class"][l]
        lines.append(f"| {short[l]} | {c['precision']:.3f} | {c['recall']:.3f} | {c['f1']:.3f} | {c['support']} |")
    lines += ["", "## Confusion matrix (rows = gold, columns = predicted)", ""]
    lines.append("| | " + " | ".join(short[l] for l in labels) + " |")
    lines.append("|---" * (len(labels) + 1) + "|")
    for g in labels:
        lines.append(f"| **{short[g]}** | " + " | ".join(str(m["confusion_matrix"][g][p]) for p in labels) + " |")
    if "calibration" in m:
        cal = m["calibration"]
        lines += [
            "",
            "## Confidence",
            "",
            f"- Mean confidence when correct: {cal['mean_conf_correct']:.2f}; when wrong: {cal['mean_conf_wrong']:.2f}",
            f"- Accuracy when confidence ≥ 0.8: {cal['accuracy_when_conf_ge_0_8']:.3f} "
            f"({cal['share_conf_ge_0_8']:.0%} of examples)",
        ]
    errors = [p for p in result["predictions"] if not p["correct"]]
    if errors:
        lines += ["", "## Mistakes", "", "| Id | Gold | Predicted | Claim | Rationale |", "|---|---|---|---|---|"]
        for p in errors:
            claim = p["claim"].replace("|", "\\|")
            why = (p["rationale"] or "").replace("|", "\\|")
            lines.append(f"| {p['id']} | {p['gold']} | {p['pred']} | {claim} | {why} |")
    return "\n".join(lines) + "\n"


def save_evaluation(result: dict, eval_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(eval_dir) / stamp
    suffix = 1
    while out.exists():
        suffix += 1
        out = Path(eval_dir) / f"{stamp}_{suffix}"
    out.mkdir(parents=True)
    (out / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "report.md").write_text(render_eval_markdown(result), encoding="utf-8")
    return out

"""Classification metrics in pure Python (no scikit-learn dependency)."""

from __future__ import annotations

from typing import Sequence

from ..schemas import LABEL_ORDER, Label

PROBLEM_LABELS = {Label.UNSUPPORTED.value, Label.CONTRADICTED.value}


def _safe_div(a: float, b: float) -> float:
    return a / b if b else 0.0


def _prf(tp: int, fp: int, fn: int) -> dict[str, float]:
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


def compute_metrics(
    gold: Sequence[str],
    pred: Sequence[str],
    confidences: Sequence[float] | None = None,
) -> dict:
    """Metrics for 4-way verdicts plus a binary "problem claim" view.

    The binary view treats unsupported + contradicted as the positive class:
    its recall is the share of bad claims ATLAS catches, its precision the
    share of flagged claims that really are bad.
    """
    if len(gold) != len(pred):
        raise ValueError("gold and pred must have the same length")
    labels = [label.value for label in LABEL_ORDER]
    n = len(gold)

    confusion = {g: {p: 0 for p in labels} for g in labels}
    for g, p in zip(gold, pred):
        confusion[g][p] += 1

    per_class = {}
    for label in labels:
        tp = confusion[label][label]
        fp = sum(confusion[g][label] for g in labels if g != label)
        fn = sum(confusion[label][p] for p in labels if p != label)
        per_class[label] = {**_prf(tp, fp, fn), "support": tp + fn}

    present = [l for l in labels if per_class[l]["support"] > 0]
    macro_f1 = _safe_div(sum(per_class[l]["f1"] for l in present), len(present))
    weighted_f1 = _safe_div(sum(per_class[l]["f1"] * per_class[l]["support"] for l in labels), n)
    accuracy = _safe_div(sum(confusion[l][l] for l in labels), n)

    g_bad = [g in PROBLEM_LABELS for g in gold]
    p_bad = [p in PROBLEM_LABELS for p in pred]
    tp = sum(g and p for g, p in zip(g_bad, p_bad))
    fp = sum((not g) and p for g, p in zip(g_bad, p_bad))
    fn = sum(g and not p for g, p in zip(g_bad, p_bad))
    binary = {**_prf(tp, fp, fn), "support": sum(g_bad)}

    result = {
        "n": n,
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class": per_class,
        "confusion_matrix": confusion,
        "problem_detection": binary,
    }

    if confidences is not None and n:
        correct = [c for c, g, p in zip(confidences, gold, pred) if g == p]
        wrong = [c for c, g, p in zip(confidences, gold, pred) if g != p]
        high = [(g == p) for c, g, p in zip(confidences, gold, pred) if c >= 0.8]
        result["calibration"] = {
            "mean_conf_correct": round(_safe_div(sum(correct), len(correct)), 4),
            "mean_conf_wrong": round(_safe_div(sum(wrong), len(wrong)), 4),
            "accuracy_when_conf_ge_0_8": round(_safe_div(sum(high), len(high)), 4),
            "share_conf_ge_0_8": round(_safe_div(len(high), n), 4),
        }
    return result

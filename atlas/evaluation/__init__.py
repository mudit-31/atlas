"""Evaluation of the claim verifier against labelled benchmark data."""

from .metrics import compute_metrics
from .runner import load_dataset, run_evaluation

__all__ = ["compute_metrics", "load_dataset", "run_evaluation"]

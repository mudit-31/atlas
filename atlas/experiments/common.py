"""Helpers shared by experiments."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..config import Settings

EXPERIMENTS_DIR = Path("data/experiments")


def experiment_settings(model: str | None = None, cache: bool = True) -> Settings:
    """Settings for measurement runs.

    Fallback models are disabled so every number comes from the model it is
    attributed to; a quota error fails the run instead of silently switching.
    """
    settings = Settings.from_env()
    settings.fallback_models = []
    settings.cache_enabled = cache
    if model:
        settings.verifier_model = model
    return settings


def save_experiment(name: str, result: dict, summary_md: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = EXPERIMENTS_DIR / name / stamp
    suffix = 1
    while out.exists():
        suffix += 1
        out = EXPERIMENTS_DIR / name / f"{stamp}_{suffix}"
    out.mkdir(parents=True)
    result = {**result, "created_at": datetime.now().isoformat(timespec="seconds")}
    (out / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "summary.md").write_text(summary_md, encoding="utf-8")
    return out


def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{100 * x:.1f}%"

"""Runtime configuration, read from environment variables (and `.env`)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return value.strip() if value and value.strip() else default


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {value!r}") from exc


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None or not value.strip():
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass
class Settings:
    """All tunable knobs for ATLAS. Defaults favour the Gemini free tier."""

    google_api_key: str | None = None
    tavily_api_key: str | None = None

    # Models. The writer and verifier need judgement; extraction is simple
    # and runs on the cheapest model. Fallbacks are tried, in order, when a
    # model is unavailable or its daily quota is used up.
    writer_model: str = "gemini-3.5-flash-lite"
    verifier_model: str = "gemini-3.5-flash-lite"
    extractor_model: str = "gemini-3.5-flash-lite"
    fallback_models: list[str] = field(
        default_factory=lambda: ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
    )
    # Optional Gemini "thinking level" (e.g. "low"). Empty = model default.
    thinking_level: str = ""

    # Client-side throttle so bursts never trip the per-minute limit.
    gemini_rpm: int = 10
    max_retries: int = 4

    # Search: one "basic" Tavily query (1 credit) per research run.
    max_sources: int = 6
    search_depth: str = "basic"
    max_source_chars: int = 8000
    writer_chars_per_source: int = 3000

    # Claims and verification.
    max_claims: int = 25
    verify_batch_size: int = 12
    evidence_per_claim: int = 4
    chunk_chars: int = 700
    chunk_overlap: int = 120

    # Storage.
    cache_enabled: bool = True
    cache_dir: Path = Path("data/cache")
    output_dir: Path = Path("data/outputs")
    eval_dir: Path = Path("data/eval_runs")

    # Request timeout for Gemini calls, in seconds.
    request_timeout: float = 120.0

    @classmethod
    def from_env(cls, env_file: str | os.PathLike[str] | None = None) -> "Settings":
        """Build settings from environment variables, loading `.env` first."""
        load_dotenv(env_file, override=False)
        return cls(
            google_api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
            tavily_api_key=os.getenv("TAVILY_API_KEY"),
            writer_model=_env_str("ATLAS_WRITER_MODEL", cls.writer_model),
            verifier_model=_env_str("ATLAS_VERIFIER_MODEL", cls.verifier_model),
            extractor_model=_env_str("ATLAS_EXTRACTOR_MODEL", cls.extractor_model),
            fallback_models=_env_list(
                "ATLAS_FALLBACK_MODELS", ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
            ),
            thinking_level=_env_str("ATLAS_THINKING_LEVEL", ""),
            gemini_rpm=_env_int("GEMINI_RPM", cls.gemini_rpm),
            max_retries=_env_int("ATLAS_MAX_RETRIES", cls.max_retries),
            max_sources=_env_int("ATLAS_MAX_SOURCES", cls.max_sources),
            search_depth=_env_str("ATLAS_SEARCH_DEPTH", cls.search_depth),
            max_source_chars=_env_int("ATLAS_MAX_SOURCE_CHARS", cls.max_source_chars),
            writer_chars_per_source=_env_int(
                "ATLAS_WRITER_CHARS_PER_SOURCE", cls.writer_chars_per_source
            ),
            max_claims=_env_int("ATLAS_MAX_CLAIMS", cls.max_claims),
            verify_batch_size=_env_int("ATLAS_VERIFY_BATCH_SIZE", cls.verify_batch_size),
            evidence_per_claim=_env_int("ATLAS_EVIDENCE_PER_CLAIM", cls.evidence_per_claim),
            chunk_chars=_env_int("ATLAS_CHUNK_CHARS", cls.chunk_chars),
            chunk_overlap=_env_int("ATLAS_CHUNK_OVERLAP", cls.chunk_overlap),
            cache_enabled=_env_bool("ATLAS_CACHE", True),
            cache_dir=Path(_env_str("ATLAS_CACHE_DIR", str(cls.cache_dir))),
            output_dir=Path(_env_str("ATLAS_OUTPUT_DIR", str(cls.output_dir))),
            eval_dir=Path(_env_str("ATLAS_EVAL_DIR", str(cls.eval_dir))),
            request_timeout=_env_float("ATLAS_REQUEST_TIMEOUT", cls.request_timeout),
        )

    def require_gemini(self) -> str:
        if not self.google_api_key:
            raise ConfigError(
                "GOOGLE_API_KEY is not set. Get a free key at https://aistudio.google.com/apikey "
                "and put it in your .env file."
            )
        return self.google_api_key

    def require_tavily(self) -> str:
        if not self.tavily_api_key:
            raise ConfigError(
                "TAVILY_API_KEY is not set. Get a free key (1,000 credits/month) at "
                "https://app.tavily.com and put it in your .env file."
            )
        return self.tavily_api_key


class ConfigError(RuntimeError):
    """Raised when a required setting (usually an API key) is missing."""

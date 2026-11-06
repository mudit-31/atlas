"""Gemini client wrapper: rate limiting, retries, model fallback and caching.

Everything that talks to Gemini goes through `GeminiLLM`, so free-tier
protections live in one place:

* a client-side requests-per-minute throttle,
* retries that honour the server's `retryDelay` on 429s,
* automatic fallback to the next model when one is missing or its daily
  quota is exhausted,
* a disk cache keyed on the full request, so identical calls are free.
"""

from __future__ import annotations

import json
import logging
import random
import re
import threading
import time
from collections import deque
from typing import Callable, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from .cache import DiskCache, make_key
from .config import Settings
from .schemas import Usage

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """Raised when no model could produce a usable response."""


class LLM(Protocol):
    """The interface the pipeline depends on (real or fake)."""

    def generate_text(self, prompt: str, *, model: str, system: str | None = None) -> str: ...

    def generate_json(
        self, prompt: str, schema: type[T], *, model: str, system: str | None = None
    ) -> T: ...


class RateLimiter:
    """Sliding-window limiter: at most `rpm` calls in any 60-second window."""

    def __init__(
        self,
        rpm: int,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.rpm = max(0, rpm)
        self._clock = clock
        self._sleep = sleep
        self._calls: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        if self.rpm <= 0:
            return
        while True:
            with self._lock:
                now = self._clock()
                while self._calls and now - self._calls[0] >= 60.0:
                    self._calls.popleft()
                if len(self._calls) < self.rpm:
                    self._calls.append(now)
                    return
                wait = 60.0 - (now - self._calls[0]) + 0.05
            logger.info("Rate limit: waiting %.1fs before the next Gemini call.", wait)
            self._sleep(wait)


_RETRY_DELAY_RE = re.compile(r"^(\d+(?:\.\d+)?)s$")


def _error_details(exc: Exception) -> str:
    details = getattr(exc, "details", None)
    try:
        return json.dumps(details, default=str)
    except (TypeError, ValueError):
        return str(details)


def retry_delay_from_error(exc: Exception) -> float | None:
    """Extract Google's suggested `retryDelay` (e.g. "37s") from an API error."""
    details = getattr(exc, "details", None)
    stack = [details]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            delay = item.get("retryDelay")
            if isinstance(delay, str):
                match = _RETRY_DELAY_RE.match(delay.strip())
                if match:
                    return float(match.group(1))
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return None


def is_daily_quota_error(exc: Exception) -> bool:
    text = _error_details(exc) + str(getattr(exc, "message", ""))
    return "PerDay" in text or "per day" in text.lower()


def _is_model_unavailable(exc: Exception) -> bool:
    code = getattr(exc, "code", None)
    if code == 404:
        return True
    message = str(getattr(exc, "message", "") or "").lower()
    return code in (400, 403) and "model" in message and (
        "not found" in message or "not supported" in message or "unsupported" in message
        or "does not have access" in message
    )


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text


class GeminiLLM:
    """Production `LLM` backed by the google-genai SDK."""

    def __init__(
        self,
        settings: Settings,
        usage: Usage | None = None,
        client: object | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.settings = settings
        self.usage = usage if usage is not None else Usage()
        self._sleep = sleep
        self.limiter = RateLimiter(settings.gemini_rpm, sleep=sleep)
        self.cache = DiskCache(settings.cache_dir, "llm", enabled=settings.cache_enabled)
        if client is None:
            from google import genai
            from google.genai import types

            client = genai.Client(
                api_key=settings.require_gemini(),
                http_options=types.HttpOptions(timeout=int(settings.request_timeout * 1000)),
            )
        self.client = client
        # Models that failed permanently in this process (missing / out of
        # daily quota) are skipped for the rest of the run.
        self._dead_models: set[str] = set()

    # ------------------------------------------------------------------ public

    def generate_text(self, prompt: str, *, model: str, system: str | None = None) -> str:
        return self._generate(prompt, model=model, system=system, schema=None)

    def generate_json(
        self, prompt: str, schema: type[T], *, model: str, system: str | None = None
    ) -> T:
        last_error: Exception | None = None
        for attempt in range(2):
            raw = self._generate(
                prompt, model=model, system=system, schema=schema, bust_cache=attempt > 0
            )
            try:
                return schema.model_validate_json(_strip_fences(raw))
            except ValidationError as exc:
                last_error = exc
                logger.warning("Model returned JSON that failed validation; retrying once.")
        raise LLMError(f"Model output did not match {schema.__name__}: {last_error}")

    # ---------------------------------------------------------------- internal

    def _model_chain(self, model: str) -> list[str]:
        chain = [model] + [m for m in self.settings.fallback_models if m != model]
        return [m for m in chain if m not in self._dead_models]

    def _build_config(self, model: str, system: str | None, schema: type[BaseModel] | None):
        from google.genai import types

        kwargs: dict = {}
        if system:
            kwargs["system_instruction"] = system
        if schema is not None:
            kwargs["response_mime_type"] = "application/json"
            kwargs["response_schema"] = schema
        if self.settings.thinking_level and model.startswith("gemini-3"):
            kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_level=self.settings.thinking_level
            )
        return types.GenerateContentConfig(**kwargs)

    def _generate(
        self,
        prompt: str,
        *,
        model: str,
        system: str | None,
        schema: type[BaseModel] | None,
        bust_cache: bool = False,
    ) -> str:
        schema_sig = schema.model_json_schema() if schema is not None else None
        key = make_key("gemini", model, system, prompt, schema_sig, self.settings.thinking_level)
        if not bust_cache:
            cached = self.cache.get(key)
            if cached is not None:
                self.usage.llm_cache_hits += 1
                return cached["text"]

        chain = self._model_chain(model)
        if not chain:
            raise LLMError("Every configured Gemini model is unavailable or out of quota.")

        last_error: Exception | None = None
        for candidate in chain:
            try:
                text = self._call_with_retries(candidate, prompt, system, schema)
            except _SkipModel as skip:
                last_error = skip.cause
                self._dead_models.add(candidate)
                logger.warning("Model %s unavailable (%s); trying next model.", candidate, skip.reason)
                continue
            if candidate != model:
                logger.info("Served by fallback model %s.", candidate)
            self.cache.set(key, {"text": text, "model": candidate})
            return text
        raise LLMError(f"All Gemini models failed. Last error: {last_error}")

    def _call_with_retries(
        self, model: str, prompt: str, system: str | None, schema: type[BaseModel] | None
    ) -> str:
        from google.genai import errors

        config = self._build_config(model, system, schema)
        attempts = self.settings.max_retries + 1
        for attempt in range(attempts):
            self.limiter.acquire()
            try:
                response = self.client.models.generate_content(
                    model=model, contents=prompt, config=config
                )
            except errors.APIError as exc:
                code = getattr(exc, "code", None)
                if code == 429 and is_daily_quota_error(exc):
                    raise _SkipModel("daily quota exhausted", exc) from exc
                if _is_model_unavailable(exc):
                    raise _SkipModel(f"HTTP {code}", exc) from exc
                retryable = code in (408, 429) or (isinstance(code, int) and code >= 500)
                if not retryable or attempt == attempts - 1:
                    if code == 429:
                        raise _SkipModel("rate limited after retries", exc) from exc
                    raise LLMError(f"Gemini call failed ({code}): {exc}") from exc
                delay = retry_delay_from_error(exc) or self._backoff(attempt)
                logger.warning("Gemini HTTP %s; retrying in %.1fs (%d/%d).", code, delay, attempt + 1, attempts - 1)
                self._sleep(delay)
                continue
            except (ConnectionError, TimeoutError, OSError) as exc:
                if attempt == attempts - 1:
                    raise LLMError(f"Network error calling Gemini: {exc}") from exc
                delay = self._backoff(attempt)
                logger.warning("Network error (%s); retrying in %.1fs.", exc, delay)
                self._sleep(delay)
                continue

            self._record_usage(model, response)
            text = getattr(response, "text", None)
            if not text:
                reason = _finish_reason(response)
                raise LLMError(f"Gemini returned no text (finish reason: {reason}).")
            return text
        raise LLMError("Gemini retries exhausted.")  # pragma: no cover

    @staticmethod
    def _backoff(attempt: int) -> float:
        return min(60.0, 2.0 * (2**attempt)) + random.uniform(0, 1)

    def _record_usage(self, model: str, response: object) -> None:
        self.usage.llm_calls += 1
        self.usage.calls_by_model[model] = self.usage.calls_by_model.get(model, 0) + 1
        meta = getattr(response, "usage_metadata", None)
        if meta is not None:
            self.usage.prompt_tokens += int(getattr(meta, "prompt_token_count", 0) or 0)
            self.usage.output_tokens += int(getattr(meta, "candidates_token_count", 0) or 0)


class _SkipModel(Exception):
    def __init__(self, reason: str, cause: Exception) -> None:
        super().__init__(reason)
        self.reason = reason
        self.cause = cause


def _finish_reason(response: object) -> str:
    try:
        return str(response.candidates[0].finish_reason)  # type: ignore[attr-defined]
    except (AttributeError, IndexError, TypeError):
        feedback = getattr(response, "prompt_feedback", None)
        return str(feedback) if feedback else "unknown"

from types import SimpleNamespace

import pytest
from google.genai import errors
from pydantic import BaseModel

from atlas.llm import GeminiLLM, LLMError, RateLimiter, is_daily_quota_error, retry_delay_from_error


def _ok(text):
    return SimpleNamespace(
        text=text, usage_metadata=SimpleNamespace(prompt_token_count=10, candidates_token_count=4)
    )


def _err(code, status="", message="", details=None):
    body = {"error": {"code": code, "status": status, "message": message, "details": details or []}}
    cls = errors.ClientError if code < 500 else errors.ServerError
    return cls(code, body)


class ScriptedClient:
    """Fake google-genai client: pops a scripted outcome per call."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []
        self.models = self

    def generate_content(self, *, model, contents, config):
        self.calls.append(model)
        outcome = self.script.pop(0)
        if callable(outcome):
            outcome = outcome(model)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def make(settings, script):
    sleeps = []
    client = ScriptedClient(script)
    llm = GeminiLLM(settings, client=client, sleep=sleeps.append)
    return llm, client, sleeps


RETRY_DETAILS = [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "7s"}]
DAILY_DETAILS = [
    {"@type": "type.googleapis.com/google.rpc.QuotaFailure",
     "violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}
]


def test_retry_delay_and_daily_detection():
    assert retry_delay_from_error(_err(429, details=RETRY_DETAILS)) == 7.0
    assert retry_delay_from_error(_err(429)) is None
    assert is_daily_quota_error(_err(429, details=DAILY_DETAILS))
    assert not is_daily_quota_error(_err(429, details=RETRY_DETAILS))


def test_retries_429_using_server_delay(settings):
    llm, client, sleeps = make(settings, [_err(429, "RESOURCE_EXHAUSTED", details=RETRY_DETAILS), _ok("hi")])
    assert llm.generate_text("p", model="m1") == "hi"
    assert sleeps == [7.0]
    assert llm.usage.llm_calls == 1 and llm.usage.prompt_tokens == 10


def test_daily_quota_falls_back_to_next_model(settings):
    settings.fallback_models = ["m2"]
    llm, client, _ = make(settings, [_err(429, details=DAILY_DETAILS), _ok("from m2"), _ok("again")])
    assert llm.generate_text("p", model="m1") == "from m2"
    assert client.calls == ["m1", "m2"]
    # m1 is now known dead: the next (uncached) call goes straight to m2
    assert llm.generate_text("other", model="m1") == "again"
    assert client.calls[-1] == "m2"


def test_missing_model_falls_back(settings):
    settings.fallback_models = ["m2"]
    llm, client, _ = make(settings, [_err(404, "NOT_FOUND", "models/m1 is not found"), _ok("ok")])
    assert llm.generate_text("p", model="m1") == "ok"
    assert llm.usage.calls_by_model == {"m2": 1}


def test_non_retryable_error_raises(settings):
    llm, _, _ = make(settings, [_err(400, "INVALID_ARGUMENT", "bad request")])
    with pytest.raises(LLMError):
        llm.generate_text("p", model="m1")


def test_server_errors_retry_then_succeed(settings):
    llm, client, sleeps = make(settings, [_err(503, "UNAVAILABLE"), _ok("ok")])
    assert llm.generate_text("p", model="m1") == "ok"
    assert len(sleeps) == 1


def test_cache_avoids_second_call(settings):
    llm, client, _ = make(settings, [_ok("cached")])
    assert llm.generate_text("p", model="m1") == "cached"
    assert llm.generate_text("p", model="m1") == "cached"
    assert len(client.calls) == 1 and llm.usage.llm_cache_hits == 1


class Item(BaseModel):
    name: str
    count: int


def test_generate_json_parses_and_retries_bad_json(settings):
    llm, client, _ = make(settings, [_ok("not json"), _ok('```json\n{"name": "a", "count": 2}\n```')])
    assert llm.generate_json("p", Item, model="m1") == Item(name="a", count=2)
    assert len(client.calls) == 2


def test_empty_response_raises(settings):
    llm, _, _ = make(settings, [SimpleNamespace(text=None, usage_metadata=None, candidates=[])])
    with pytest.raises(LLMError):
        llm.generate_text("p", model="m1")


def test_rate_limiter_waits_when_window_full():
    now = [0.0]
    sleeps = []

    def sleep(seconds):
        sleeps.append(seconds)
        now[0] += seconds

    limiter = RateLimiter(2, clock=lambda: now[0], sleep=sleep)
    limiter.acquire()
    limiter.acquire()
    limiter.acquire()  # third call in the same minute must wait ~60s
    assert len(sleeps) == 1 and 59 < sleeps[0] <= 61

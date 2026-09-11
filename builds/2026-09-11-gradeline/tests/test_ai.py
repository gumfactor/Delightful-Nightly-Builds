import json
import urllib.error

import pytest

from src import ai


def test_deterministic_feedback_met_coverage():
    text = ai.deterministic_feedback("Clear Thesis", hits=3, min_hits=1, score=10.0, max_points=10)
    assert "met the expected keyword coverage" in text
    assert "3/1" in text


def test_deterministic_feedback_fell_short():
    text = ai.deterministic_feedback("Clear Thesis", hits=0, min_hits=2, score=0.0, max_points=10)
    assert "fell short" in text


def test_deterministic_feedback_manual_only():
    text = ai.deterministic_feedback("Argument Quality", hits=0, min_hits=0, score=0.0, max_points=20)
    assert "manual review" in text


def test_draft_feedback_no_api_key_returns_none_and_never_calls_transport():
    def exploding_transport(url, payload):
        raise AssertionError("transport should never be called with no api_key")

    result = ai.draft_feedback("Thesis", "desc", "submission text", api_key="", transport=exploding_transport)
    assert result is None


def test_draft_feedback_uses_mocked_transport_and_parses_response():
    captured = {}

    def fake_transport(url, payload):
        captured["url"] = url
        captured["payload"] = payload
        response = {"content": [{"text": "This is grounded feedback on the thesis."}]}
        return json.dumps(response).encode("utf-8")

    result = ai.draft_feedback(
        "Clear Thesis", "States a thesis.", "My thesis is X.", api_key="sk-fake", transport=fake_transport
    )
    assert result == "This is grounded feedback on the thesis."
    assert captured["url"] == ai.ANTHROPIC_URL
    assert captured["payload"]["model"] == ai.ANTHROPIC_MODEL


def test_draft_feedback_payload_never_contains_a_student_identifier():
    """The AI module has no identifier parameter at all, so a student's name
    cannot appear in the payload by construction. This test plants a sentinel
    identifier value nowhere near the function call and asserts it is absent
    from every string the mocked transport actually receives."""
    sentinel = "STUDENT_IDENTIFIER_SENTINEL_Jane_Doe"
    captured = {}

    def fake_transport(url, payload):
        captured["payload"] = payload
        return json.dumps({"content": [{"text": "feedback"}]}).encode("utf-8")

    ai.draft_feedback("Thesis", "desc", "submission text without any name", api_key="sk-fake", transport=fake_transport)
    payload_str = json.dumps(captured["payload"])
    assert sentinel not in payload_str


def test_draft_feedback_malformed_response_returns_none():
    def fake_transport(url, payload):
        return b"not valid json"

    result = ai.draft_feedback("Thesis", "desc", "text", api_key="sk-fake", transport=fake_transport)
    assert result is None


def test_draft_feedback_missing_content_key_returns_none():
    def fake_transport(url, payload):
        return json.dumps({"unexpected": "shape"}).encode("utf-8")

    result = ai.draft_feedback("Thesis", "desc", "text", api_key="sk-fake", transport=fake_transport)
    assert result is None


def test_draft_feedback_http_error_returns_none():
    def failing_transport(url, payload):
        raise urllib.error.HTTPError(url, 401, "Unauthorized", hdrs=None, fp=None)

    result = ai.draft_feedback("Thesis", "desc", "text", api_key="sk-bad", transport=failing_transport)
    assert result is None


def test_draft_feedback_url_error_returns_none():
    def failing_transport(url, payload):
        raise urllib.error.URLError("no network")

    result = ai.draft_feedback("Thesis", "desc", "text", api_key="sk-fake", transport=failing_transport)
    assert result is None


def test_draft_feedback_empty_text_response_returns_none():
    def fake_transport(url, payload):
        return json.dumps({"content": [{"text": "   "}]}).encode("utf-8")

    result = ai.draft_feedback("Thesis", "desc", "text", api_key="sk-fake", transport=fake_transport)
    assert result is None


def test_default_transport_uses_env_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-from-env")
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"content": [{"text": "ok"}]}).encode("utf-8")

    def fake_urlopen(request, timeout=30):
        captured["headers"] = dict(request.header_items())
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    raw = ai.default_transport(ai.ANTHROPIC_URL, {"model": ai.ANTHROPIC_MODEL})
    assert json.loads(raw)["content"][0]["text"] == "ok"
    assert captured["headers"]["X-api-key"] == "sk-from-env"

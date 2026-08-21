import json
import urllib.error

from src import ai_review

RAW_SECRET = "sk-ant-thisistherealsecretvalue1234567890"


class FakeResponse:
    def __init__(self, body: dict):
        self._body = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return self._body


def _ai_body(verdict: str, rationale: str = "looks like a real key format") -> dict:
    return {
        "content": [
            {"type": "text", "text": f"VERDICT: {verdict}\nRATIONALE: {rationale}"}
        ]
    }


def test_no_api_key_uses_deterministic_fallback_and_makes_zero_network_calls(monkeypatch):
    called = {"count": 0}

    def fail_if_called(*args, **kwargs):
        called["count"] += 1
        raise AssertionError("urlopen should never be called with no API key")

    monkeypatch.setattr(ai_review.urllib.request, "urlopen", fail_if_called)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    result = ai_review.review_finding(
        pattern_name="AWS Access Key ID", file_ext=".py", entropy=4.2,
        masked_snippet="AWS_KEY = '[REDACTED]'", api_key=None,
    )

    assert called["count"] == 0
    assert result["source"] == "fallback"
    assert result["verdict"] == "likely_secret"


def test_generic_pattern_fallback_verdict_is_uncertain(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("urlopen should never be called with no API key")

    monkeypatch.setattr(ai_review.urllib.request, "urlopen", fail_if_called)
    result = ai_review.review_finding(
        pattern_name="Generic High-Entropy Match (my_token)", file_ext=".py",
        entropy=4.5, masked_snippet="my_token = '[REDACTED]'", api_key=None,
    )
    assert result["verdict"] == "uncertain"
    assert result["source"] == "fallback"


def test_ai_request_payload_never_contains_the_raw_secret(monkeypatch):
    captured_requests = []

    def fake_urlopen(request, timeout=None):
        captured_requests.append(request)
        return FakeResponse(_ai_body("likely_placeholder"))

    monkeypatch.setattr(ai_review.urllib.request, "urlopen", fake_urlopen)

    masked_snippet = f"api_key = '[REDACTED]'  # was 'api_key = {RAW_SECRET[:0]}'"
    ai_review.review_finding(
        pattern_name="Anthropic API Key", file_ext=".py", entropy=4.8,
        masked_snippet=masked_snippet, api_key="fake-test-key-not-real",
    )

    assert len(captured_requests) == 1
    body_text = captured_requests[0].data.decode("utf-8")
    assert RAW_SECRET not in body_text


def test_ai_response_parsed_into_verdict_and_rationale(monkeypatch):
    def fake_urlopen(request, timeout=None):
        return FakeResponse(_ai_body("likely_secret", "matches a known key prefix"))

    monkeypatch.setattr(ai_review.urllib.request, "urlopen", fake_urlopen)

    result = ai_review.review_finding(
        pattern_name="Anthropic API Key", file_ext=".py", entropy=4.8,
        masked_snippet="api_key = '[REDACTED]'", api_key="fake-test-key-not-real",
    )

    assert result["verdict"] == "likely_secret"
    assert result["rationale"] == "matches a known key prefix"
    assert result["source"] == "ai"


def test_network_failure_falls_back_gracefully(monkeypatch):
    def raise_url_error(request, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(ai_review.urllib.request, "urlopen", raise_url_error)

    result = ai_review.review_finding(
        pattern_name="AWS Access Key ID", file_ext=".py", entropy=4.2,
        masked_snippet="AWS_KEY = '[REDACTED]'", api_key="fake-test-key-not-real",
    )

    assert result["source"] == "fallback"
    assert result["verdict"] == "likely_secret"

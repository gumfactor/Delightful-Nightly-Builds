import json
import urllib.error
import urllib.request

import pytest

from src import ai_client


class FakeResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def read(self):
        return self._body


def test_missing_api_key_raises():
    with pytest.raises(ai_client.MissingAPIKeyError):
        ai_client.call_claude("prompt", api_key=None)


def test_missing_api_key_raises_for_empty_string():
    with pytest.raises(ai_client.MissingAPIKeyError):
        ai_client.call_claude("prompt", api_key="")


def test_call_claude_success(monkeypatch):
    payload = {"content": [{"type": "text", "text": "hello from claude"}]}

    def fake_urlopen(request, timeout=None):
        return FakeResponse(payload)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    result = ai_client.call_claude("prompt", api_key="fake-key")
    assert result == "hello from claude"


def test_call_claude_sends_correct_headers_and_no_key_in_url(monkeypatch):
    payload = {"content": [{"type": "text", "text": "ok"}]}
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["request"] = request
        return FakeResponse(payload)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    ai_client.call_claude("prompt", api_key="secret-key-123")

    sent_request = captured["request"]
    assert sent_request.get_header("X-api-key") == "secret-key-123"
    assert sent_request.full_url == ai_client.ANTHROPIC_API_URL
    assert "secret-key-123" not in sent_request.full_url


def test_call_claude_http_error(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.HTTPError(ai_client.ANTHROPIC_API_URL, 500, "Server Error", None, None)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(ai_client.AnthropicAPIError):
        ai_client.call_claude("prompt", api_key="fake-key")


def test_call_claude_url_error(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.URLError("simulated DNS failure")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(ai_client.AnthropicAPIError):
        ai_client.call_claude("prompt", api_key="fake-key")


def test_call_claude_malformed_response_raises(monkeypatch):
    def fake_urlopen(request, timeout=None):
        return FakeResponse({"unexpected": "shape"})

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(ai_client.AnthropicAPIError):
        ai_client.call_claude("prompt", api_key="fake-key")


def test_call_claude_empty_text_raises(monkeypatch):
    payload = {"content": [{"type": "text", "text": ""}]}

    def fake_urlopen(request, timeout=None):
        return FakeResponse(payload)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(ai_client.AnthropicAPIError):
        ai_client.call_claude("prompt", api_key="fake-key")

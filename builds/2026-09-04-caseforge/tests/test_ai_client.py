import json
import urllib.error

from src import ai_client


def test_call_claude_returns_none_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    calls = {"count": 0}

    def fake_urlopen(*args, **kwargs):
        calls["count"] += 1
        raise AssertionError("urlopen should never be called with no API key")

    monkeypatch.setattr(ai_client.urllib.request, "urlopen", fake_urlopen)
    result = ai_client.call_claude("hello")
    assert result is None
    assert calls["count"] == 0


class _FakeResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_call_claude_returns_text_on_success(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    def fake_urlopen(request, timeout=None):
        return _FakeResponse({"content": [{"type": "text", "text": "A polished paragraph."}]})

    monkeypatch.setattr(ai_client.urllib.request, "urlopen", fake_urlopen)
    result = ai_client.call_claude("hello")
    assert result == "A polished paragraph."


def test_call_claude_joins_multiple_text_blocks(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    def fake_urlopen(request, timeout=None):
        return _FakeResponse(
            {"content": [{"type": "text", "text": "Part one. "}, {"type": "text", "text": "Part two."}]}
        )

    monkeypatch.setattr(ai_client.urllib.request, "urlopen", fake_urlopen)
    result = ai_client.call_claude("hello")
    assert result == "Part one. Part two."


def test_call_claude_returns_none_on_http_error(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    def fake_urlopen(request, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(ai_client.urllib.request, "urlopen", fake_urlopen)
    result = ai_client.call_claude("hello")
    assert result is None


def test_call_claude_returns_none_on_malformed_response(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    def fake_urlopen(request, timeout=None):
        return _FakeResponse({"unexpected": "shape"})

    monkeypatch.setattr(ai_client.urllib.request, "urlopen", fake_urlopen)
    result = ai_client.call_claude("hello")
    assert result is None


def test_call_claude_returns_none_on_empty_text(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    def fake_urlopen(request, timeout=None):
        return _FakeResponse({"content": [{"type": "text", "text": "   "}]})

    monkeypatch.setattr(ai_client.urllib.request, "urlopen", fake_urlopen)
    result = ai_client.call_claude("hello")
    assert result is None


def test_call_claude_sends_api_key_header(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sentinel-key")
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["headers"] = request.headers
        return _FakeResponse({"content": [{"type": "text", "text": "ok"}]})

    monkeypatch.setattr(ai_client.urllib.request, "urlopen", fake_urlopen)
    ai_client.call_claude("hello")
    # urllib.request.Request lower-cases header keys' first letter capitalization internally.
    assert captured["headers"].get("X-api-key") == "sentinel-key"

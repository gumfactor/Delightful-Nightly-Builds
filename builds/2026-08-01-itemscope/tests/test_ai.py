import json
import urllib.error

import pytest

from itemscope import ai
from itemscope.stats import ItemStats


def _flagged_item() -> ItemStats:
    return ItemStats(
        item_id="item_1",
        p_value=0.98,
        discrimination=-0.1,
        discrimination_note=None,
        flags=["too_easy", "negative_discrimination"],
    )


def test_template_fallback_used_when_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    def _fail_if_called(*args, **kwargs):
        raise AssertionError("network call must not happen with no API key")

    monkeypatch.setattr(ai.urllib.request, "urlopen", _fail_if_called)

    text, source = ai.generate_item_suggestion(_flagged_item())

    assert source == "template"
    assert len(text) > 0
    assert "miskeyed" in text or "confusing" in text


def test_template_fallback_covers_all_flag_types():
    item = ItemStats(
        item_id="item_2",
        p_value=0.5,
        discrimination=0.4,
        discrimination_note=None,
        flags=[],
    )
    text, source = ai.generate_item_suggestion(item, api_key=None)
    assert source == "template"
    assert text == "No issues detected for this item."


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_ai_path_used_when_key_provided_and_call_succeeds(monkeypatch):
    fake_body = json.dumps(
        {"content": [{"type": "text", "text": "Retire this item — it is too easy."}]}
    ).encode("utf-8")

    def _fake_urlopen(request, timeout=None):
        assert request.headers.get("X-api-key") == "test-key-123" or request.headers.get(
            "X-Api-Key"
        ) == "test-key-123"
        return _FakeResponse(fake_body)

    monkeypatch.setattr(ai.urllib.request, "urlopen", _fake_urlopen)

    text, source = ai.generate_item_suggestion(_flagged_item(), api_key="test-key-123")

    assert source == "ai"
    assert text == "Retire this item — it is too easy."


def test_ai_path_falls_back_to_template_on_network_error(monkeypatch):
    def _raise_url_error(request, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(ai.urllib.request, "urlopen", _raise_url_error)

    text, source = ai.generate_item_suggestion(_flagged_item(), api_key="test-key-123")

    assert source == "template"
    assert len(text) > 0


def test_ai_path_falls_back_to_template_on_malformed_response(monkeypatch):
    def _fake_urlopen(request, timeout=None):
        return _FakeResponse(b"not valid json")

    monkeypatch.setattr(ai.urllib.request, "urlopen", _fake_urlopen)

    text, source = ai.generate_item_suggestion(_flagged_item(), api_key="test-key-123")

    assert source == "template"

import io
import json
import urllib.error

import pytest

from src import ai_enrich


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_no_api_key_makes_zero_network_calls(monkeypatch):
    def _fail_if_called(*args, **kwargs):
        raise AssertionError("urlopen should never be called without an api_key")

    monkeypatch.setattr("src.ai_enrich.urllib.request.urlopen", _fail_if_called)
    assert ai_enrich.enrich_chunk("some text", api_key=None) is None
    assert ai_enrich.enrich_chunk("some text", api_key="") is None


def test_empty_text_makes_zero_network_calls(monkeypatch):
    def _fail_if_called(*args, **kwargs):
        raise AssertionError("urlopen should never be called with empty text")

    monkeypatch.setattr("src.ai_enrich.urllib.request.urlopen", _fail_if_called)
    assert ai_enrich.enrich_chunk("", api_key="fake-key") is None


def test_successful_response_is_parsed(monkeypatch):
    body = {
        "content": [
            {"text": json.dumps({"summary": "A short summary.", "tags": ["Stress", "Empathy"]})}
        ]
    }
    payload = json.dumps(body).encode("utf-8")

    def _fake_urlopen(request, timeout=None):
        return _FakeResponse(payload)

    monkeypatch.setattr("src.ai_enrich.urllib.request.urlopen", _fake_urlopen)
    result = ai_enrich.enrich_chunk("some grant text", api_key="fake-key")
    assert result == {"summary": "A short summary.", "tags": ["stress", "empathy"]}


def test_malformed_inner_json_falls_back_to_none(monkeypatch):
    body = {"content": [{"text": "not valid json"}]}
    payload = json.dumps(body).encode("utf-8")

    def _fake_urlopen(request, timeout=None):
        return _FakeResponse(payload)

    monkeypatch.setattr("src.ai_enrich.urllib.request.urlopen", _fake_urlopen)
    assert ai_enrich.enrich_chunk("text", api_key="fake-key") is None


def test_missing_content_key_falls_back_to_none(monkeypatch):
    payload = json.dumps({"unexpected": "shape"}).encode("utf-8")

    def _fake_urlopen(request, timeout=None):
        return _FakeResponse(payload)

    monkeypatch.setattr("src.ai_enrich.urllib.request.urlopen", _fake_urlopen)
    assert ai_enrich.enrich_chunk("text", api_key="fake-key") is None


def test_non_string_summary_or_non_list_tags_rejected(monkeypatch):
    body = {"content": [{"text": json.dumps({"summary": 123, "tags": ["ok"]})}]}
    payload = json.dumps(body).encode("utf-8")

    def _fake_urlopen(request, timeout=None):
        return _FakeResponse(payload)

    monkeypatch.setattr("src.ai_enrich.urllib.request.urlopen", _fake_urlopen)
    assert ai_enrich.enrich_chunk("text", api_key="fake-key") is None


def test_network_error_falls_back_to_none(monkeypatch):
    def _raise_url_error(request, timeout=None):
        raise urllib.error.URLError("simulated network failure")

    monkeypatch.setattr("src.ai_enrich.urllib.request.urlopen", _raise_url_error)
    assert ai_enrich.enrich_chunk("text", api_key="fake-key") is None


def test_response_body_not_json_falls_back_to_none(monkeypatch):
    def _fake_urlopen(request, timeout=None):
        return _FakeResponse(b"not json at all")

    monkeypatch.setattr("src.ai_enrich.urllib.request.urlopen", _fake_urlopen)
    assert ai_enrich.enrich_chunk("text", api_key="fake-key") is None

import json

import pytest

from src import ai_briefing


class FakeResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._body


ITEMS = [
    {"title": "example.com", "category": "registration", "urgency": "Overdue"},
    {"title": "Business License", "category": "license", "urgency": "Due This Week"},
    {"title": "Cottage Insurance", "category": "insurance", "urgency": "Healthy"},
]


def test_no_api_key_makes_zero_network_calls(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    call_count = {"n": 0}

    def fake_urlopen(*args, **kwargs):
        call_count["n"] += 1
        raise AssertionError("should not be called without an API key")

    monkeypatch.setattr("src.ai_briefing.urllib.request.urlopen", fake_urlopen)
    text, used_ai = ai_briefing.generate_briefing(ITEMS)
    assert call_count["n"] == 0
    assert used_ai is False
    assert "example.com" in text or "overdue" in text.lower()


def test_deterministic_briefing_mentions_overdue_and_due_this_week(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    text, used_ai = ai_briefing.generate_briefing(ITEMS)
    assert used_ai is False
    assert "overdue" in text.lower()


def test_deterministic_briefing_all_healthy():
    healthy_items = [{"title": "example.com", "category": "registration", "urgency": "Healthy"}]
    text, used_ai = ai_briefing.generate_briefing(healthy_items)
    assert used_ai is False
    assert "nothing needs attention" in text.lower()


def test_successful_api_call_uses_ai_text(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-testing")

    def fake_urlopen(request, timeout=None):
        return FakeResponse({"content": [{"text": "Handle the overdue domain renewal first."}]})

    monkeypatch.setattr("src.ai_briefing.urllib.request.urlopen", fake_urlopen)
    text, used_ai = ai_briefing.generate_briefing(ITEMS)
    assert used_ai is True
    assert text == "Handle the overdue domain renewal first."


def test_api_failure_falls_back_to_deterministic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-testing")

    def fake_urlopen(request, timeout=None):
        raise ConnectionError("network unreachable")

    monkeypatch.setattr("src.ai_briefing.urllib.request.urlopen", fake_urlopen)
    text, used_ai = ai_briefing.generate_briefing(ITEMS)
    assert used_ai is False
    assert "overdue" in text.lower()


def test_empty_api_response_text_falls_back_to_deterministic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-for-testing")

    def fake_urlopen(request, timeout=None):
        return FakeResponse({"content": [{"text": ""}]})

    monkeypatch.setattr("src.ai_briefing.urllib.request.urlopen", fake_urlopen)
    text, used_ai = ai_briefing.generate_briefing(ITEMS)
    assert used_ai is False

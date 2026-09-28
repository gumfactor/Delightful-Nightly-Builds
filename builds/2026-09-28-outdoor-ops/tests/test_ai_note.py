import json

import pytest

from src import ai_note

SUMMARY = {
    "best_running_day": "2026-09-30", "best_running_score": 92.0,
    "worst_running_day": "2026-10-01", "worst_running_score": 55.0,
    "running_limiting_factor": "aqi",
    "best_golf_day": "2026-09-30", "best_golf_score": 96.0,
    "worst_golf_day": "2026-09-29", "worst_golf_score": 40.0,
    "golf_limiting_factor": "precip",
}


def test_deterministic_note_mentions_best_and_worst_days():
    note = ai_note.deterministic_note(SUMMARY)
    assert "2026-09-30" in note
    assert "2026-10-01" in note
    assert "2026-09-29" in note


def test_generate_note_uses_fallback_when_no_api_key():
    def raising_transport(key, body):
        raise AssertionError("transport must not be called with no API key")

    note = ai_note.generate_note(SUMMARY, api_key=None, transport=raising_transport)
    assert note == ai_note.deterministic_note(SUMMARY)


def test_generate_note_uses_transport_when_key_present():
    def fake_transport(key, body):
        assert key == "test-key"
        return json.dumps({"content": [{"type": "text", "text": "Run Wednesday, skip Tuesday for golf."}]})

    note = ai_note.generate_note(SUMMARY, api_key="test-key", transport=fake_transport)
    assert note == "Run Wednesday, skip Tuesday for golf."


def test_generate_note_falls_back_on_transport_error():
    def raising_transport(key, body):
        raise ConnectionError("network unreachable")

    note = ai_note.generate_note(SUMMARY, api_key="test-key", transport=raising_transport)
    assert note == ai_note.deterministic_note(SUMMARY)


def test_generate_note_falls_back_on_malformed_response():
    def bad_transport(key, body):
        return "not json"

    note = ai_note.generate_note(SUMMARY, api_key="test-key", transport=bad_transport)
    assert note == ai_note.deterministic_note(SUMMARY)


def test_generate_note_falls_back_on_empty_content():
    def empty_transport(key, body):
        return json.dumps({"content": []})

    note = ai_note.generate_note(SUMMARY, api_key="test-key", transport=empty_transport)
    assert note == ai_note.deterministic_note(SUMMARY)


def test_generate_note_reads_env_var_when_api_key_not_passed(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    calls = []

    def fake_transport(key, body):
        calls.append(key)
        return json.dumps({"content": [{"type": "text", "text": "note"}]})

    note = ai_note.generate_note(SUMMARY, transport=fake_transport)
    assert calls == ["env-key"]
    assert note == "note"

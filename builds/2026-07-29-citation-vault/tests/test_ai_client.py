import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
import ai_client


@pytest.fixture(autouse=True)
def clear_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


def test_suggest_tags_no_key_uses_deterministic_fallback(monkeypatch):
    calls = []

    def spy_request(payload):
        calls.append(payload)
        raise AssertionError("should not be called without an API key")

    tags = ai_client.suggest_tags(
        "Stress Reactivity and Empathy in Forensic Populations",
        "We examine cortisol reactivity and empathic accuracy in offenders.",
        request_fn=spy_request,
    )
    assert calls == []
    assert len(tags) > 0
    assert all(t.islower() for t in tags)


def test_suggest_tags_with_key_success(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    def fake_request(payload):
        return json.dumps({"content": [{"text": "stress, empathy, cortisol"}]}).encode()

    tags = ai_client.suggest_tags("Title", "Abstract", request_fn=fake_request)
    assert tags == ["stress", "empathy", "cortisol"]


def test_suggest_tags_network_error_falls_back(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    def failing_request(payload):
        raise OSError("network down")

    tags = ai_client.suggest_tags(
        "Psychopathy and Decision Making", "abstract text here", request_fn=failing_request
    )
    assert len(tags) > 0


def test_suggest_tags_malformed_response_falls_back(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    def bad_request(payload):
        return b"not json"

    tags = ai_client.suggest_tags("Neuroscience Paper Title", "abstract", request_fn=bad_request)
    assert len(tags) > 0


def test_suggest_tags_empty_response_falls_back(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    def empty_request(payload):
        return json.dumps({"content": [{"text": ""}]}).encode()

    tags = ai_client.suggest_tags("Affective Neuroscience Study", "long abstract about stress", request_fn=empty_request)
    assert len(tags) > 0


def test_deterministic_tags_filters_stopwords():
    tags = ai_client._deterministic_tags(
        "The Effect of the Stress on the Brain and the Body",
        "This study examines the effect of stress on brain and body responses.",
    )
    assert "the" not in tags
    assert "and" not in tags


def test_resurface_rationale_no_key_deterministic():
    old = {"title": "Old Paper", "id": 1}
    new = {"title": "New Paper", "id": 2}
    text = ai_client.resurface_rationale(old, new, ["stress", "cortisol"])
    assert "Old Paper" in text or "stress" in text
    assert "New Paper" in text


def test_resurface_rationale_with_key_success(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    def fake_request(payload):
        return json.dumps({"content": [{"text": "Both examine cortisol reactivity in similar populations."}]}).encode()

    old = {"title": "Old Paper", "id": 1}
    new = {"title": "New Paper", "id": 2}
    text = ai_client.resurface_rationale(old, new, ["cortisol"], request_fn=fake_request)
    assert text == "Both examine cortisol reactivity in similar populations."


def test_resurface_rationale_network_error_falls_back(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    def failing_request(payload):
        raise OSError("timeout")

    old = {"title": "Old Paper", "id": 1}
    new = {"title": "New Paper", "id": 2}
    text = ai_client.resurface_rationale(old, new, ["stress"], request_fn=failing_request)
    assert "New Paper" in text

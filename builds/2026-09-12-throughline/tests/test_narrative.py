import json

import pytest

from src import narrative


def make_cluster(label="stress / cortisol", papers=None, keywords=None):
    return {
        "id": 1,
        "label": label,
        "keywords": keywords or ["stress", "cortisol"],
        "papers": papers
        if papers is not None
        else [
            {"title": "Paper One", "year": 2019, "citation_count": 10, "abstract": "About stress."},
            {"title": "Paper Two", "year": 2021, "citation_count": 5, "abstract": "About cortisol."},
        ],
        "narrative": None,
        "narrative_source": None,
    }


def test_deterministic_narrative_includes_key_facts():
    cluster = make_cluster()
    text = narrative.deterministic_narrative(cluster)
    assert "stress / cortisol" in text
    assert "2019" in text and "2021" in text
    assert "15 total citations" in text
    assert "Paper One" in text and "Paper Two" in text


def test_deterministic_narrative_handles_missing_years():
    cluster = make_cluster(papers=[{"title": "Undated Paper", "year": None, "citation_count": 0, "abstract": None}])
    text = narrative.deterministic_narrative(cluster)
    assert "year unknown" in text
    assert "0 total citations" in text


def test_generate_narrative_without_ai_flag_returns_deterministic():
    cluster = make_cluster()

    def transport_should_not_be_called(url, headers, body):
        raise AssertionError("transport must not be called when use_ai=False")

    text, source = narrative.generate_narrative(cluster, use_ai=False, transport=transport_should_not_be_called)
    assert source == "deterministic"
    assert text == narrative.deterministic_narrative(cluster)


def test_generate_narrative_ai_requested_but_no_api_key_falls_back(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    cluster = make_cluster()

    def transport_should_not_be_called(url, headers, body):
        raise AssertionError("transport must not be called with no API key")

    text, source = narrative.generate_narrative(cluster, use_ai=True, transport=transport_should_not_be_called)
    assert source == "deterministic"


def test_generate_narrative_ai_success(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
    cluster = make_cluster()

    captured = {}

    def fake_transport(url, headers, body):
        captured["url"] = url
        captured["headers"] = headers
        captured["body"] = json.loads(body)
        return json.dumps({"content": [{"type": "text", "text": "A synthesized narrative."}]}).encode()

    text, source = narrative.generate_narrative(cluster, use_ai=True, transport=fake_transport)
    assert source == "ai"
    assert text == "A synthesized narrative."
    assert captured["url"] == narrative.AI_URL
    assert captured["headers"]["x-api-key"] == "test-key-123"
    assert captured["body"]["model"] == narrative.AI_MODEL


def test_generate_narrative_ai_network_error_falls_back(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
    cluster = make_cluster()

    import urllib.error

    def failing_transport(url, headers, body):
        raise urllib.error.URLError("connection reset")

    text, source = narrative.generate_narrative(cluster, use_ai=True, transport=failing_transport)
    assert source == "deterministic"
    assert text == narrative.deterministic_narrative(cluster)


def test_generate_narrative_ai_malformed_response_falls_back(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
    cluster = make_cluster()

    def bad_json_transport(url, headers, body):
        return b"not valid json"

    text, source = narrative.generate_narrative(cluster, use_ai=True, transport=bad_json_transport)
    assert source == "deterministic"


def test_generate_narrative_ai_empty_text_falls_back(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-123")
    cluster = make_cluster()

    def empty_text_transport(url, headers, body):
        return json.dumps({"content": [{"type": "text", "text": "   "}]}).encode()

    text, source = narrative.generate_narrative(cluster, use_ai=True, transport=empty_text_transport)
    assert source == "deterministic"

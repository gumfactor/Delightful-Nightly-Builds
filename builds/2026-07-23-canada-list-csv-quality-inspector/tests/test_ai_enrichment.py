import json
from unittest.mock import MagicMock, patch

from src import ai_enrichment


def _mock_response(body_dict):
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value.read.return_value = json.dumps(body_dict).encode("utf-8")
    return mock_cm


def test_is_ai_available_false_when_no_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert ai_enrichment.is_ai_available() is False


def test_is_ai_available_true_when_key_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    assert ai_enrichment.is_ai_available() is True


def test_confirm_duplicate_cluster_fallback_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    confirmed, reasoning = ai_enrichment.confirm_duplicate_cluster(["Acme Co", "Acme Corp"])
    assert confirmed is None
    assert "not configured" in reasoning


@patch("src.ai_enrichment.urllib.request.urlopen")
def test_confirm_duplicate_cluster_parses_yes(mock_urlopen, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    mock_urlopen.return_value = _mock_response(
        {"content": [{"text": "CONFIRMED: yes | REASON: Same address and phone number."}]}
    )
    confirmed, reasoning = ai_enrichment.confirm_duplicate_cluster(["Acme Co", "Acme Corp"])
    assert confirmed is True
    assert "Same address" in reasoning
    mock_urlopen.assert_called_once()


@patch("src.ai_enrichment.urllib.request.urlopen")
def test_confirm_duplicate_cluster_parses_no(mock_urlopen, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    mock_urlopen.return_value = _mock_response(
        {"content": [{"text": "CONFIRMED: no | REASON: Different cities entirely."}]}
    )
    confirmed, reasoning = ai_enrichment.confirm_duplicate_cluster(["Acme Co", "Acme West"])
    assert confirmed is False
    assert "Different cities" in reasoning


@patch("src.ai_enrichment.urllib.request.urlopen")
def test_confirm_duplicate_cluster_handles_unparseable_response(mock_urlopen, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    mock_urlopen.return_value = _mock_response({"content": [{"text": "I'm not sure."}]})
    confirmed, reasoning = ai_enrichment.confirm_duplicate_cluster(["Acme Co", "Acme Corp"])
    assert confirmed is None
    assert "Could not parse" in reasoning


@patch("src.ai_enrichment.urllib.request.urlopen", side_effect=TimeoutError("timed out"))
def test_confirm_duplicate_cluster_handles_network_failure(mock_urlopen, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    confirmed, reasoning = ai_enrichment.confirm_duplicate_cluster(["Acme Co", "Acme Corp"])
    assert confirmed is None
    assert "AI call failed" in reasoning


def test_suggest_ownership_status_mapping_fallback_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    suggestion, reasoning = ai_enrichment.suggest_ownership_status_mapping(
        "partially-canadian", ["canadian-owned", "foreign-owned", "unknown"]
    )
    assert suggestion is None
    assert "not configured" in reasoning


@patch("src.ai_enrichment.urllib.request.urlopen")
def test_suggest_ownership_status_mapping_parses_valid_suggestion(mock_urlopen, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    mock_urlopen.return_value = _mock_response(
        {"content": [{"text": "SUGGESTION: unknown | REASON: Partial ownership is ambiguous."}]}
    )
    suggestion, reasoning = ai_enrichment.suggest_ownership_status_mapping(
        "partially-canadian", ["canadian-owned", "foreign-owned", "unknown"]
    )
    assert suggestion == "unknown"
    assert "ambiguous" in reasoning


@patch("src.ai_enrichment.urllib.request.urlopen")
def test_suggest_ownership_status_mapping_rejects_non_canonical_suggestion(mock_urlopen, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    mock_urlopen.return_value = _mock_response(
        {"content": [{"text": "SUGGESTION: partially-canadian | REASON: made up value"}]}
    )
    suggestion, reasoning = ai_enrichment.suggest_ownership_status_mapping(
        "partially-canadian", ["canadian-owned", "foreign-owned", "unknown"]
    )
    assert suggestion is None


@patch("src.ai_enrichment.urllib.request.urlopen")
def test_call_claude_returns_none_on_malformed_body(mock_urlopen, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    mock_urlopen.return_value = _mock_response({"unexpected": "shape"})
    result = ai_enrichment._call_claude("hello")
    assert result is None

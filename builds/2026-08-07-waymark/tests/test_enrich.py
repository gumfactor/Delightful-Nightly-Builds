"""Tests for optional Claude Haiku enrichment. All Anthropic HTTP calls are mocked."""

from __future__ import annotations

import json
import urllib.error
from unittest.mock import MagicMock, patch

from src import enrich


def _commit():
    return {
        "subject": "refactor!: switch to plugin renderer",
        "body": "Because the old renderer could not support new export formats.",
        "files_changed": 5,
        "insertions": 120,
        "deletions": 40,
    }


def test_is_available_false_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert enrich.is_available() is False


def test_is_available_true_with_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")
    assert enrich.is_available() is True


@patch("src.enrich.urllib.request.urlopen")
def test_enrich_commit_makes_zero_network_calls_without_key(mock_urlopen, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    try:
        enrich.enrich_commit(_commit())
    except enrich.EnrichmentError:
        pass
    mock_urlopen.assert_not_called()


@patch("src.enrich.urllib.request.urlopen")
def test_enrich_commit_returns_text_from_successful_response(mock_urlopen):
    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps(
        {"content": [{"type": "text", "text": "Switched to a plugin-based renderer for export flexibility."}]}
    ).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    result = enrich.enrich_commit(_commit(), api_key="sk-test-key")
    assert "plugin-based renderer" in result


@patch("src.enrich.urllib.request.urlopen")
def test_enrich_commit_raises_on_network_error(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.URLError("connection refused")
    try:
        enrich.enrich_commit(_commit(), api_key="sk-test-key")
        assert False, "expected EnrichmentError"
    except enrich.EnrichmentError:
        pass


@patch("src.enrich.urllib.request.urlopen")
def test_enrich_commit_raises_when_response_has_no_text(mock_urlopen):
    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps({"content": []}).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    try:
        enrich.enrich_commit(_commit(), api_key="sk-test-key")
        assert False, "expected EnrichmentError"
    except enrich.EnrichmentError:
        pass


def test_enrich_commit_raises_without_api_key_argument_or_env(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    try:
        enrich.enrich_commit(_commit())
        assert False, "expected EnrichmentError"
    except enrich.EnrichmentError:
        pass


@patch("src.enrich.urllib.request.urlopen")
def test_enrich_commit_sends_expected_model(mock_urlopen):
    fake_response = MagicMock()
    fake_response.read.return_value = json.dumps(
        {"content": [{"type": "text", "text": "A summary."}]}
    ).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    enrich.enrich_commit(_commit(), api_key="sk-test-key")

    sent_request = mock_urlopen.call_args[0][0]
    payload = json.loads(sent_request.data.decode("utf-8"))
    assert payload["model"] == "claude-haiku-4-5"
    assert sent_request.headers.get("X-api-key") == "sk-test-key"

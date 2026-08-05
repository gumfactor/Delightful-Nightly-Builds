"""Tests for the optional Claude Haiku commentary layer — never calls the real API."""

import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import ai  # noqa: E402


def _mock_response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def test_no_api_key_returns_template_and_makes_no_network_call():
    with patch("ai.urllib.request.urlopen") as mock_urlopen:
        note = ai.generate_note(
            title="A Paper",
            abstract="An abstract.",
            previous_count=5,
            latest_count=8,
            latest_date="2026-08-05",
            api_key=None,
        )
    mock_urlopen.assert_not_called()
    assert "5" in note and "8" in note and "2026-08-05" in note


def test_successful_call_returns_model_text():
    payload = {"content": [{"type": "text", "text": "Likely gaining traction from a recent review citing it."}]}
    with patch("ai.urllib.request.urlopen", return_value=_mock_response(payload)):
        note = ai.generate_note(
            title="A Paper",
            abstract="An abstract.",
            previous_count=5,
            latest_count=8,
            latest_date="2026-08-05",
            api_key="fake-key",
        )
    assert note == "Likely gaining traction from a recent review citing it."


def test_failed_call_falls_back_to_template():
    with patch("ai.urllib.request.urlopen", side_effect=urllib.error.URLError("no network")):
        note = ai.generate_note(
            title="A Paper",
            abstract="An abstract.",
            previous_count=5,
            latest_count=8,
            latest_date="2026-08-05",
            api_key="fake-key",
        )
    assert note == ai.fallback_note("A Paper", 5, 8, "2026-08-05")


def test_malformed_response_falls_back_to_template():
    response = MagicMock()
    response.read.return_value = b"not json"
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    with patch("ai.urllib.request.urlopen", return_value=response):
        note = ai.generate_note(
            title="A Paper",
            abstract="An abstract.",
            previous_count=5,
            latest_count=8,
            latest_date="2026-08-05",
            api_key="fake-key",
        )
    assert note == ai.fallback_note("A Paper", 5, 8, "2026-08-05")


def test_empty_content_falls_back_to_template():
    payload = {"content": []}
    with patch("ai.urllib.request.urlopen", return_value=_mock_response(payload)):
        note = ai.generate_note(
            title="A Paper",
            abstract="An abstract.",
            previous_count=5,
            latest_count=8,
            latest_date="2026-08-05",
            api_key="fake-key",
        )
    assert note == ai.fallback_note("A Paper", 5, 8, "2026-08-05")


def test_generate_note_reads_env_var_when_api_key_arg_omitted(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    payload = {"content": [{"type": "text", "text": "From env key."}]}
    with patch("ai.urllib.request.urlopen", return_value=_mock_response(payload)):
        note = ai.generate_note(
            title="A Paper",
            abstract="An abstract.",
            previous_count=5,
            latest_count=8,
            latest_date="2026-08-05",
        )
    assert note == "From env key."

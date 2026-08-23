"""Tests for src/ai_briefing.py — deterministic fallback and the aggregate-only prompt."""

import json
import urllib.error
from unittest import mock

from src import ai_briefing

SAMPLE_SUMMARY = {
    "day_change_pct": 1.25,
    "allocation_pct": {"STK": 80.0, "CASH": 20.0},
    "top_movers": [{"symbol": "AAPL", "pct_change": 12.5}],
}


def test_no_api_key_uses_deterministic_template_and_makes_no_network_call():
    with mock.patch("urllib.request.urlopen") as mock_urlopen:
        result = ai_briefing.build_briefing(SAMPLE_SUMMARY, api_key=None)

    mock_urlopen.assert_not_called()
    assert "1.25" in result
    assert "$" not in result


def test_with_api_key_calls_anthropic_and_returns_its_text():
    fake_response = mock.MagicMock()
    fake_response.read.return_value = json.dumps(
        {"content": [{"text": "Markets were calm today."}]}
    ).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = False

    with mock.patch("urllib.request.urlopen", return_value=fake_response) as mock_urlopen:
        result = ai_briefing.build_briefing(SAMPLE_SUMMARY, api_key="sk-test-key")

    assert result == "Markets were calm today."
    mock_urlopen.assert_called_once()


def test_malformed_api_response_falls_back_to_template():
    fake_response = mock.MagicMock()
    fake_response.read.return_value = b"not json"
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = False

    with mock.patch("urllib.request.urlopen", return_value=fake_response):
        result = ai_briefing.build_briefing(SAMPLE_SUMMARY, api_key="sk-test-key")

    assert "Set ANTHROPIC_API_KEY" in result


def test_network_error_falls_back_to_template():
    with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("no network")):
        result = ai_briefing.build_briefing(SAMPLE_SUMMARY, api_key="sk-test-key")

    assert "Set ANTHROPIC_API_KEY" in result


def test_prompt_contains_no_dollar_amounts_or_account_id():
    prompt = ai_briefing._build_prompt(SAMPLE_SUMMARY)
    assert "$" not in prompt
    assert "U123" not in prompt
    assert "no dollar" in prompt  # instructs the model not to include dollar figures either


def test_deterministic_briefing_reports_flat_on_zero_change():
    result = ai_briefing._deterministic_briefing({"day_change_pct": 0.0, "top_movers": []})
    assert "flat" in result

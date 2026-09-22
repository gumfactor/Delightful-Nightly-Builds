import json
import urllib.error
from unittest.mock import MagicMock, patch

from src import ai_polish

FACTS = {
    "wind_knots": "9.5",
    "gust_knots": "12.0",
    "temp_c": "21.0",
    "precip_probability": "10.0%",
    "beaufort_name": "Gentle Breeze",
}
DRAFT = "9.5 knots of Gentle Breeze, gusts to 12.0, 21.0C, 10.0% rain risk."


def _mock_anthropic_response(text: str):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({"content": [{"type": "text", "text": text}]}).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    return mock_response


def test_polish_returns_draft_unchanged_with_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with patch("src.ai_polish.urllib.request.urlopen") as mock_urlopen:
        result = ai_polish.polish(DRAFT, FACTS, api_key=None)
        assert result == DRAFT
        mock_urlopen.assert_not_called()


def test_polish_accepts_valid_response_with_all_facts_present():
    polished_text = "Gentle Breeze at 9.5 knots (gusts to 12.0) kept things easy at 21.0C, just a 10.0% rain risk."
    with patch("src.ai_polish.urllib.request.urlopen", return_value=_mock_anthropic_response(polished_text)):
        result = ai_polish.polish(DRAFT, FACTS, api_key="fake-key-for-test")
        assert result == polished_text


def test_polish_falls_back_when_response_drops_a_fact():
    # Missing the precip_probability fact entirely.
    incomplete = "Gentle Breeze at 9.5 knots (gusts to 12.0) kept things easy at 21.0C."
    with patch("src.ai_polish.urllib.request.urlopen", return_value=_mock_anthropic_response(incomplete)):
        result = ai_polish.polish(DRAFT, FACTS, api_key="fake-key-for-test")
        assert result == DRAFT


def test_polish_falls_back_on_network_error():
    with patch("src.ai_polish.urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        result = ai_polish.polish(DRAFT, FACTS, api_key="fake-key-for-test")
        assert result == DRAFT


def test_polish_falls_back_on_malformed_json():
    mock_response = MagicMock()
    mock_response.read.return_value = b"not json"
    mock_response.__enter__.return_value = mock_response
    with patch("src.ai_polish.urllib.request.urlopen", return_value=mock_response):
        result = ai_polish.polish(DRAFT, FACTS, api_key="fake-key-for-test")
        assert result == DRAFT


def test_polish_falls_back_on_unexpected_response_shape():
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({"unexpected": "shape"}).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    with patch("src.ai_polish.urllib.request.urlopen", return_value=mock_response):
        result = ai_polish.polish(DRAFT, FACTS, api_key="fake-key-for-test")
        assert result == DRAFT


def test_polish_uses_environment_variable_when_no_explicit_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    polished_text = "Gentle Breeze at 9.5 knots (gusts to 12.0) kept things easy at 21.0C, just a 10.0% rain risk."
    with patch("src.ai_polish.urllib.request.urlopen", return_value=_mock_anthropic_response(polished_text)) as mock_urlopen:
        result = ai_polish.polish(DRAFT, FACTS, api_key=None)
        assert result == polished_text
        mock_urlopen.assert_called_once()

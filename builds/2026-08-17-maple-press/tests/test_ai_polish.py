import json
import urllib.error
from unittest.mock import MagicMock, patch

import ai_polish


def test_polish_no_api_key_makes_zero_network_calls():
    with patch("ai_polish.urllib.request.urlopen") as mock_urlopen:
        text, was_polished = ai_polish.polish("Draft body text.", "spotlight", api_key=None)
    mock_urlopen.assert_not_called()
    assert text == "Draft body text."
    assert was_polished is False


def test_polish_no_api_key_and_no_env_var_makes_zero_network_calls(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with patch("ai_polish.urllib.request.urlopen") as mock_urlopen:
        text, was_polished = ai_polish.polish("Draft body text.", "gift_guide")
    mock_urlopen.assert_not_called()
    assert was_polished is False
    assert text == "Draft body text."


def _mock_response(payload_dict):
    response = MagicMock()
    response.read.return_value = json.dumps(payload_dict).encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def test_polish_success_returns_polished_text():
    mock_response = _mock_response({"content": [{"text": "A polished rewrite of the draft."}]})
    with patch("ai_polish.urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        text, was_polished = ai_polish.polish("Draft body text.", "spotlight", api_key="fake-key")

    mock_urlopen.assert_called_once()
    assert text == "A polished rewrite of the draft."
    assert was_polished is True


def test_polish_network_error_falls_back_to_draft():
    with patch(
        "ai_polish.urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        text, was_polished = ai_polish.polish("Draft body text.", "spotlight", api_key="fake-key")
    assert text == "Draft body text."
    assert was_polished is False


def test_polish_malformed_response_falls_back():
    mock_response = _mock_response({"unexpected": "shape"})
    with patch("ai_polish.urllib.request.urlopen", return_value=mock_response):
        text, was_polished = ai_polish.polish("Draft body text.", "spotlight", api_key="fake-key")
    assert text == "Draft body text."
    assert was_polished is False


def test_polish_empty_text_response_falls_back():
    mock_response = _mock_response({"content": [{"text": "   "}]})
    with patch("ai_polish.urllib.request.urlopen", return_value=mock_response):
        text, was_polished = ai_polish.polish("Draft body text.", "spotlight", api_key="fake-key")
    assert text == "Draft body text."
    assert was_polished is False


def test_polish_request_includes_draft_and_not_raw_business_data():
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _mock_response({"content": [{"text": "polished"}]})

    with patch("ai_polish.urllib.request.urlopen", side_effect=fake_urlopen):
        ai_polish.polish("Only the draft markdown.", "spotlight", api_key="fake-key")

    sent_prompt = captured["body"]["messages"][0]["content"]
    assert "Only the draft markdown." in sent_prompt

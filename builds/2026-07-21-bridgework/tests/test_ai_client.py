import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import ai_client, taxonomy

CONCEPT = taxonomy.get_concept("hpa_axis_response")
DOMAIN = taxonomy.get_domain("kitchen")
DRAFT = {"hook": "draft hook", "analogy": "draft analogy", "caveat": "draft caveat"}


def _mock_response(status, body_dict):
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.read.return_value = json.dumps(body_dict).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False
    return mock_resp


def test_no_api_key_returns_none_without_network_call():
    with patch("src.ai_client.urllib.request.urlopen") as mock_urlopen:
        result = ai_client.call_claude(CONCEPT, DOMAIN, "public_talk", DRAFT, api_key=None)
        assert result is None
        mock_urlopen.assert_not_called()


def test_successful_response_is_parsed():
    payload = {"content": [{"text": json.dumps({"hook": "H", "analogy": "A", "caveat": "C"})}]}
    with patch("src.ai_client.urllib.request.urlopen", return_value=_mock_response(200, payload)):
        result = ai_client.call_claude(CONCEPT, DOMAIN, "public_talk", DRAFT, api_key="fake-key")
    assert result == {"hook": "H", "analogy": "A", "caveat": "C"}


def test_non_200_status_returns_none():
    payload = {"content": [{"text": json.dumps({"hook": "H", "analogy": "A", "caveat": "C"})}]}
    with patch("src.ai_client.urllib.request.urlopen", return_value=_mock_response(500, payload)):
        result = ai_client.call_claude(CONCEPT, DOMAIN, "public_talk", DRAFT, api_key="fake-key")
    assert result is None


def test_malformed_inner_json_returns_none():
    payload = {"content": [{"text": "not valid json"}]}
    with patch("src.ai_client.urllib.request.urlopen", return_value=_mock_response(200, payload)):
        result = ai_client.call_claude(CONCEPT, DOMAIN, "public_talk", DRAFT, api_key="fake-key")
    assert result is None


def test_missing_expected_keys_returns_none():
    payload = {"content": [{"text": json.dumps({"hook": "H"})}]}
    with patch("src.ai_client.urllib.request.urlopen", return_value=_mock_response(200, payload)):
        result = ai_client.call_claude(CONCEPT, DOMAIN, "public_talk", DRAFT, api_key="fake-key")
    assert result is None


def test_network_error_returns_none():
    with patch(
        "src.ai_client.urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        result = ai_client.call_claude(CONCEPT, DOMAIN, "public_talk", DRAFT, api_key="fake-key")
    assert result is None


def test_timeout_returns_none():
    with patch("src.ai_client.urllib.request.urlopen", side_effect=TimeoutError("timed out")):
        result = ai_client.call_claude(CONCEPT, DOMAIN, "public_talk", DRAFT, api_key="fake-key")
    assert result is None


def test_empty_string_fields_return_none():
    payload = {"content": [{"text": json.dumps({"hook": "  ", "analogy": "A", "caveat": "C"})}]}
    with patch("src.ai_client.urllib.request.urlopen", return_value=_mock_response(200, payload)):
        result = ai_client.call_claude(CONCEPT, DOMAIN, "public_talk", DRAFT, api_key="fake-key")
    assert result is None


def test_request_includes_api_key_header():
    payload = {"content": [{"text": json.dumps({"hook": "H", "analogy": "A", "caveat": "C"})}]}
    captured = {}

    def fake_urlopen(request, timeout):
        captured["headers"] = dict(request.header_items())
        return _mock_response(200, payload)

    with patch("src.ai_client.urllib.request.urlopen", side_effect=fake_urlopen):
        ai_client.call_claude(CONCEPT, DOMAIN, "public_talk", DRAFT, api_key="secret-key-123")
    assert captured["headers"].get("X-api-key") == "secret-key-123"

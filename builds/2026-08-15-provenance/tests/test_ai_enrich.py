import json
from unittest.mock import patch

from src import ai_enrich


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def test_no_api_key_makes_zero_network_calls():
    with patch("src.ai_enrich.urllib.request.urlopen") as mock_urlopen:
        note = ai_enrich.enrich("Acme Co", "no claims resolved", "uncertain", api_key=None)
    assert note is None
    mock_urlopen.assert_not_called()


def test_never_invoked_for_non_uncertain_verdicts_even_with_a_key():
    with patch("src.ai_enrich.urllib.request.urlopen") as mock_urlopen:
        note = ai_enrich.enrich("Acme Co", "registered in Canada", "canadian", api_key="fake-key")
    assert note is None
    mock_urlopen.assert_not_called()


def test_successful_response_extracts_note_text():
    body = json.dumps({"content": [{"type": "text", "text": "This business's ownership could not be fully confirmed."}]}).encode("utf-8")
    with patch("src.ai_enrich.urllib.request.urlopen", return_value=_FakeResponse(body)):
        note = ai_enrich.enrich("Acme Co", "conflicting claims", "uncertain", api_key="fake-key")
    assert note == "This business's ownership could not be fully confirmed."


def test_network_failure_falls_back_to_none():
    with patch("src.ai_enrich.urllib.request.urlopen", side_effect=OSError("network down")):
        note = ai_enrich.enrich("Acme Co", "conflicting claims", "uncertain", api_key="fake-key")
    assert note is None


def test_malformed_response_falls_back_to_none():
    body = json.dumps({"unexpected": "shape"}).encode("utf-8")
    with patch("src.ai_enrich.urllib.request.urlopen", return_value=_FakeResponse(body)):
        note = ai_enrich.enrich("Acme Co", "conflicting claims", "uncertain", api_key="fake-key")
    assert note is None


def test_reads_key_from_environment_when_not_passed_explicitly(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    body = json.dumps({"content": [{"type": "text", "text": "Note from env key."}]}).encode("utf-8")
    with patch("src.ai_enrich.urllib.request.urlopen", return_value=_FakeResponse(body)) as mock_urlopen:
        note = ai_enrich.enrich("Acme Co", "conflicting claims", "uncertain")
    assert note == "Note from env key."
    mock_urlopen.assert_called_once()

import json
from unittest.mock import MagicMock, patch

import ai_summary


def test_fallback_used_when_no_api_key():
    entries = [{"field": "id", "change": "removed", "severity": "breaking", "old": "int", "new": None, "detail": "field removed"}]
    summary = ai_summary.generate_summary(entries, api_key=None)
    assert "breaking change" in summary
    assert "field removed" in summary


def test_fallback_for_no_changes():
    summary = ai_summary.generate_summary([], api_key=None)
    assert summary == "No structural changes detected between the two schemas."


def test_fallback_groups_by_all_severities():
    entries = [
        {"field": "a", "change": "removed", "severity": "breaking", "old": "int", "new": None, "detail": "a removed"},
        {"field": "b", "change": "presence_changed", "severity": "risky", "old": "required", "new": "optional", "detail": "b optional"},
        {"field": "c", "change": "added", "severity": "safe", "old": None, "new": "str", "detail": "c added"},
    ]
    summary = ai_summary.generate_summary(entries, api_key=None)
    assert "breaking change" in summary
    assert "risky change" in summary
    assert "safe change" in summary


def _mock_response(text):
    body = json.dumps({"content": [{"type": "text", "text": text}]}).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = False
    return mock_resp


def test_successful_api_call_returns_model_text():
    entries = [{"field": "id", "change": "removed", "severity": "breaking", "old": "int", "new": None, "detail": "field removed"}]
    with patch("ai_summary.urllib.request.urlopen", return_value=_mock_response("Review the removed id field.")):
        summary = ai_summary.generate_summary(entries, api_key="fake-key")
    assert summary == "Review the removed id field."


def test_api_failure_falls_back_to_deterministic_summary():
    entries = [{"field": "id", "change": "removed", "severity": "breaking", "old": "int", "new": None, "detail": "field removed"}]
    with patch("ai_summary.urllib.request.urlopen", side_effect=OSError("network unreachable")):
        summary = ai_summary.generate_summary(entries, api_key="fake-key")
    assert "breaking change" in summary
    assert "field removed" in summary


def test_empty_model_response_falls_back():
    entries = [{"field": "id", "change": "removed", "severity": "breaking", "old": "int", "new": None, "detail": "field removed"}]
    with patch("ai_summary.urllib.request.urlopen", return_value=_mock_response("")):
        summary = ai_summary.generate_summary(entries, api_key="fake-key")
    assert "breaking change" in summary

import json
import os
import sys
import urllib.error
from datetime import date
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ai_review import _FALLBACK_NOTE, annotate_all, get_ai_note  # noqa: E402
from rules import STATUS_NO_BLOCKING_RULE, STATUS_REQUIRES_JUSTIFICATION, LineItem, Verdict  # noqa: E402


def _verdict(status=STATUS_REQUIRES_JUSTIFICATION):
    line = LineItem(item="Equipment", category="Equipment", amount=500.0, item_date=date(2026, 5, 1), justification="")
    return Verdict(line=line, status=status, reason="No justification provided.", principle="Direct cost principle")


def _mock_response(text):
    body = json.dumps({"content": [{"text": text}]}).encode("utf-8")
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value.read.return_value = body
    return mock_cm


def test_no_api_key_returns_fallback_without_network_call():
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = AssertionError("network call must not be made without an API key")
        note = get_ai_note(_verdict(), api_key=None)
    assert note == _FALLBACK_NOTE
    mock_urlopen.assert_not_called()


def test_successful_api_call_returns_response_text():
    with patch("urllib.request.urlopen", return_value=_mock_response("This looks like a direct research cost.")):
        note = get_ai_note(_verdict(), api_key="fake-test-key")
    assert note == "This looks like a direct research cost."


def test_malformed_response_falls_back_to_deterministic_note():
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value.read.return_value = json.dumps({"content": []}).encode("utf-8")
    with patch("urllib.request.urlopen", return_value=mock_cm):
        note = get_ai_note(_verdict(), api_key="fake-test-key")
    assert note == _FALLBACK_NOTE


def test_network_error_falls_back_to_deterministic_note():
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
        note = get_ai_note(_verdict(), api_key="fake-test-key")
    assert note == _FALLBACK_NOTE


def test_annotate_all_skips_when_use_ai_false():
    verdicts = [_verdict(STATUS_REQUIRES_JUSTIFICATION)]
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = AssertionError("must not call network when use_ai is False")
        notes = annotate_all(verdicts, use_ai=False, api_key="fake-test-key")
    assert notes == {}
    mock_urlopen.assert_not_called()


def test_annotate_all_only_reviews_eligible_statuses():
    reviewable = _verdict(STATUS_NO_BLOCKING_RULE)
    line2 = LineItem(item="Wine", category="Hospitality", amount=100.0, item_date=date(2026, 5, 1), justification="")
    ineligible = Verdict(line=line2, status="ineligible", reason="Alcohol is ineligible.", principle="p")
    verdicts = [reviewable, ineligible]
    with patch("urllib.request.urlopen", return_value=_mock_response("note text")):
        notes = annotate_all(verdicts, use_ai=True, api_key="fake-test-key")
    assert 0 in notes
    assert 1 not in notes


def test_prompt_never_includes_other_line_items_or_file_paths():
    verdict = _verdict()
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["body"] = request.data.decode("utf-8")
        return _mock_response("ok")

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        get_ai_note(verdict, api_key="fake-test-key")

    payload = json.loads(captured["body"])
    prompt_text = payload["messages"][0]["content"]
    assert verdict.line.item in prompt_text
    assert "sample_data" not in prompt_text
    assert ".csv" not in prompt_text

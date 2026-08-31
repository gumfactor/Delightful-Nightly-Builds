"""Unit tests for src/coach.py — optional AI coach note with deterministic
fallback. Every Anthropic call is mocked; none of these tests ever touch
the network."""

import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.coach import generate_coach_note

_STATS = [
    {"id": "running", "name": "Running", "cadence": "daily", "current_streak": 4,
     "longest_streak": 10, "completion_rate": 0.9},
    {"id": "writing", "name": "Writing", "cadence": "daily", "current_streak": 0,
     "longest_streak": 3, "completion_rate": 0.2},
]


def test_no_api_key_uses_deterministic_fallback_with_zero_network_calls() -> None:
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_urlopen.side_effect = AssertionError("must not be called without an API key")
        note = generate_coach_note(_STATS, api_key=None)
    assert note.source == "deterministic"
    assert "Running" in note.text
    mock_urlopen.assert_not_called()


def test_deterministic_fallback_handles_empty_habit_list() -> None:
    note = generate_coach_note([], api_key=None)
    assert note.source == "deterministic"
    assert "habits.json" in note.text


def test_ai_call_used_when_key_present_and_request_succeeds() -> None:
    response_body = json.dumps({"content": [{"type": "text", "text": "Great consistency on running."}]})
    mock_response = MagicMock()
    mock_response.read.return_value = response_body.encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_response) as mock_urlopen:
        note = generate_coach_note(_STATS, api_key="fake-key-for-test")

    assert note.source == "ai"
    assert note.text == "Great consistency on running."
    mock_urlopen.assert_called_once()


def test_ai_call_sends_only_aggregate_fields_never_dates_or_notes() -> None:
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        response = MagicMock()
        response.read.return_value = json.dumps(
            {"content": [{"type": "text", "text": "note"}]}
        ).encode("utf-8")
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        return response

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        generate_coach_note(_STATS, api_key="fake-key-for-test")

    prompt = captured["body"]["messages"][0]["content"]
    json_blob = prompt[prompt.index("["):]
    summary_sent = json.loads(json_blob)
    assert summary_sent  # non-empty, something was actually sent
    for entry in summary_sent:
        assert set(entry.keys()) == {"name", "cadence", "current_streak", "longest_streak", "completion_rate"}


def test_ai_call_failure_falls_back_to_deterministic() -> None:
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("no network")):
        note = generate_coach_note(_STATS, api_key="fake-key-for-test")
    assert note.source == "deterministic"
    assert note.text  # still real, non-empty content


def test_ai_call_empty_response_falls_back_to_deterministic() -> None:
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({"content": []}).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False

    with patch("urllib.request.urlopen", return_value=mock_response):
        note = generate_coach_note(_STATS, api_key="fake-key-for-test")

    assert note.source == "deterministic"


def test_deterministic_fallback_flags_lowest_completion_rate() -> None:
    note = generate_coach_note(_STATS, api_key=None)
    assert "Writing" in note.text

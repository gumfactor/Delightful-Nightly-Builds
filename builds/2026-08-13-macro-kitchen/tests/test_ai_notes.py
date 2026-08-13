import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import ai_notes

DAY_TOTALS = {"calories": 2400.0, "protein_g": 160.0, "carbs_g": 220.0, "fat_g": 80.0}
RECIPE_NAMES = ["Greek Yogurt & Berry Bowl", "Grilled Chicken Caesar Salad", "Baked Salmon with Asparagus"]


def test_no_api_key_makes_zero_network_calls(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with patch("urllib.request.urlopen") as mock_urlopen:
        note, used_ai = ai_notes.generate_day_note(DAY_TOTALS, RECIPE_NAMES)
        mock_urlopen.assert_not_called()
    assert used_ai is False
    assert isinstance(note, str) and len(note) > 0


def test_deterministic_note_mentions_calories():
    note = ai_notes._deterministic_note(DAY_TOTALS, RECIPE_NAMES)
    assert "2400" in note


def test_deterministic_note_labels_high_protein_day():
    high_protein_totals = {"calories": 2000.0, "protein_g": 180.0, "carbs_g": 100.0, "fat_g": 60.0}
    note = ai_notes._deterministic_note(high_protein_totals, RECIPE_NAMES)
    assert "protein-forward" in note.lower()


def test_successful_api_call_returns_ai_text(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    response_body = json.dumps(
        {"content": [{"type": "text", "text": "Prep the salmon the night before."}]}
    ).encode("utf-8")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return response_body

    with patch("urllib.request.urlopen", return_value=FakeResponse()) as mock_urlopen:
        note, used_ai = ai_notes.generate_day_note(DAY_TOTALS, RECIPE_NAMES)
        mock_urlopen.assert_called_once()

    assert used_ai is True
    assert note == "Prep the salmon the night before."


def test_api_failure_falls_back_to_deterministic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
        note, used_ai = ai_notes.generate_day_note(DAY_TOTALS, RECIPE_NAMES)

    assert used_ai is False
    assert isinstance(note, str) and len(note) > 0


def test_api_malformed_response_falls_back_to_deterministic(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"{}"  # missing 'content' key

    with patch("urllib.request.urlopen", return_value=FakeResponse()):
        note, used_ai = ai_notes.generate_day_note(DAY_TOTALS, RECIPE_NAMES)

    assert used_ai is False
    assert isinstance(note, str) and len(note) > 0


def test_prompt_never_includes_body_stats(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")

    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["body"] = request.data.decode("utf-8")
        raise TimeoutError("stop after capturing")

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        ai_notes.generate_day_note(DAY_TOTALS, RECIPE_NAMES)

    body_text = captured["body"]
    # Use JSON-key form so substrings of unrelated words (e.g. "age" inside
    # "messages") don't produce a false positive.
    for forbidden_key in ['"weight_kg"', '"height_cm"', '"age"', '"sex"']:
        assert forbidden_key not in body_text

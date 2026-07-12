import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import ai_polish

SAMPLE_QUESTION = {
    "skeleton": "Does empathic accuracy predict prosocial behavior in caregivers?",
    "rationale": "Measured via a behavioral task, framed through dual-process models.",
    "testability": "feasible-now",
}


def test_polish_question_falls_back_to_template_when_no_api_key():
    text, source = ai_polish.polish_question(SAMPLE_QUESTION, api_key=None)
    assert source == "template"
    assert "Research Question" in text
    assert SAMPLE_QUESTION["skeleton"] in text


def test_polish_question_calls_claude_when_key_present_and_parses_response():
    fake_response_body = json.dumps(
        {"content": [{"type": "text", "text": "A polished grant-ready paragraph."}]}
    ).encode("utf-8")

    mock_cm = MagicMock()
    mock_cm.__enter__.return_value.read.return_value = fake_response_body

    with patch("src.ai_polish.urllib.request.urlopen", return_value=mock_cm) as mock_urlopen:
        text, source = ai_polish.polish_question(SAMPLE_QUESTION, api_key="fake-key-for-test")

    assert source == "claude"
    assert text == "A polished grant-ready paragraph."
    mock_urlopen.assert_called_once()


def test_polish_question_falls_back_on_network_error():
    with patch(
        "src.ai_polish.urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        text, source = ai_polish.polish_question(SAMPLE_QUESTION, api_key="fake-key-for-test")
    assert source == "template"
    assert SAMPLE_QUESTION["skeleton"] in text


def test_polish_question_falls_back_on_malformed_response():
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value.read.return_value = b"not valid json"

    with patch("src.ai_polish.urllib.request.urlopen", return_value=mock_cm):
        text, source = ai_polish.polish_question(SAMPLE_QUESTION, api_key="fake-key-for-test")

    assert source == "template"


def test_polish_question_falls_back_when_response_has_no_text_blocks():
    fake_response_body = json.dumps({"content": []}).encode("utf-8")
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value.read.return_value = fake_response_body

    with patch("src.ai_polish.urllib.request.urlopen", return_value=mock_cm):
        text, source = ai_polish.polish_question(SAMPLE_QUESTION, api_key="fake-key-for-test")

    assert source == "template"

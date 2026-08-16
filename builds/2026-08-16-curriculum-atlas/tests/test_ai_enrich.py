import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from src import ai_enrich


def _mock_response(text):
    resp = MagicMock()
    resp.read.return_value = json.dumps({"content": [{"text": text}]}).encode("utf-8")
    cm = MagicMock()
    cm.__enter__.return_value = resp
    cm.__exit__.return_value = False
    return cm


def test_get_api_key_reads_env_var(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
    assert ai_enrich.get_api_key() == "sk-test-123"


def test_get_api_key_returns_none_when_unset(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert ai_enrich.get_api_key() is None


def test_auto_mark_concepts_makes_zero_calls_with_no_key():
    with patch("src.ai_enrich.urllib.request.urlopen") as mock_urlopen:
        result = ai_enrich.auto_mark_concepts("Some syllabus text.", None)
    mock_urlopen.assert_not_called()
    assert result == "Some syllabus text."


def test_auto_mark_concepts_returns_marked_text_on_success():
    marked = "We discuss the [[HPA axis]] today."
    with patch("src.ai_enrich.urllib.request.urlopen", return_value=_mock_response(marked)) as mock_urlopen:
        result = ai_enrich.auto_mark_concepts("We discuss the HPA axis today.", "sk-test")
    mock_urlopen.assert_called_once()
    assert result == marked


def test_auto_mark_concepts_falls_back_on_network_error():
    with patch("src.ai_enrich.urllib.request.urlopen", side_effect=urllib.error.URLError("blocked")):
        result = ai_enrich.auto_mark_concepts("Original text.", "sk-test")
    assert result == "Original text."


def test_auto_mark_concepts_falls_back_on_malformed_response():
    cm = MagicMock()
    cm.__enter__.return_value.read.return_value = b"not valid json"
    cm.__exit__.return_value = False
    with patch("src.ai_enrich.urllib.request.urlopen", return_value=cm):
        result = ai_enrich.auto_mark_concepts("Original text.", "sk-test")
    assert result == "Original text."


def test_auto_mark_concepts_falls_back_on_empty_text_input():
    with patch("src.ai_enrich.urllib.request.urlopen") as mock_urlopen:
        result = ai_enrich.auto_mark_concepts("", "sk-test")
    mock_urlopen.assert_not_called()
    assert result == ""


def test_generate_concept_notes_makes_zero_calls_with_no_key():
    with patch("src.ai_enrich.urllib.request.urlopen") as mock_urlopen:
        result = ai_enrich.generate_concept_notes([("hpa axi", "HPA Axis")], None)
    mock_urlopen.assert_not_called()
    assert result == {}


def test_generate_concept_notes_makes_zero_calls_with_empty_concept_list():
    with patch("src.ai_enrich.urllib.request.urlopen") as mock_urlopen:
        result = ai_enrich.generate_concept_notes([], "sk-test")
    mock_urlopen.assert_not_called()
    assert result == {}


def test_generate_concept_notes_parses_numbered_response():
    response_text = "1. A stress hormone axis.\n2. A theory of empathic accuracy."
    concepts = [("hpa axi", "HPA Axis"), ("empathy theory", "Empathy Theory")]
    with patch("src.ai_enrich.urllib.request.urlopen", return_value=_mock_response(response_text)) as mock_urlopen:
        result = ai_enrich.generate_concept_notes(concepts, "sk-test")
    mock_urlopen.assert_called_once()
    assert result["hpa axi"] == "A stress hormone axis."
    assert result["empathy theory"] == "A theory of empathic accuracy."


def test_generate_concept_notes_single_call_regardless_of_count():
    concepts = [(f"concept{i}", f"Concept {i}") for i in range(5)]
    response_text = "\n".join(f"{i + 1}. Note {i}." for i in range(5))
    with patch("src.ai_enrich.urllib.request.urlopen", return_value=_mock_response(response_text)) as mock_urlopen:
        ai_enrich.generate_concept_notes(concepts, "sk-test")
    assert mock_urlopen.call_count == 1


def test_generate_concept_notes_falls_back_to_empty_on_error():
    with patch("src.ai_enrich.urllib.request.urlopen", side_effect=OSError("network down")):
        result = ai_enrich.generate_concept_notes([("x", "X")], "sk-test")
    assert result == {}

"""Tests for prompt.py — prompt construction."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from prompt import build_prompt, SYSTEM_PROMPT, VALID_LEVELS


def test_prompt_contains_topic():
    result = build_prompt("cortisol and stress", "Stress and Coping", "undergrad", 75)
    assert "cortisol and stress" in result


def test_prompt_contains_course():
    result = build_prompt("memory", "Cognitive Neuroscience", "graduate", 90)
    assert "Cognitive Neuroscience" in result


def test_prompt_contains_level():
    result = build_prompt("empathy", "Social Neuroscience", "graduate", 60)
    assert "graduate" in result


def test_prompt_contains_duration():
    result = build_prompt("sleep", "Stress and Coping", "undergrad", 45)
    assert "45" in result


def test_prompt_requests_json():
    result = build_prompt("pain", "Neuroscience", "undergrad", 75)
    assert "JSON" in result


def test_prompt_requests_objectives():
    result = build_prompt("amygdala", "Affective Neuroscience", "graduate", 75)
    assert "objectives" in result


def test_prompt_requests_quiz_items():
    result = build_prompt("stress", "Coping", "undergrad", 75)
    assert "quiz" in result.lower()


def test_prompt_requests_discussion_questions():
    result = build_prompt("empathy", "Social Neuroscience", "mixed", 90)
    assert "discussion" in result.lower()


def test_prompt_requests_hook():
    result = build_prompt("dopamine", "Neuroscience", "undergrad", 75)
    assert "hook" in result.lower() or "opening" in result.lower()


def test_prompt_requests_key_concepts():
    result = build_prompt("serotonin", "Psychopharmacology", "graduate", 60)
    assert "key_concepts" in result or "concepts" in result.lower()


def test_prompt_requests_homework():
    result = build_prompt("HPA axis", "Stress and Coping", "undergrad", 75)
    assert "homework" in result.lower()


def test_prompt_requests_outline():
    result = build_prompt("fear", "Affective Neuroscience", "graduate", 75)
    assert "outline" in result.lower()


def test_system_prompt_is_string():
    assert isinstance(SYSTEM_PROMPT, str) and len(SYSTEM_PROMPT) > 20


def test_system_prompt_instructs_json():
    assert "JSON" in SYSTEM_PROMPT


def test_valid_levels_contains_undergrad():
    assert "undergrad" in VALID_LEVELS


def test_valid_levels_contains_graduate():
    assert "graduate" in VALID_LEVELS


def test_valid_levels_contains_mixed():
    assert "mixed" in VALID_LEVELS


def test_prompt_duration_in_outline_requirement():
    result = build_prompt("stress", "Coping", "undergrad", 90)
    assert "90" in result


def test_prompt_level_in_audience_context():
    result = build_prompt("fear", "Affective Neuro", "graduate", 75)
    assert result.count("graduate") >= 2

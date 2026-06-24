"""Tests for parser.py — response parsing and validation."""

import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from parser import parse_response, make_slug, REQUIRED_SECTIONS


FULL_VALID = {
    "objectives": ["Explain the HPA axis", "Identify cortisol effects"],
    "outline": [
        {"time_range": "0-5 min", "title": "Introduction", "activity": "Overview"},
        {"time_range": "5-45 min", "title": "Core content", "activity": "Lecture"},
    ],
    "hook": "Imagine waking up at 3am with a racing heart...",
    "discussion_questions": [
        {"question": "What triggers the HPA axis?", "teaching_note": "Pair-share first"},
        {"question": "How does cortisol affect memory?", "teaching_note": "Think-pair-share"},
    ],
    "quiz_items": [
        {
            "question": "Which gland releases cortisol?",
            "options": {"A": "Adrenal", "B": "Thyroid", "C": "Pituitary", "D": "Pineal"},
            "answer": "A",
            "rationale": "The adrenal cortex secretes cortisol; the others do not.",
        }
    ],
    "key_concepts": ["cortisol: a glucocorticoid stress hormone", "HPA axis: hypothalamic-pituitary-adrenal axis"],
    "homework": "Write a one-page reflection on how stress affects your daily life.",
}


def test_parse_valid_json_returns_dict():
    raw = json.dumps(FULL_VALID)
    result = parse_response(raw)
    assert isinstance(result, dict)


def test_parse_valid_json_has_all_sections():
    raw = json.dumps(FULL_VALID)
    result = parse_response(raw)
    for section in REQUIRED_SECTIONS:
        assert section in result, f"Missing section: {section}"


def test_parse_objectives_extracted():
    raw = json.dumps(FULL_VALID)
    result = parse_response(raw)
    assert result["objectives"] == FULL_VALID["objectives"]


def test_parse_outline_extracted():
    raw = json.dumps(FULL_VALID)
    result = parse_response(raw)
    assert len(result["outline"]) == 2


def test_parse_hook_extracted():
    raw = json.dumps(FULL_VALID)
    result = parse_response(raw)
    assert "3am" in result["hook"]


def test_parse_discussion_questions_extracted():
    raw = json.dumps(FULL_VALID)
    result = parse_response(raw)
    assert len(result["discussion_questions"]) == 2


def test_parse_quiz_items_extracted():
    raw = json.dumps(FULL_VALID)
    result = parse_response(raw)
    assert len(result["quiz_items"]) == 1
    assert result["quiz_items"][0]["answer"] == "A"


def test_parse_quiz_item_has_rationale():
    raw = json.dumps(FULL_VALID)
    result = parse_response(raw)
    assert "adrenal cortex" in result["quiz_items"][0]["rationale"]


def test_parse_key_concepts_extracted():
    raw = json.dumps(FULL_VALID)
    result = parse_response(raw)
    assert len(result["key_concepts"]) == 2


def test_parse_homework_extracted():
    raw = json.dumps(FULL_VALID)
    result = parse_response(raw)
    assert "reflection" in result["homework"]


def test_parse_malformed_json_returns_defaults():
    result = parse_response("not valid json at all {{{{")
    assert isinstance(result, dict)
    for section in REQUIRED_SECTIONS:
        assert section in result


def test_parse_missing_objectives_uses_default():
    data = dict(FULL_VALID)
    del data["objectives"]
    result = parse_response(json.dumps(data))
    assert isinstance(result["objectives"], list)
    assert len(result["objectives"]) > 0


def test_parse_missing_quiz_items_uses_empty():
    data = dict(FULL_VALID)
    del data["quiz_items"]
    result = parse_response(json.dumps(data))
    assert isinstance(result["quiz_items"], list)


def test_parse_quiz_item_missing_answer_gets_default():
    data = dict(FULL_VALID)
    item = dict(FULL_VALID["quiz_items"][0])
    del item["answer"]
    data["quiz_items"] = [item]
    result = parse_response(json.dumps(data))
    assert result["quiz_items"][0]["answer"] in ("A", "B", "C", "D")


def test_parse_quiz_item_missing_rationale_gets_empty():
    data = dict(FULL_VALID)
    item = dict(FULL_VALID["quiz_items"][0])
    del item["rationale"]
    data["quiz_items"] = [item]
    result = parse_response(json.dumps(data))
    assert result["quiz_items"][0]["rationale"] == ""


def test_parse_quiz_item_without_options_is_rejected():
    data = dict(FULL_VALID)
    data["quiz_items"] = [{"question": "Bad item"}]
    result = parse_response(json.dumps(data))
    assert len(result["quiz_items"]) == 0


def test_parse_hook_not_str_gets_default():
    data = dict(FULL_VALID)
    data["hook"] = 12345
    result = parse_response(json.dumps(data))
    assert isinstance(result["hook"], str)


def test_parse_homework_not_str_gets_default():
    data = dict(FULL_VALID)
    data["homework"] = ["not", "a", "string"]
    result = parse_response(json.dumps(data))
    assert isinstance(result["homework"], str)


def test_parse_json_with_markdown_fence():
    fenced = "```json\n" + json.dumps(FULL_VALID) + "\n```"
    result = parse_response(fenced)
    assert "objectives" in result
    assert len(result["objectives"]) > 0


def test_make_slug_basic():
    assert make_slug("Cortisol and Stress") == "cortisol-and-stress"


def test_make_slug_special_chars():
    assert make_slug("HPA-axis: what is it?") == "hpa-axis-what-is-it"


def test_make_slug_truncates_at_80():
    long = "a" * 100
    assert len(make_slug(long)) <= 80


def test_make_slug_no_leading_trailing_hyphens():
    result = make_slug("  hello world  ")
    assert not result.startswith("-") and not result.endswith("-")

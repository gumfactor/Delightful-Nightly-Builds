"""Tests for renderer.py — HTML and markdown generation."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from renderer import render_html, render_markdown


SAMPLE_DATA = {
    "objectives": ["Explain the cortisol stress response", "Identify HPA axis components"],
    "outline": [
        {"time_range": "0-5 min", "title": "Introduction", "activity": "Warm-up question"},
        {"time_range": "5-65 min", "title": "Core Lecture", "activity": "Slides and discussion"},
        {"time_range": "65-75 min", "title": "Wrap-up", "activity": "Summary and Q&A"},
    ],
    "hook": "Imagine waking at 3am with a racing heart. That surge you feel is cortisol.",
    "discussion_questions": [
        {"question": "What triggers the HPA axis?", "teaching_note": "Pair-share first."},
        {"question": "How does cortisol affect memory consolidation?", "teaching_note": ""},
    ],
    "quiz_items": [
        {
            "question": "Which gland produces cortisol?",
            "options": {"A": "Adrenal cortex", "B": "Thyroid", "C": "Pituitary", "D": "Pineal"},
            "answer": "A",
            "rationale": "The adrenal cortex, specifically the zona fasciculata, secretes cortisol.",
        }
    ],
    "key_concepts": [
        "cortisol: primary glucocorticoid stress hormone",
        "HPA axis: hypothalamic-pituitary-adrenal axis governing stress response",
    ],
    "homework": "Write a one-page reflection on how chronic stress affects cognitive performance.",
}


def get_html():
    return render_html("Cortisol and Stress", "Stress and Coping", "undergrad", 75, SAMPLE_DATA)


def get_md():
    return render_markdown("Cortisol and Stress", "Stress and Coping", "undergrad", 75, SAMPLE_DATA)


def test_html_has_doctype():
    assert get_html().startswith("<!DOCTYPE html>")


def test_html_has_html_tag():
    assert "<html" in get_html()


def test_html_has_utf8_charset():
    assert "UTF-8" in get_html()


def test_html_has_title():
    h = get_html()
    assert "<title>" in h and "Cortisol" in h


def test_html_includes_topic():
    assert "Cortisol and Stress" in get_html()


def test_html_includes_course():
    assert "Stress and Coping" in get_html()


def test_html_has_all_section_tabs():
    h = get_html()
    for tab in ("Objectives", "Outline", "Hook", "Discussion", "Quiz", "Concepts", "Homework"):
        assert tab in h, f"Missing tab: {tab}"


def test_html_objectives_content():
    assert "cortisol stress response" in get_html()


def test_html_outline_time_range():
    assert "0-5 min" in get_html()


def test_html_hook_content():
    assert "racing heart" in get_html()


def test_html_discussion_question():
    assert "HPA axis" in get_html()


def test_html_quiz_options_abcd():
    h = get_html()
    for opt in ("A.", "B.", "C.", "D."):
        assert opt in h, f"Missing option: {opt}"


def test_html_quiz_show_answer_button():
    assert "Show Answer" in get_html()


def test_html_key_concept_term():
    assert "cortisol" in get_html()


def test_html_homework_content():
    assert "reflection" in get_html()


def test_html_xss_escaping_in_topic():
    h = render_html("<script>alert(1)</script>", "Course", "undergrad", 75, SAMPLE_DATA)
    assert "<script>alert(1)</script>" not in h
    assert "&lt;script&gt;" in h


def test_html_xss_escaping_in_course():
    h = render_html("Topic", '<img src=x onerror="alert(1)">', "undergrad", 75, SAMPLE_DATA)
    assert 'onerror="alert(1)"' not in h


def test_html_copy_button_present():
    assert "copy-btn" in get_html() or "Copy" in get_html()


def test_html_export_button_present():
    assert "Export" in get_html() or "export" in get_html()


def test_html_data_testid_attributes():
    h = get_html()
    assert "data-testid" in h


def test_html_empty_objectives_handled():
    data = dict(SAMPLE_DATA)
    data["objectives"] = []
    h = render_html("Test", "Course", "undergrad", 75, data)
    assert "No objectives generated" in h


def test_html_empty_quiz_handled():
    data = dict(SAMPLE_DATA)
    data["quiz_items"] = []
    h = render_html("Test", "Course", "undergrad", 75, data)
    assert "No quiz items generated" in h


def test_markdown_has_topic_header():
    assert "# Cortisol and Stress" in get_md()


def test_markdown_has_objectives_section():
    md = get_md()
    assert "## Learning Objectives" in md


def test_markdown_has_quiz_section():
    assert "## Quiz Items" in get_md()


def test_markdown_has_answer():
    assert "Answer: A" in get_md()


def test_markdown_has_concepts_section():
    assert "## Key Concepts" in get_md()


def test_markdown_has_homework_section():
    assert "## Homework" in get_md()

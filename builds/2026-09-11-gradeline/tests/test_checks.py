import pytest

from src.checks import (
    check_compliance,
    count_citations,
    count_words,
    find_sections,
    flesch_reading_ease,
    keyword_coverage_score,
    keyword_hits,
)
from src.rubric import load_rubric_dict

RUBRIC_DICT = {
    "name": "Test",
    "min_words": 5,
    "max_words": 50,
    "min_citations": 1,
    "required_sections": ["Introduction", "Discussion"],
    "criteria": [
        {"id": "c1", "name": "C1", "max_points": 10, "keywords": ["alpha"], "min_keyword_hits": 1}
    ],
}


def test_count_words_basic():
    assert count_words("one two three") == 3


def test_count_words_empty_string():
    assert count_words("") == 0


def test_count_words_ignores_punctuation_as_separator():
    assert count_words("Hello, world! It's fine.") == 4


def test_find_sections_plain_heading():
    text = "Introduction\nSome text.\nDiscussion\nMore text."
    result = find_sections(text, ["Introduction", "Discussion"])
    assert result == {"Introduction": True, "Discussion": True}


def test_find_sections_markdown_heading():
    text = "## Introduction\nSome text.\n### Discussion\nMore text."
    result = find_sections(text, ["Introduction", "Discussion"])
    assert result == {"Introduction": True, "Discussion": True}


def test_find_sections_case_insensitive():
    text = "INTRODUCTION\nSome text."
    result = find_sections(text, ["Introduction"])
    assert result["Introduction"] is True


def test_find_sections_with_trailing_colon():
    text = "Discussion:\nSome text."
    result = find_sections(text, ["Discussion"])
    assert result["Discussion"] is True


def test_find_sections_missing_section():
    text = "Introduction\nSome text with no other headings."
    result = find_sections(text, ["Introduction", "Conclusion"])
    assert result == {"Introduction": True, "Conclusion": False}


def test_find_sections_does_not_match_mid_sentence():
    text = "This paragraph discusses the introduction of a new idea in passing."
    result = find_sections(text, ["Introduction"])
    assert result["Introduction"] is False


def test_count_citations_author_year():
    text = "This is supported by evidence (Smith, 2019) and also (Jones & Lee, 2020)."
    assert count_citations(text) == 2


def test_count_citations_et_al():
    text = "Prior work (Nguyen et al. 2021) found similar results."
    assert count_citations(text) == 1


def test_count_citations_numbered():
    text = "This was shown previously [1] and confirmed again [2, 3]."
    assert count_citations(text) == 2


def test_count_citations_zero():
    assert count_citations("No citations appear anywhere in this text.") == 0


def test_keyword_hits_counts_each_keyword():
    text = "The study found evidence. Another study confirmed the evidence."
    hits = keyword_hits(text, ["study", "evidence", "missing"])
    assert hits == {"study": 2, "evidence": 2, "missing": 0}


def test_keyword_hits_is_case_insensitive_and_whole_word():
    text = "Studying is different from a study of studies."
    hits = keyword_hits(text, ["study"])
    assert hits["study"] == 1


def test_keyword_coverage_score_full_credit_when_hits_meet_minimum():
    text = "alpha alpha alpha"
    score, hits = keyword_coverage_score(text, ["alpha"], min_hits=2, max_points=10)
    assert score == 10.0
    assert hits == 3


def test_keyword_coverage_score_partial_credit():
    text = "alpha appears once here."
    score, hits = keyword_coverage_score(text, ["alpha"], min_hits=4, max_points=8)
    assert hits == 1
    assert score == pytest.approx(2.0)


def test_keyword_coverage_score_zero_hits():
    text = "no matching terms at all."
    score, hits = keyword_coverage_score(text, ["alpha"], min_hits=2, max_points=10)
    assert score == 0.0
    assert hits == 0


def test_keyword_coverage_score_zero_min_hits_raises():
    with pytest.raises(ValueError):
        keyword_coverage_score("alpha", ["alpha"], min_hits=0, max_points=10)


def test_flesch_reading_ease_returns_none_for_empty_text():
    assert flesch_reading_ease("") is None


def test_flesch_reading_ease_treats_untermined_text_as_one_sentence():
    # No '.', '!', or '?' present, but there are still words -- the whole
    # string counts as a single implicit sentence rather than returning None.
    score = flesch_reading_ease("no terminator here")
    assert score is not None


def test_flesch_reading_ease_returns_none_for_whitespace_only():
    assert flesch_reading_ease("   \n\t  ") is None


def test_flesch_reading_ease_reasonable_range_for_simple_text():
    text = "The cat sat on the mat. The dog ran fast."
    score = flesch_reading_ease(text)
    assert score is not None
    assert 0 <= score <= 130


def test_check_compliance_all_pass():
    rubric = load_rubric_dict(RUBRIC_DICT)
    text = "Introduction\nAlpha is here with citation (Smith, 2020).\nDiscussion\nMore words here for length."
    result = check_compliance(text, rubric)
    assert result.word_count_ok is True
    assert result.sections_ok is True
    assert result.citations_ok is True


def test_check_compliance_flags_failures():
    rubric = load_rubric_dict(RUBRIC_DICT)
    text = "Introduction\nShort."
    result = check_compliance(text, rubric)
    assert result.sections_ok is False
    assert result.sections_found == {"Introduction": True, "Discussion": False}
    assert result.citations_ok is False


def test_check_compliance_word_count_too_long():
    rubric = load_rubric_dict(RUBRIC_DICT)
    text = "Introduction\nDiscussion\n" + ("word " * 60) + "(Smith, 2020)"
    result = check_compliance(text, rubric)
    assert result.word_count_ok is False

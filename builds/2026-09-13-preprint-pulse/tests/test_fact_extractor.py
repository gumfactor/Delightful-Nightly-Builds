"""Tests for fact_extractor.py — regex extraction of reported statistics."""

from __future__ import annotations

from datetime import date

from arxiv_client import Paper
from fact_extractor import extract_facts, extract_facts_from_text


def _paper(arxiv_id: str, title: str, abstract: str) -> Paper:
    return Paper(
        arxiv_id=arxiv_id,
        title=title,
        authors=["Author"],
        abstract=abstract,
        published=date(2026, 8, 1),
        categories=["q-bio.NC"],
        pdf_url=f"http://arxiv.org/pdf/{arxiv_id}",
    )


CRAFTED_SENTENCE = (
    "In a sample of N = 84 participants, cortisol reactivity correlated with "
    "anxiety (r = .32, p < .001; d = 0.45)."
)


def test_extract_facts_from_text_finds_all_four_types():
    results = extract_facts_from_text(CRAFTED_SENTENCE)
    types = {t for t, _, _ in results}
    assert types == {"sample_size", "p_value", "correlation", "effect_size"}

    raw_by_type = {t: raw for t, raw, _ in results}
    assert raw_by_type["sample_size"] == "N = 84"
    assert raw_by_type["p_value"] == "p < .001"
    assert raw_by_type["correlation"] == "r = .32"
    assert raw_by_type["effect_size"] == "d = 0.45"


def test_extract_facts_from_text_no_match_returns_empty():
    assert extract_facts_from_text("This abstract reports no numeric statistics at all.") == []


def test_extract_facts_from_text_context_includes_surrounding_words():
    results = extract_facts_from_text(CRAFTED_SENTENCE)
    for _, raw, context in results:
        assert raw in context


def test_extract_facts_from_text_multiple_matches_of_same_type():
    text = "Study 1 had N = 40 participants; Study 2 had N = 210 participants."
    results = extract_facts_from_text(text)
    sample_sizes = [raw for t, raw, _ in results if t == "sample_size"]
    assert sample_sizes == ["N = 40", "N = 210"]


def test_extract_facts_preserves_paper_order_and_attribution():
    papers = [
        _paper("p1", "First Paper", "N = 10 participants took part (p = 0.02)."),
        _paper("p2", "Second Paper", "No statistics reported here."),
        _paper("p3", "Third Paper", "A correlation was found (r = .55)."),
    ]
    facts = extract_facts(papers)
    assert [f.arxiv_id for f in facts] == ["p1", "p1", "p3"]
    assert facts[0].paper_title == "First Paper"
    assert facts[0].fact_type == "sample_size"
    assert facts[1].fact_type == "p_value"
    assert facts[2].paper_title == "Third Paper"
    assert facts[2].fact_type == "correlation"


def test_extract_facts_lowercase_n_is_also_matched():
    results = extract_facts_from_text("A subsample of n = 12 was excluded for motion.")
    assert any(t == "sample_size" and raw == "n = 12" for t, raw, _ in results)

"""Tests for outline_builder.py — hook-stat sentences and outline assembly."""

from __future__ import annotations

from datetime import date, datetime, timezone

from arxiv_client import Paper
from outline_builder import build_outline


def _paper(arxiv_id: str, published: date, abstract: str = "") -> Paper:
    return Paper(
        arxiv_id=arxiv_id,
        title=f"Title {arxiv_id}",
        authors=["Author"],
        abstract=abstract,
        published=published,
        categories=["q-bio.NC"],
        pdf_url=f"http://arxiv.org/pdf/{arxiv_id}",
    )


NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)


def test_hook_stat_defined_pct_change_rising():
    # Spread evenly across the 3 early and 3 late months (1/mo, then 2/mo) so
    # the least-squares slope is unambiguously "rising", not a near-threshold case.
    early_months = [date(2026, 4, 10), date(2026, 5, 10), date(2026, 6, 10)]
    late_months = [date(2026, 7, 5), date(2026, 7, 20), date(2026, 8, 5), date(2026, 8, 25), date(2026, 9, 1), date(2026, 9, 1)]
    papers = [_paper(f"e{i}", d) for i, d in enumerate(early_months)] + [
        _paper(f"l{i}", d) for i, d in enumerate(late_months)
    ]
    outline = build_outline(papers, "empathy training", window_months=6, now=NOW)
    assert "empathy training" in outline.hook_stat
    assert "grew" in outline.hook_stat
    assert "+100%" in outline.hook_stat
    assert "3" in outline.hook_stat and "6" in outline.hook_stat


def test_hook_stat_undefined_pct_change_when_first_half_empty():
    papers = [_paper(f"l{i}", date(2026, 8, 10)) for i in range(4)]
    outline = build_outline(papers, "novel topic", window_months=6, now=NOW)
    assert "None" not in outline.hook_stat
    assert "%" not in outline.hook_stat
    assert "second half" in outline.hook_stat


def test_hook_stat_zero_papers():
    outline = build_outline([], "an obscure topic", window_months=6, now=NOW)
    assert outline.total_papers == 0
    assert 'No arXiv papers matched "an obscure topic"' in outline.hook_stat


def test_top_papers_sorted_descending_and_capped_at_limit():
    papers = [_paper(f"p{i}", date(2026, 1, 1 + i)) for i in range(15)]
    outline = build_outline(papers, "topic", window_months=12, now=datetime(2026, 2, 1, tzinfo=timezone.utc))
    assert len(outline.top_papers) == 8
    published_dates = [p.published for p in outline.top_papers]
    assert published_dates == sorted(published_dates, reverse=True)
    assert outline.top_papers[0].arxiv_id == "p14"  # the most recent


def test_notable_facts_capped_at_limit():
    # 8 distinct sample-size matches in one abstract -> more than NOTABLE_FACTS_LIMIT (6).
    abstract = ", ".join(f"N = {10 * i}" for i in range(1, 9))
    papers = [_paper("p1", date(2026, 8, 1), abstract=abstract)]
    outline = build_outline(papers, "topic", window_months=6, now=NOW)
    assert len(outline.notable_facts) == 6


def test_outline_records_generated_at_timestamp():
    outline = build_outline([], "topic", window_months=6, now=NOW)
    assert outline.generated_at == NOW.isoformat()


def test_outline_total_papers_matches_input_length():
    papers = [_paper(f"p{i}", date(2026, 8, 1)) for i in range(5)]
    outline = build_outline(papers, "topic", window_months=6, now=NOW)
    assert outline.total_papers == 5

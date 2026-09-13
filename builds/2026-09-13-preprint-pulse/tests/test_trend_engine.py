"""Tests for trend_engine.py — bucketing, slope/direction, rising keywords.

Every expected value below was hand-computed before being encoded as an
assertion (see BUILD_LOG.md). `now` is fixed at 2026-09-01 throughout so the
6-month window always buckets to Apr, May, Jun, Jul, Aug, Sep 2026.
"""

from __future__ import annotations

from datetime import date

import pytest

from arxiv_client import Paper
from trend_engine import bucket_by_month, compute_trend, rising_keywords

NOW = date(2026, 9, 1)


def _paper(arxiv_id: str, published: date, title: str = "", abstract: str = "") -> Paper:
    return Paper(
        arxiv_id=arxiv_id,
        title=title or f"Paper {arxiv_id}",
        authors=["Author"],
        abstract=abstract,
        published=published,
        categories=["q-bio.NC"],
        pdf_url=f"http://arxiv.org/pdf/{arxiv_id}",
    )


def _rising_corpus() -> list[Paper]:
    """1 paper/month Apr-Jun, 2 papers/month Jul-Sep -> counts [1,1,1,2,2,2]."""
    dates = [
        date(2026, 4, 10),
        date(2026, 5, 12),
        date(2026, 6, 15),
        date(2026, 7, 5),
        date(2026, 7, 20),
        date(2026, 8, 3),
        date(2026, 8, 25),
        date(2026, 9, 1),
        date(2026, 9, 1),
    ]
    # That's 9 dates but we want exactly [1,1,1,2,2,2] = 9 papers total. Recount:
    # Apr:1 May:1 Jun:1 Jul:2 Aug:2 Sep:2 = 9. Matches `dates` above (Jul has 2: idx3,4; Aug has 2: idx5,6; Sep has 2: idx7,8).
    return [_paper(f"p{i}", d) for i, d in enumerate(dates)]


def test_month_labels_via_bucket_by_month():
    buckets = bucket_by_month([], months=6, now=NOW)
    labels = [b.period_label for b in buckets]
    assert labels == ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]
    assert all(b.count == 0 for b in buckets)


def test_bucket_by_month_counts_match_hand_worked_corpus():
    papers = _rising_corpus()
    buckets = bucket_by_month(papers, months=6, now=NOW)
    counts = [b.count for b in buckets]
    assert counts == [1, 1, 1, 2, 2, 2]


def test_compute_trend_rising_matches_hand_computed_slope():
    trend = compute_trend(_rising_corpus(), months=6, now=NOW)
    # Hand-computed least-squares slope for y=[1,1,1,2,2,2], x=0..5: 4.5 / 17.5
    assert trend.slope == pytest.approx(4.5 / 17.5, abs=1e-9)
    assert trend.direction == "rising"
    assert trend.first_half_count == 3
    assert trend.second_half_count == 6
    assert trend.pct_change == pytest.approx(100.0)


def test_compute_trend_declining_is_the_mirror_of_rising():
    dates = [
        date(2026, 4, 5), date(2026, 4, 20),
        date(2026, 5, 10), date(2026, 5, 25),
        date(2026, 6, 15), date(2026, 6, 20),
        date(2026, 7, 10),
        date(2026, 8, 10),
        date(2026, 9, 1),
    ]  # counts [2,2,2,1,1,1]
    papers = [_paper(f"d{i}", d) for i, d in enumerate(dates)]
    trend = compute_trend(papers, months=6, now=NOW)
    assert [b.count for b in trend.buckets] == [2, 2, 2, 1, 1, 1]
    assert trend.slope == pytest.approx(-4.5 / 17.5, abs=1e-9)
    assert trend.direction == "declining"
    assert trend.first_half_count == 6
    assert trend.second_half_count == 3
    assert trend.pct_change == pytest.approx(-50.0)


def test_compute_trend_flat_when_counts_are_equal():
    dates = [date(2026, m, 10) for m in range(4, 10) for _ in range(2)]  # 2/month, all equal
    papers = [_paper(f"f{i}", d) for i, d in enumerate(dates)]
    trend = compute_trend(papers, months=6, now=NOW)
    assert trend.slope == pytest.approx(0.0, abs=1e-9)
    assert trend.direction == "flat"
    assert trend.pct_change == pytest.approx(0.0)


def test_compute_trend_single_bucket_edge_case_has_no_crash():
    papers = [_paper("s1", NOW), _paper("s2", NOW)]
    trend = compute_trend(papers, months=1, now=NOW)
    assert len(trend.buckets) == 1
    assert trend.slope == 0.0
    assert trend.direction == "flat"
    assert trend.first_half_count == 0  # half = 1 // 2 = 0
    assert trend.second_half_count == 2
    assert trend.pct_change is None  # undefined: first_half_count == 0


def test_compute_trend_empty_corpus_does_not_crash():
    trend = compute_trend([], months=6, now=NOW)
    assert trend.first_half_count == 0
    assert trend.second_half_count == 0
    assert trend.pct_change is None
    assert trend.direction == "flat"


def test_rising_keywords_detects_a_real_shift():
    early = [
        _paper("e1", date(2026, 4, 5), abstract="Amygdala reactivity was measured across trials."),
        _paper("e2", date(2026, 5, 5), abstract="Amygdala connectivity predicted anxiety scores."),
    ]
    late = [
        _paper("l1", date(2026, 8, 1), abstract="Cortisol levels tracked stress across the cohort."),
        _paper("l2", date(2026, 8, 10), abstract="Cortisol reactivity correlated with cortisol awakening response."),
        _paper("l3", date(2026, 8, 20), abstract="A new cortisol biomarker was proposed for chronic stress."),
    ]
    keywords = rising_keywords(early + late, months=6, now=NOW, min_support=2)
    assert "cortisol" in keywords
    assert "amygdala" not in keywords  # only appears early -> declining, filtered out (score <= 0)


def test_rising_keywords_respects_min_support_floor():
    papers = [
        _paper("a", date(2026, 4, 1), abstract="A rare neologism appears exactly once."),
        _paper("b", date(2026, 8, 1), abstract="Common terminology about stress research."),
        _paper("c", date(2026, 8, 5), abstract="More common terminology about stress research."),
    ]
    keywords = rising_keywords(papers, months=6, now=NOW, min_support=2)
    assert "neologism" not in keywords  # total support = 1, below the floor
    assert "terminology" in keywords  # appears in 2 late papers, 0 early -> rising, support 2


def test_rising_keywords_empty_corpus_returns_empty_list():
    assert rising_keywords([], months=6, now=NOW) == []

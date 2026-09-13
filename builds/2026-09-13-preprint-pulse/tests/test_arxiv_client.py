"""Tests for arxiv_client.py — Atom parsing, pagination, caching, errors."""

from __future__ import annotations

import urllib.error
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from arxiv_client import (
    ArxivClientError,
    Paper,
    _build_query,
    fetch_papers,
    parse_atom_response,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_arxiv_response.xml"
FIXTURE_XML = FIXTURE_PATH.read_text(encoding="utf-8")

EMPTY_FEED = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"></feed>"""

INCOMPLETE_ENTRY_FEED = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Missing id and published date</title>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2609.00001v1</id>
    <published>2026-09-01T00:00:00Z</published>
    <title>Valid Entry</title>
    <summary>An abstract.</summary>
  </entry>
</feed>"""


class FakeResponse:
    def __init__(self, text: str):
        self._text = text

    def read(self):
        return self._text.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_parse_atom_response_basic():
    papers = parse_atom_response(FIXTURE_XML)
    assert len(papers) == 2

    p1, p2 = papers
    assert p1.arxiv_id == "2608.12345v1"
    assert p1.title == "Cortisol Reactivity and Amygdala Connectivity in Chronic Stress"
    assert p1.authors == ["A. Researcher", "B. Collaborator"]
    assert p1.published == date(2026, 8, 20)
    assert p1.categories == ["q-bio.NC"]
    assert p1.pdf_url == "http://arxiv.org/pdf/2608.12345v1"
    assert "N = 84" in p1.abstract

    # Second entry has no explicit pdf link -> derived from the abs id.
    assert p2.arxiv_id == "2607.54321v2"
    assert p2.pdf_url == "http://arxiv.org/pdf/2607.54321v2"
    assert p2.categories == ["q-bio.NC", "cs.CY"]


def test_parse_atom_response_empty_feed_returns_empty_list():
    assert parse_atom_response(EMPTY_FEED) == []


def test_parse_atom_response_skips_incomplete_entries():
    papers = parse_atom_response(INCOMPLETE_ENTRY_FEED)
    assert len(papers) == 1
    assert papers[0].title == "Valid Entry"


def test_parse_atom_response_malformed_xml_raises():
    with pytest.raises(ArxivClientError):
        parse_atom_response("not xml at all <<<")


def test_build_query_quotes_multiword_topics():
    assert _build_query("large language models", None) == 'all:"large language models"'
    assert _build_query("empathy", None) == "all:empathy"


def test_build_query_adds_category_filter():
    query = _build_query("empathy", ["q-bio.NC", "cs.CY"])
    assert query == 'all:empathy AND (cat:q-bio.NC OR cat:cs.CY)'


def test_fetch_papers_network_error_raises_client_error():
    def raising_urlopen(url, timeout=30):
        raise urllib.error.URLError("connection refused")

    with pytest.raises(ArxivClientError):
        fetch_papers("empathy", urlopen=raising_urlopen, sleep=lambda s: None)


def test_fetch_papers_stops_paginating_once_page_is_short():
    calls = {"count": 0}

    def fake_urlopen(url, timeout=30):
        calls["count"] += 1
        return FakeResponse(FIXTURE_XML)  # always returns 2 entries < PAGE_SIZE

    papers = fetch_papers(
        "affective neuroscience",
        months=24,
        max_results=150,
        urlopen=fake_urlopen,
        sleep=lambda s: None,
        now=datetime(2026, 9, 13, tzinfo=timezone.utc),
    )
    assert len(papers) == 2
    assert calls["count"] == 1  # short page (2 < PAGE_SIZE of 50) stops the loop


def test_fetch_papers_deduplicates_and_stops_at_cutoff():
    # First page has the two fixture papers (2026-08-20 and 2026-07-05).
    # A narrow 1-month window with `now` on 2026-09-13 should exclude the
    # 2026-07-05 paper (below cutoff) without needing a second page.
    def fake_urlopen(url, timeout=30):
        return FakeResponse(FIXTURE_XML)

    papers = fetch_papers(
        "affective neuroscience",
        months=1,
        max_results=150,
        urlopen=fake_urlopen,
        sleep=lambda s: None,
        now=datetime(2026, 9, 13, tzinfo=timezone.utc),
    )
    ids = {p.arxiv_id for p in papers}
    assert "2608.12345v1" in ids
    assert "2607.54321v2" not in ids


def test_fetch_papers_cache_round_trip(tmp_path: Path):
    calls = {"count": 0}

    def fake_urlopen(url, timeout=30):
        calls["count"] += 1
        return FakeResponse(FIXTURE_XML)

    now = datetime(2026, 9, 13, tzinfo=timezone.utc)
    cache_dir = tmp_path / "cache"

    first = fetch_papers(
        "affective neuroscience",
        months=24,
        cache_dir=cache_dir,
        urlopen=fake_urlopen,
        sleep=lambda s: None,
        now=now,
    )
    assert calls["count"] == 1
    assert len(first) == 2

    def failing_urlopen(url, timeout=30):
        raise AssertionError("should not hit the network on a cache hit")

    second = fetch_papers(
        "affective neuroscience",
        months=24,
        cache_dir=cache_dir,
        urlopen=failing_urlopen,
        sleep=lambda s: None,
        now=now,  # same instant -> well within TTL
    )
    assert len(second) == 2
    assert {p.arxiv_id for p in second} == {p.arxiv_id for p in first}


def test_fetch_papers_cache_expires_after_ttl(tmp_path: Path):
    calls = {"count": 0}

    def fake_urlopen(url, timeout=30):
        calls["count"] += 1
        return FakeResponse(FIXTURE_XML)

    cache_dir = tmp_path / "cache"
    first_now = datetime(2026, 9, 13, tzinfo=timezone.utc)
    fetch_papers(
        "affective neuroscience",
        months=24,
        cache_dir=cache_dir,
        cache_ttl_hours=1,
        urlopen=fake_urlopen,
        sleep=lambda s: None,
        now=first_now,
    )
    assert calls["count"] == 1

    later_now = datetime(2026, 9, 14, tzinfo=timezone.utc)  # 24h later, TTL was 1h
    fetch_papers(
        "affective neuroscience",
        months=24,
        cache_dir=cache_dir,
        cache_ttl_hours=1,
        urlopen=fake_urlopen,
        sleep=lambda s: None,
        now=later_now,
    )
    assert calls["count"] == 2  # cache was stale -> refetched


def test_paper_to_dict_and_from_dict_round_trip():
    paper = Paper(
        arxiv_id="2609.00001v1",
        title="Test Paper",
        authors=["X. Author"],
        abstract="An abstract.",
        published=date(2026, 9, 1),
        categories=["q-bio.NC"],
        pdf_url="http://arxiv.org/pdf/2609.00001v1",
    )
    restored = Paper.from_dict(paper.to_dict())
    assert restored == paper

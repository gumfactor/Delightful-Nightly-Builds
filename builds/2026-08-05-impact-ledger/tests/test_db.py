"""Tests for SQLite persistence, snapshot dedup, and trend/velocity queries."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import db  # noqa: E402

AUTHOR = {
    "author_id": "A1",
    "display_name": "Jane Doe",
    "works_count": 2,
    "cited_by_count": 15,
    "h_index": 3,
    "i10_index": 1,
}

WORK_A = {
    "work_id": "W1",
    "title": "First Paper",
    "publication_year": 2020,
    "doi": "10.1/a",
    "host_venue": "Journal A",
    "cited_by_count": 10,
    "concepts": ["Neuroscience"],
    "abstract": "An early finding.",
}

WORK_B = {
    "work_id": "W2",
    "title": "Second Paper",
    "publication_year": 2022,
    "doi": "10.1/b",
    "host_venue": "Journal B",
    "cited_by_count": 5,
    "concepts": ["Statistics"],
    "abstract": "A later finding.",
}


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(tmp_path / "test.db")
    yield connection
    connection.close()


def test_upsert_author_inserts_and_updates(conn):
    db.upsert_author(conn, AUTHOR, "2026-08-01")
    stored = db.get_author(conn, "A1")
    assert stored["display_name"] == "Jane Doe"
    assert stored["last_synced"] == "2026-08-01"

    updated = {**AUTHOR, "cited_by_count": 20}
    db.upsert_author(conn, updated, "2026-08-02")
    stored_again = db.get_author(conn, "A1")
    assert stored_again["cited_by_count"] == 20
    assert stored_again["last_synced"] == "2026-08-02"


def test_get_author_returns_none_when_missing(conn):
    assert db.get_author(conn, "does-not-exist") is None


def test_same_day_resync_does_not_duplicate_rows(conn):
    db.upsert_work_snapshot(conn, "A1", WORK_A, "2026-08-01")
    db.upsert_work_snapshot(conn, "A1", {**WORK_A, "cited_by_count": 11}, "2026-08-01")

    rows = conn.execute(
        "SELECT COUNT(*) AS n FROM work_snapshots WHERE work_id = ? AND sync_date = ?",
        ("W1", "2026-08-01"),
    ).fetchone()
    assert rows["n"] == 1

    latest = db.latest_snapshot(conn, "A1")
    assert latest[0]["cited_by_count"] == 11


def test_later_day_sync_adds_new_distinct_date(conn):
    db.upsert_work_snapshot(conn, "A1", WORK_A, "2026-08-01")
    db.upsert_work_snapshot(conn, "A1", WORK_A, "2026-08-02")

    dates = db.distinct_sync_dates(conn, "A1")
    assert dates == ["2026-08-01", "2026-08-02"]


def test_citation_trend_aggregates_per_date(conn):
    db.upsert_work_snapshot(conn, "A1", WORK_A, "2026-08-01")
    db.upsert_work_snapshot(conn, "A1", WORK_B, "2026-08-01")
    db.upsert_work_snapshot(conn, "A1", {**WORK_A, "cited_by_count": 12}, "2026-08-02")
    db.upsert_work_snapshot(conn, "A1", {**WORK_B, "cited_by_count": 6}, "2026-08-02")

    trend = db.citation_trend(conn, "A1")
    assert trend == [
        {"sync_date": "2026-08-01", "total_citations": 15},
        {"sync_date": "2026-08-02", "total_citations": 18},
    ]


def test_rising_papers_empty_with_one_snapshot(conn):
    db.upsert_work_snapshot(conn, "A1", WORK_A, "2026-08-01")
    assert db.rising_papers(conn, "A1") == []


def test_rising_papers_detects_citation_increase(conn):
    db.upsert_work_snapshot(conn, "A1", WORK_A, "2026-08-01")
    db.upsert_work_snapshot(conn, "A1", {**WORK_A, "cited_by_count": 14}, "2026-08-02")

    rising = db.rising_papers(conn, "A1")
    assert len(rising) == 1
    assert rising[0]["velocity"] == 4
    assert rising[0]["previous_cited_by_count"] == 10
    assert rising[0]["cited_by_count"] == 14


def test_rising_papers_excludes_unchanged_and_decreased(conn):
    db.upsert_work_snapshot(conn, "A1", WORK_A, "2026-08-01")
    db.upsert_work_snapshot(conn, "A1", WORK_B, "2026-08-01")
    db.upsert_work_snapshot(conn, "A1", WORK_A, "2026-08-02")  # unchanged
    db.upsert_work_snapshot(conn, "A1", {**WORK_B, "cited_by_count": 3}, "2026-08-02")  # decreased

    rising = db.rising_papers(conn, "A1")
    assert rising == []


def test_rising_papers_excludes_papers_new_in_latest_snapshot(conn):
    db.upsert_work_snapshot(conn, "A1", WORK_A, "2026-08-01")
    db.upsert_work_snapshot(conn, "A1", WORK_A, "2026-08-02")
    db.upsert_work_snapshot(conn, "A1", WORK_B, "2026-08-02")  # first appears on day 2

    rising = db.rising_papers(conn, "A1")
    assert all(paper["work_id"] != "W2" for paper in rising)


def test_latest_snapshot_returns_empty_before_any_sync(conn):
    assert db.latest_snapshot(conn, "A1") == []

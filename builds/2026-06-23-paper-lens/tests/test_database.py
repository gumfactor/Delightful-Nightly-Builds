"""Tests for database.py — SQLite persistence."""
import sys
import sqlite3
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database import init_db, insert_paper, get_papers, mark_as_read, search_papers


@pytest.fixture
def tmp_db(tmp_path):
    db = tmp_path / "test_papers.db"
    init_db(db)
    return db


def _make_paper(arxiv_id="2410.00001", title="Test Paper", relevance=7, topic_label=""):
    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": "Alice Smith, Bob Jones",
        "abstract": "Test abstract about brain imaging methods.",
        "published_date": "2024-10-01",
        "fetched_date": "2024-10-15T10:00:00",
        "relevance_score": relevance,
        "summary": "Two sentence summary about methodology.",
        "methodology": "fMRI",
        "topic_label": topic_label,
    }


def test_init_creates_papers_table(tmp_db):
    with sqlite3.connect(str(tmp_db)) as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='papers'"
        ).fetchall()
    assert len(tables) == 1


def test_insert_paper_stores_all_fields(tmp_db):
    paper = _make_paper(topic_label="empathy neuroscience")
    result = insert_paper(paper, tmp_db)
    assert result is True
    papers = get_papers(tmp_db)
    assert len(papers) == 1
    p = papers[0]
    assert p["arxiv_id"] == "2410.00001"
    assert p["title"] == "Test Paper"
    assert p["relevance_score"] == 7
    assert p["methodology"] == "fMRI"
    assert p["topic_label"] == "empathy neuroscience"


def test_insert_duplicate_arxiv_id_returns_false(tmp_db):
    paper = _make_paper()
    assert insert_paper(paper, tmp_db) is True
    assert insert_paper(paper, tmp_db) is False
    # Only one copy in DB
    assert len(get_papers(tmp_db)) == 1


def test_mark_as_read_sets_flag(tmp_db):
    insert_paper(_make_paper(), tmp_db)
    result = mark_as_read("2410.00001", tmp_db)
    assert result is True
    papers = get_papers(tmp_db)
    assert papers[0]["is_read"] == 1


def test_mark_as_read_unknown_id_returns_false(tmp_db):
    result = mark_as_read("9999.99999", tmp_db)
    assert result is False


def test_get_papers_returns_empty_list_when_db_empty(tmp_db):
    papers = get_papers(tmp_db)
    assert papers == []


def test_get_papers_orders_by_relevance_descending(tmp_db):
    insert_paper(_make_paper("2410.00001", "Low Rel", relevance=3), tmp_db)
    insert_paper(_make_paper("2410.00002", "High Rel", relevance=9), tmp_db)
    insert_paper(_make_paper("2410.00003", "Mid Rel", relevance=6), tmp_db)
    papers = get_papers(tmp_db)
    scores = [p["relevance_score"] for p in papers]
    assert scores == sorted(scores, reverse=True)


def test_search_papers_matches_title(tmp_db):
    insert_paper(_make_paper("2410.00001", "Empathy in Psychopaths"), tmp_db)
    insert_paper(_make_paper("2410.00002", "Stress Hormones Study"), tmp_db)
    results = search_papers("empathy", tmp_db)
    assert len(results) == 1
    assert results[0]["arxiv_id"] == "2410.00001"


def test_search_papers_matches_summary(tmp_db):
    paper = _make_paper()
    paper["summary"] = "Cortisol levels in HPA axis research"
    insert_paper(paper, tmp_db)
    results = search_papers("cortisol", tmp_db)
    assert len(results) == 1


def test_search_papers_no_match_returns_empty(tmp_db):
    insert_paper(_make_paper(), tmp_db)
    results = search_papers("zzznomatchzzz", tmp_db)
    assert results == []

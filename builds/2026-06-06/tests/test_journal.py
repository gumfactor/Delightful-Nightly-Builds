"""Tests for Journal: add, list, get, and projects operations."""

from pathlib import Path

import pytest
from src.journal import Journal
from src.storage import Storage
from src.models import Session


def make_journal(tmp_path: Path) -> Journal:
    return Journal(Storage(tmp_path / "sessions.json"))


def test_add_session_returns_session_with_correct_fields(tmp_path: Path):
    journal = make_journal(tmp_path)
    s = journal.add_session(
        project="canada-list",
        summary="Fixed the duplicate-key bug in product indexer",
    )
    assert s.project == "canada-list"
    assert s.summary == "Fixed the duplicate-key bug in product indexer"
    assert s.id  # non-empty


def test_add_session_persists_to_storage(tmp_path: Path):
    journal = make_journal(tmp_path)
    journal.add_session(project="proj", summary="something")
    sessions = journal.storage.load_all()
    assert len(sessions) == 1


def test_list_sessions_returns_most_recent_first(tmp_path: Path):
    """Ordering must be reverse chronological regardless of insertion order."""
    storage = Storage(tmp_path / "sessions.json")
    older = Session(
        id="aaaa0001",
        timestamp="2026-06-04T10:00:00Z",
        project="proj",
        summary="older session",
        context="",
        next_steps=[],
        files=[],
        tags=[],
    )
    newer = Session(
        id="bbbb0002",
        timestamp="2026-06-06T10:00:00Z",
        project="proj",
        summary="newer session",
        context="",
        next_steps=[],
        files=[],
        tags=[],
    )
    storage.save_all([older, newer])
    journal = Journal(storage)

    sessions = journal.list_sessions()
    assert sessions[0].summary == "newer session"
    assert sessions[1].summary == "older session"


def test_list_sessions_filters_by_project(tmp_path: Path):
    journal = make_journal(tmp_path)
    journal.add_session(project="canada-list", summary="Fixed CSV parser")
    journal.add_session(project="lab-admin", summary="Grant deadline tracking")
    journal.add_session(project="canada-list", summary="Updated search index")

    results = journal.list_sessions(project="canada-list")
    assert len(results) == 2
    assert all(s.project == "canada-list" for s in results)


def test_list_sessions_respects_limit(tmp_path: Path):
    journal = make_journal(tmp_path)
    for i in range(8):
        journal.add_session(project="proj", summary=f"entry {i}")

    results = journal.list_sessions(limit=3)
    assert len(results) == 3


def test_list_sessions_returns_all_when_limit_exceeds_count(tmp_path: Path):
    journal = make_journal(tmp_path)
    journal.add_session(project="proj", summary="only one entry")
    results = journal.list_sessions(limit=100)
    assert len(results) == 1


def test_get_session_by_id_returns_correct_session(tmp_path: Path):
    journal = make_journal(tmp_path)
    added = journal.add_session(project="proj", summary="find me by ID")
    found = journal.get_session(added.id)
    assert found is not None
    assert found.id == added.id
    assert found.summary == "find me by ID"


def test_get_session_returns_none_for_unknown_id(tmp_path: Path):
    journal = make_journal(tmp_path)
    journal.add_session(project="proj", summary="some session")
    assert journal.get_session("nonexistent") is None


def test_get_projects_returns_sorted_unique_names(tmp_path: Path):
    journal = make_journal(tmp_path)
    journal.add_session(project="zebra-project", summary="a")
    journal.add_session(project="alpha-project", summary="b")
    journal.add_session(project="zebra-project", summary="c")  # duplicate

    projects = journal.get_projects()
    assert projects == ["alpha-project", "zebra-project"]


def test_get_projects_returns_empty_list_when_no_sessions(tmp_path: Path):
    journal = make_journal(tmp_path)
    assert journal.get_projects() == []

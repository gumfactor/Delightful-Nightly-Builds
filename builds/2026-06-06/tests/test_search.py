"""Tests for full-text search across session fields."""

from src.models import Session
from src.search import search_sessions


def make_session(
    project: str = "test-proj",
    summary: str = "",
    context: str = "",
    tags: list | None = None,
    files: list | None = None,
    next_steps: list | None = None,
) -> Session:
    return Session.create(
        project=project,
        summary=summary,
        context=context or "",
        tags=tags or [],
        files=files or [],
        next_steps=next_steps or [],
    )


def test_search_finds_match_in_summary():
    sessions = [make_session(summary="debugging JWT authentication logic")]
    assert len(search_sessions(sessions, "jwt")) == 1


def test_search_is_case_insensitive():
    sessions = [make_session(summary="Working on Canada List ingestion pipeline")]
    assert len(search_sessions(sessions, "CANADA LIST")) == 1


def test_search_no_match_returns_empty_list():
    sessions = [make_session(summary="database schema migration")]
    assert search_sessions(sessions, "fmri preprocessing") == []


def test_search_empty_query_returns_empty_list():
    sessions = [make_session(summary="something relevant")]
    assert search_sessions(sessions, "") == []


def test_search_filters_results_by_project():
    sessions = [
        make_session(project="proj-a", summary="fixing the import bug"),
        make_session(project="proj-b", summary="fixing the export bug"),
    ]
    results = search_sessions(sessions, "bug", project="proj-a")
    assert len(results) == 1
    assert results[0].project == "proj-a"


def test_search_finds_match_in_tags():
    sessions = [make_session(summary="doing analysis", tags=["neuroimaging", "fsl", "fmri"])]
    assert len(search_sessions(sessions, "fsl")) == 1


def test_search_finds_match_in_files():
    sessions = [make_session(summary="refactoring", files=["src/preprocess.py", "tests/test_preprocess.py"])]
    assert len(search_sessions(sessions, "preprocess")) == 1


def test_search_finds_match_in_context():
    sessions = [make_session(
        summary="working on auth",
        context="Redis is being used to store refresh tokens with 7-day TTL",
    )]
    assert len(search_sessions(sessions, "redis")) == 1


def test_search_finds_match_in_next_steps():
    sessions = [make_session(
        summary="continued work",
        next_steps=["Implement Bayesian model comparison"],
    )]
    assert len(search_sessions(sessions, "bayesian")) == 1


def test_search_returns_multiple_matches():
    sessions = [
        make_session(summary="csv parsing logic"),
        make_session(summary="csv export feature"),
        make_session(summary="json schema validator"),
    ]
    results = search_sessions(sessions, "csv")
    assert len(results) == 2


def test_search_project_filter_is_case_insensitive():
    sessions = [make_session(project="Canada-List", summary="something")]
    results = search_sessions(sessions, "something", project="canada-list")
    assert len(results) == 1

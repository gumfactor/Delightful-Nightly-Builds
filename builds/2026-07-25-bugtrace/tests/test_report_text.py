import pytest

from src import store
from src.report_text import render_text


@pytest.fixture
def conn(tmp_path):
    return store.init_db(str(tmp_path / "bugtrace.db"))


def test_empty_report_says_no_commits(conn):
    text = render_text(conn)
    assert "No fix commits recorded yet" in text


def test_report_lists_categories_with_percentages(conn):
    store.upsert_fix(conn, "o/r", "s1", "fix", "2026-06-01T00:00:00Z", "type_mismatch", "keyword", "e", "d")
    store.upsert_fix(conn, "o/r", "s2", "fix", "2026-06-02T00:00:00Z", "type_mismatch", "keyword", "e", "d")
    store.upsert_fix(conn, "o/r", "s3", "fix", "2026-06-03T00:00:00Z", "typo_naming", "keyword", "e", "d")
    text = render_text(conn)
    assert "3 classified fix commit(s)" in text
    assert "Type mismatch" in text
    assert "66.7%" in text or "66.6%" in text


def test_report_includes_repo_breakdown(conn):
    store.upsert_fix(conn, "owner/repo-a", "s1", "fix", "2026-06-01T00:00:00Z", "type_mismatch", "keyword", "e", "d")
    text = render_text(conn)
    assert "owner/repo-a" in text

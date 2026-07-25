import pytest

from src import store


@pytest.fixture
def conn(tmp_path):
    db_path = tmp_path / "bugtrace.db"
    return store.init_db(str(db_path))


def _insert(conn, repo="owner/repo", sha="sha1", category="type_mismatch", date="2026-06-01T10:00:00Z"):
    store.upsert_fix(conn, repo, sha, "fix message", date, category, "keyword", "explanation", "diff excerpt")


def test_upsert_and_get_all_fixes(conn):
    _insert(conn, sha="sha1")
    fixes = store.get_all_fixes(conn)
    assert len(fixes) == 1
    assert fixes[0]["sha"] == "sha1"


def test_upsert_dedupes_same_repo_and_sha(conn):
    _insert(conn, sha="sha1", category="type_mismatch")
    # Re-sync with a different category should NOT overwrite the original classification.
    store.upsert_fix(conn, "owner/repo", "sha1", "fix message", "2026-06-01T10:00:00Z", "other", "ai", "changed", "diff")
    fixes = store.get_all_fixes(conn)
    assert len(fixes) == 1
    assert fixes[0]["category"] == "type_mismatch"


def test_is_known(conn):
    assert not store.is_known(conn, "owner/repo", "sha1")
    _insert(conn, sha="sha1")
    assert store.is_known(conn, "owner/repo", "sha1")


def test_different_repos_same_sha_not_deduped(conn):
    _insert(conn, repo="owner/repo-a", sha="sha1")
    _insert(conn, repo="owner/repo-b", sha="sha1")
    assert len(store.get_all_fixes(conn)) == 2


def test_category_counts(conn):
    _insert(conn, sha="s1", category="type_mismatch")
    _insert(conn, sha="s2", category="type_mismatch")
    _insert(conn, sha="s3", category="typo_naming")
    counts = store.category_counts(conn)
    assert counts[0] == {"category": "type_mismatch", "count": 2}
    assert counts[1] == {"category": "typo_naming", "count": 1}


def test_monthly_counts(conn):
    _insert(conn, sha="s1", date="2026-06-01T10:00:00Z")
    _insert(conn, sha="s2", date="2026-06-15T10:00:00Z")
    _insert(conn, sha="s3", date="2026-07-01T10:00:00Z")
    monthly = store.monthly_counts(conn)
    assert {"month": "2026-06", "count": 2} in monthly
    assert {"month": "2026-07", "count": 1} in monthly


def test_repo_counts(conn):
    _insert(conn, repo="owner/repo-a", sha="s1")
    _insert(conn, repo="owner/repo-b", sha="s2")
    _insert(conn, repo="owner/repo-a", sha="s3")
    counts = store.repo_counts(conn)
    assert counts[0] == {"repo": "owner/repo-a", "count": 2}


def test_empty_database_returns_empty_lists(conn):
    assert store.get_all_fixes(conn) == []
    assert store.category_counts(conn) == []
    assert store.monthly_counts(conn) == []

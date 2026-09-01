import pytest

from src import store


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    connection = store.connect(db_path)
    yield connection
    connection.close()


def test_insert_and_read_back(conn):
    store.upsert_snapshot(conn, "user/repo", "python", "requests", "2.31.0", "exact", "2.32.0", "2026-09-01")
    store.commit(conn)
    rows = store.snapshots_for_date(conn, "2026-09-01")
    assert len(rows) == 1
    assert rows[0]["dependency"] == "requests"
    assert rows[0]["pinned_version"] == "2.31.0"


def test_same_day_resync_upserts_without_duplicating(conn):
    store.upsert_snapshot(conn, "user/repo", "python", "requests", "2.31.0", "exact", "2.32.0", "2026-09-01")
    store.upsert_snapshot(conn, "user/repo", "python", "requests", "2.31.1", "exact", "2.32.0", "2026-09-01")
    store.commit(conn)
    rows = store.snapshots_for_date(conn, "2026-09-01")
    assert len(rows) == 1
    assert rows[0]["pinned_version"] == "2.31.1"


def test_different_dates_accumulate_history(conn):
    store.upsert_snapshot(conn, "user/repo", "python", "requests", "2.31.0", "exact", "2.32.0", "2026-09-01")
    store.upsert_snapshot(conn, "user/repo", "python", "requests", "2.31.1", "exact", "2.32.0", "2026-09-02")
    store.commit(conn)
    history = store.history_for_dependency(conn, "python", "requests")
    assert [row["fetched_at_date"] for row in history] == ["2026-09-01", "2026-09-02"]


def test_latest_snapshot_date_returns_max_date(conn):
    store.upsert_snapshot(conn, "user/repo", "python", "requests", "2.31.0", "exact", "2.32.0", "2026-09-01")
    store.upsert_snapshot(conn, "user/repo", "python", "requests", "2.31.1", "exact", "2.32.0", "2026-09-03")
    store.commit(conn)
    assert store.latest_snapshot_date(conn) == "2026-09-03"


def test_latest_snapshot_date_none_when_empty(conn):
    assert store.latest_snapshot_date(conn) is None


def test_different_repos_same_dependency_both_stored(conn):
    store.upsert_snapshot(conn, "user/repo-a", "python", "requests", "2.31.0", "exact", "2.32.0", "2026-09-01")
    store.upsert_snapshot(conn, "user/repo-b", "python", "requests", "2.28.0", "exact", "2.32.0", "2026-09-01")
    store.commit(conn)
    rows = store.snapshots_for_date(conn, "2026-09-01")
    assert len(rows) == 2
    assert {row["repo"] for row in rows} == {"user/repo-a", "user/repo-b"}

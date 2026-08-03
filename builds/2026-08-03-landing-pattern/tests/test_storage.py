"""Tests for SQLite snapshot persistence."""

from __future__ import annotations

from landing_pattern import storage


def make_report(repo="owner/repo", synced_at="2026-08-03T12:00:00+00:00", prs=None):
    return {
        "repo": repo,
        "synced_at": synced_at,
        "prs": prs or [],
        "batch1": [],
        "batch2": [],
        "blocked": [],
        "drafts": [],
        "overlap_graph": {},
    }


def test_save_and_read_latest_snapshot(tmp_path):
    conn = storage.connect(str(tmp_path / "db.sqlite"))
    report = make_report()
    storage.save_snapshot(conn, report)
    latest = storage.latest_snapshot(conn, "owner/repo")
    assert latest["repo"] == "owner/repo"
    conn.close()


def test_latest_snapshot_returns_none_for_unseen_repo(tmp_path):
    conn = storage.connect(str(tmp_path / "db.sqlite"))
    assert storage.latest_snapshot(conn, "owner/never-synced") is None
    conn.close()


def test_two_syncs_create_two_distinct_rows_not_an_overwrite(tmp_path):
    conn = storage.connect(str(tmp_path / "db.sqlite"))
    storage.save_snapshot(conn, make_report(synced_at="2026-08-01T00:00:00+00:00"))
    storage.save_snapshot(conn, make_report(synced_at="2026-08-02T00:00:00+00:00"))
    count = conn.execute("SELECT COUNT(*) FROM syncs WHERE repo = ?", ("owner/repo",)).fetchone()[0]
    assert count == 2
    conn.close()


def test_latest_snapshot_returns_most_recent_by_time(tmp_path):
    conn = storage.connect(str(tmp_path / "db.sqlite"))
    storage.save_snapshot(conn, make_report(synced_at="2026-08-01T00:00:00+00:00"))
    storage.save_snapshot(conn, make_report(synced_at="2026-08-02T00:00:00+00:00"))
    latest = storage.latest_snapshot(conn, "owner/repo")
    assert latest["synced_at"] == "2026-08-02T00:00:00+00:00"
    conn.close()


def test_snapshot_by_id_returns_specific_row(tmp_path):
    conn = storage.connect(str(tmp_path / "db.sqlite"))
    run_id = storage.save_snapshot(conn, make_report(synced_at="2026-08-01T00:00:00+00:00"))
    storage.save_snapshot(conn, make_report(synced_at="2026-08-02T00:00:00+00:00"))
    snapshot = storage.snapshot_by_id(conn, run_id)
    assert snapshot["synced_at"] == "2026-08-01T00:00:00+00:00"
    conn.close()


def test_snapshot_by_id_returns_none_for_missing_id(tmp_path):
    conn = storage.connect(str(tmp_path / "db.sqlite"))
    assert storage.snapshot_by_id(conn, 999) is None
    conn.close()


def test_history_for_pr_returns_chronological_trend(tmp_path):
    conn = storage.connect(str(tmp_path / "db.sqlite"))
    pr = {"number": 42, "label": "ci_failing", "age_days": 1}
    storage.save_snapshot(
        conn, make_report(synced_at="2026-08-01T00:00:00+00:00", prs=[pr])
    )
    pr2 = {"number": 42, "label": "ready", "age_days": 2}
    storage.save_snapshot(
        conn, make_report(synced_at="2026-08-02T00:00:00+00:00", prs=[pr2])
    )
    history = storage.history_for_pr(conn, "owner/repo", 42)
    assert [h["label"] for h in history] == ["ci_failing", "ready"]
    conn.close()


def test_history_for_pr_empty_when_never_synced(tmp_path):
    conn = storage.connect(str(tmp_path / "db.sqlite"))
    assert storage.history_for_pr(conn, "owner/repo", 42) == []
    conn.close()


def test_connect_creates_parent_directory(tmp_path):
    db_path = tmp_path / "nested" / "dir" / "db.sqlite"
    conn = storage.connect(str(db_path))
    storage.save_snapshot(conn, make_report())
    assert db_path.exists()
    conn.close()

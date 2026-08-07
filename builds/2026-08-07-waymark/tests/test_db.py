"""Tests for the SQLite storage layer."""

from __future__ import annotations

from pathlib import Path

from src import db as db_module


def _record(commit_hash: str, **overrides) -> dict:
    base = {
        "commit_hash": commit_hash,
        "author": "Test User",
        "committed_at": "2026-01-01T00:00:00+00:00",
        "subject": "feat: add thing",
        "body": "",
        "files_changed": 1,
        "insertions": 5,
        "deletions": 1,
        "decision_score": 6,
        "tags": ["feat"],
        "summary": "Added a thing",
        "ai_summary": None,
    }
    base.update(overrides)
    return base


def test_connect_creates_db_file(db_path: Path):
    conn = db_module.connect(db_path)
    assert db_path.exists()
    conn.close()


def test_insert_and_retrieve_commits(db_conn):
    db_module.insert_commits(db_conn, "repo-a", [_record("hash1")])
    all_rows = db_module.all_commits(db_conn)
    assert len(all_rows) == 1
    assert all_rows[0]["commit_hash"] == "hash1"


def test_incremental_indexing_skips_known_hashes(db_conn):
    db_module.insert_commits(db_conn, "repo-a", [_record("hash1"), _record("hash2")])
    known = db_module.known_commit_hashes(db_conn, "repo-a")
    assert known == {"hash1", "hash2"}

    inserted = db_module.insert_commits(db_conn, "repo-a", [_record("hash1")])
    assert inserted == 1  # attempted insert count; duplicate silently ignored by INSERT OR IGNORE
    all_rows = db_module.all_commits(db_conn)
    assert len(all_rows) == 2


def test_multi_repo_isolation(db_conn):
    db_module.insert_commits(db_conn, "repo-a", [_record("shared-hash")])
    db_module.insert_commits(db_conn, "repo-b", [_record("shared-hash")])
    known_a = db_module.known_commit_hashes(db_conn, "repo-a")
    known_b = db_module.known_commit_hashes(db_conn, "repo-b")
    assert known_a == {"shared-hash"}
    assert known_b == {"shared-hash"}
    assert len(db_module.all_commits(db_conn)) == 2


def test_upsert_repo_and_list_repos(db_conn):
    db_module.upsert_repo(db_conn, "repo-a", "/tmp/repo-a", "2026-01-01T00:00:00+00:00")
    db_module.insert_commits(db_conn, "repo-a", [_record("hash1", decision_score=8)])
    repos = db_module.list_repos(db_conn)
    assert len(repos) == 1
    assert repos[0]["label"] == "repo-a"
    assert repos[0]["commit_count"] == 1
    assert repos[0]["decision_count"] == 1


def test_search_filters_by_min_score(db_conn):
    db_module.insert_commits(
        db_conn, "repo-a", [_record("low", decision_score=1), _record("high", decision_score=9)]
    )
    results = db_module.search_commits(db_conn, min_score=5)
    hashes = {r["commit_hash"] for r in results}
    assert hashes == {"high"}


def test_search_filters_by_repo_label(db_conn):
    db_module.insert_commits(db_conn, "repo-a", [_record("a1")])
    db_module.insert_commits(db_conn, "repo-b", [_record("b1")])
    results = db_module.search_commits(db_conn, repo_label="repo-a")
    assert {r["commit_hash"] for r in results} == {"a1"}


def test_search_filters_by_tag(db_conn):
    db_module.insert_commits(db_conn, "repo-a", [_record("a1", tags=["feat"]), _record("a2", tags=["fix"])])
    results = db_module.search_commits(db_conn, tag="fix")
    assert {r["commit_hash"] for r in results} == {"a2"}


def test_search_filters_by_query_text(db_conn):
    db_module.insert_commits(
        db_conn,
        "repo-a",
        [_record("a1", summary="Switched to plugin renderer"), _record("a2", summary="Bumped dependency")],
    )
    results = db_module.search_commits(db_conn, query="plugin")
    assert {r["commit_hash"] for r in results} == {"a1"}


def test_search_orders_by_score_descending(db_conn):
    db_module.insert_commits(
        db_conn,
        "repo-a",
        [_record("low", decision_score=2), _record("high", decision_score=9), _record("mid", decision_score=5)],
    )
    results = db_module.search_commits(db_conn)
    scores = [r["decision_score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_commits_needing_enrichment_excludes_already_enriched(db_conn):
    db_module.insert_commits(
        db_conn,
        "repo-a",
        [
            _record("needs-it", decision_score=8, ai_summary=None),
            _record("already-done", decision_score=8, ai_summary="Already enriched"),
            _record("too-low", decision_score=1, ai_summary=None),
        ],
    )
    candidates = db_module.commits_needing_enrichment(db_conn, repo_label=None, limit=10)
    hashes = {r["commit_hash"] for r in candidates}
    assert hashes == {"needs-it"}


def test_set_ai_summary_updates_row(db_conn):
    db_module.insert_commits(db_conn, "repo-a", [_record("hash1")])
    db_module.set_ai_summary(db_conn, "repo-a", "hash1", "A refined summary")
    row = db_module.all_commits(db_conn)[0]
    assert row["ai_summary"] == "A refined summary"

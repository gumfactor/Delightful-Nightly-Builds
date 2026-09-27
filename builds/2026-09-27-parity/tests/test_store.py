import os

import pytest

from matcher import MatchResult
from store import connect, history, latest_run_items, save_run


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "parity_test.db"
    yield str(path)


def sample_results():
    return [
        MatchResult(
            "matched_ok",
            teamwork_item={"title": "Match me", "url": "https://tw/1"},
            coda_item={"title": "Match me", "url": "https://coda/1"},
            similarity=1.0,
        ),
        MatchResult(
            "status_conflict",
            teamwork_item={"title": "Conflict task", "url": "https://tw/2"},
            coda_item={"title": "Conflict task", "url": "https://coda/2"},
            similarity=1.0,
            detail="done in Teamwork, still open in Coda",
        ),
        MatchResult("teamwork_only", teamwork_item={"title": "Lone TW", "url": "https://tw/3"}),
        MatchResult("coda_only", coda_item={"title": "Lone Coda", "url": "https://coda/3"}),
    ]


def test_fresh_database_initializes_schema(db_path):
    assert not os.path.exists(db_path)
    conn = connect(db_path)
    # No error means the schema was created; confirm the tables exist.
    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert {"sync_runs", "sync_items"} <= tables
    conn.close()


def test_save_run_and_round_trip_counts(db_path):
    conn = connect(db_path)
    run_id = save_run(conn, sample_results())
    runs = history(conn)
    conn.close()

    assert len(runs) == 1
    run = runs[0]
    assert run.id == run_id
    assert run.matched_ok == 1
    assert run.status_conflict == 1
    assert run.teamwork_only == 1
    assert run.coda_only == 1
    assert run.gap_size == 3  # status_conflict(1) + teamwork_only(1) + coda_only(1)


def test_history_returns_runs_oldest_first(db_path):
    conn = connect(db_path)
    save_run(conn, sample_results())
    save_run(conn, sample_results()[:2])
    runs = history(conn)
    conn.close()

    assert len(runs) == 2
    assert runs[0].id < runs[1].id


def test_latest_run_items_returns_none_when_no_runs(db_path):
    conn = connect(db_path)
    latest, items = latest_run_items(conn)
    conn.close()
    assert latest is None
    assert items == []


def test_latest_run_items_returns_full_item_detail(db_path):
    conn = connect(db_path)
    save_run(conn, sample_results())
    latest, items = latest_run_items(conn)
    conn.close()

    assert latest is not None
    assert len(items) == 4
    conflict_item = next(i for i in items if i["bucket"] == "status_conflict")
    assert conflict_item["detail"] == "done in Teamwork, still open in Coda"
    assert conflict_item["teamwork_title"] == "Conflict task"
    assert conflict_item["coda_title"] == "Conflict task"

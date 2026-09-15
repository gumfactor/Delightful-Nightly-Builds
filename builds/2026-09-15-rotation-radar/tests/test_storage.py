import pytest

from src.analytics import SectorPoint, SectorResult
from src import storage


def _result(ticker, ratio, momentum, quadrant):
    point = SectorPoint(date="2026-01-01", rs_ratio=ratio, rs_momentum=momentum, quadrant=quadrant)
    return SectorResult(ticker=ticker, tail=[point], latest=point, previous=None)


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    connection = storage.connect(db_path)
    yield connection
    connection.close()


def test_connect_creates_schema(conn):
    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert {"runs", "snapshots"} <= tables


def test_save_run_persists_snapshot(conn):
    snapshots = {"A": _result("A", 101.0, 99.0, "Weakening")}
    run_id = storage.save_run(conn, "2026-01-01 00:00:00 UTC", snapshots)
    rows = conn.execute("SELECT ticker, rs_ratio, rs_momentum, quadrant FROM snapshots WHERE run_id = ?", (run_id,)).fetchall()
    assert rows == [("A", 101.0, 99.0, "Weakening")]


def test_get_previous_run_snapshot_empty_when_no_history(conn):
    assert storage.get_previous_run_snapshot(conn) == {}


def test_get_previous_run_snapshot_returns_most_recent(conn):
    storage.save_run(conn, "run1", {"A": _result("A", 101.0, 99.0, "Weakening")})
    storage.save_run(conn, "run2", {"A": _result("A", 102.0, 101.0, "Leading")})
    previous = storage.get_previous_run_snapshot(conn)
    assert previous == {"A": "Leading"}


def test_get_previous_run_snapshot_before_specific_run(conn):
    run1 = storage.save_run(conn, "run1", {"A": _result("A", 101.0, 99.0, "Weakening")})
    run2 = storage.save_run(conn, "run2", {"A": _result("A", 102.0, 101.0, "Leading")})
    previous = storage.get_previous_run_snapshot(conn, before_run_id=run2)
    assert previous == {"A": "Weakening"}
    assert storage.get_previous_run_snapshot(conn, before_run_id=run1) == {}


def test_compute_transitions_first_run_reports_no_previous():
    current = {"A": _result("A", 101.0, 99.0, "Weakening")}
    transitions = storage.compute_transitions({}, current)
    assert transitions[0].previous_quadrant is None
    assert transitions[0].changed is False


def test_compute_transitions_detects_change():
    previous = {"A": "Lagging"}
    current = {"A": _result("A", 101.0, 101.0, "Leading")}
    transitions = storage.compute_transitions(previous, current)
    assert transitions[0].changed is True
    assert transitions[0].previous_quadrant == "Lagging"
    assert transitions[0].current_quadrant == "Leading"


def test_compute_transitions_no_change_when_quadrant_same():
    previous = {"A": "Leading"}
    current = {"A": _result("A", 101.0, 101.0, "Leading")}
    transitions = storage.compute_transitions(previous, current)
    assert transitions[0].changed is False


def test_get_history_orders_oldest_first(conn):
    storage.save_run(conn, "run1", {"A": _result("A", 100.0, 100.0, "Leading")})
    storage.save_run(conn, "run2", {"A": _result("A", 102.0, 101.0, "Leading")})
    history = storage.get_history(conn, "A")
    assert [row[0] for row in history] == ["run1", "run2"]
    assert history[0][1] == 100.0
    assert history[1][1] == 102.0

"""Tests for src/storage.py — SQLite snapshot persistence with same-day upsert."""

import sqlite3

import pytest

from src import storage


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    storage.init_db(connection)
    yield connection
    connection.close()


def sample_snapshot(net_liq=10000.0, symbol="AAPL"):
    return {
        "account_id": "U123",
        "net_liquidation": net_liq,
        "total_cash": 5000.0,
        "gross_position_value": 5000.0,
        "unrealized_pnl": 200.0,
        "realized_pnl": 50.0,
        "buying_power": 20000.0,
        "positions": [
            {
                "symbol": symbol,
                "sec_type": "STK",
                "currency": "USD",
                "exchange": "NASDAQ",
                "quantity": 10.0,
                "avg_cost": 150.0,
                "market_price": 200.0,
                "market_value": 2000.0,
                "unrealized_pnl": 500.0,
            }
        ],
    }


def test_init_db_creates_both_tables(conn):
    tables = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"snapshots", "positions"} <= tables


def test_sync_snapshot_inserts_new_day(conn):
    storage.sync_snapshot(conn, sample_snapshot(), snapshot_date="2026-08-20")
    rows = conn.execute("SELECT * FROM snapshots").fetchall()
    assert len(rows) == 1
    assert rows[0]["snapshot_date"] == "2026-08-20"


def test_sync_snapshot_same_day_updates_in_place_not_duplicate(conn):
    storage.sync_snapshot(conn, sample_snapshot(net_liq=10000.0), snapshot_date="2026-08-20")
    storage.sync_snapshot(conn, sample_snapshot(net_liq=10500.0), snapshot_date="2026-08-20")

    rows = conn.execute("SELECT * FROM snapshots").fetchall()
    assert len(rows) == 1
    assert rows[0]["net_liquidation"] == 10500.0


def test_sync_snapshot_same_day_replaces_positions_not_appends(conn):
    storage.sync_snapshot(conn, sample_snapshot(symbol="AAPL"), snapshot_date="2026-08-20")
    storage.sync_snapshot(conn, sample_snapshot(symbol="MSFT"), snapshot_date="2026-08-20")

    positions = conn.execute("SELECT symbol FROM positions").fetchall()
    assert [p["symbol"] for p in positions] == ["MSFT"]


def test_sync_snapshot_different_days_accumulate(conn):
    storage.sync_snapshot(conn, sample_snapshot(), snapshot_date="2026-08-19")
    storage.sync_snapshot(conn, sample_snapshot(), snapshot_date="2026-08-20")

    rows = conn.execute("SELECT snapshot_date FROM snapshots ORDER BY snapshot_date").fetchall()
    assert [r["snapshot_date"] for r in rows] == ["2026-08-19", "2026-08-20"]


def test_get_latest_snapshot_returns_most_recent_day(conn):
    storage.sync_snapshot(conn, sample_snapshot(net_liq=1.0), snapshot_date="2026-08-19")
    storage.sync_snapshot(conn, sample_snapshot(net_liq=2.0), snapshot_date="2026-08-20")

    latest = storage.get_latest_snapshot(conn)
    assert latest["snapshot_date"] == "2026-08-20"
    assert latest["net_liquidation"] == 2.0
    assert len(latest["positions"]) == 1


def test_get_latest_snapshot_on_empty_db_returns_none(conn):
    assert storage.get_latest_snapshot(conn) is None


def test_get_history_respects_days_limit(conn):
    for i, day in enumerate(["2026-08-17", "2026-08-18", "2026-08-19", "2026-08-20"]):
        storage.sync_snapshot(conn, sample_snapshot(net_liq=float(i)), snapshot_date=day)

    history = storage.get_history(conn, days=2)
    assert [h["snapshot_date"] for h in history] == ["2026-08-19", "2026-08-20"]


def test_get_history_on_empty_db_returns_empty_list(conn):
    assert storage.get_history(conn) == []


def test_get_all_snapshots_with_positions_attaches_positions(conn):
    storage.sync_snapshot(conn, sample_snapshot(), snapshot_date="2026-08-20")
    result = storage.get_all_snapshots_with_positions(conn)
    assert len(result) == 1
    assert result[0]["positions"][0]["symbol"] == "AAPL"

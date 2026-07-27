import pytest
from storage import SiliconWatchDB


def make_row(ticker="NVDA", snapshot_date="2026-07-27", market_cap=1000.0, pe=40.0):
    return {
        "ticker": ticker,
        "name": "NVIDIA Corporation",
        "subsector": "GPU / AI Accelerators",
        "snapshot_date": snapshot_date,
        "price": 120.0,
        "market_cap": market_cap,
        "pe_trailing": pe,
        "pe_forward": 35.0,
        "peg_ratio": 1.5,
        "profit_margin": 0.5,
        "revenue_growth": 0.4,
        "target_mean_price": 140.0,
        "week52_low": 80.0,
        "week52_high": 150.0,
        "fetched_at": "2026-07-27T08:00:00Z",
    }


@pytest.fixture
def db(tmp_path):
    database = SiliconWatchDB(str(tmp_path / "test.db"))
    yield database
    database.close()


def test_schema_created_on_init(db):
    cursor = db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row["name"] for row in cursor.fetchall()}
    assert {"snapshots", "price_history"}.issubset(tables)


def test_upsert_snapshot_inserts_new_row(db):
    db.upsert_snapshot(make_row())
    rows = db.get_snapshot_history("NVDA")
    assert len(rows) == 1
    assert rows[0]["market_cap"] == 1000.0


def test_upsert_snapshot_same_day_updates_not_duplicates(db):
    db.upsert_snapshot(make_row(market_cap=1000.0))
    db.upsert_snapshot(make_row(market_cap=1200.0))
    rows = db.get_snapshot_history("NVDA")
    assert len(rows) == 1
    assert rows[0]["market_cap"] == 1200.0


def test_upsert_snapshot_different_day_creates_new_row(db):
    db.upsert_snapshot(make_row(snapshot_date="2026-07-26"))
    db.upsert_snapshot(make_row(snapshot_date="2026-07-27"))
    rows = db.get_snapshot_history("NVDA")
    assert len(rows) == 2


def test_insert_price_history_dedupes_by_date(db):
    db.insert_price_history("NVDA", [("2026-07-25", 100.0), ("2026-07-26", 101.0)])
    db.insert_price_history("NVDA", [("2026-07-26", 102.0), ("2026-07-27", 103.0)])
    history = db.get_price_history("NVDA")
    assert history == [("2026-07-25", 100.0), ("2026-07-26", 102.0), ("2026-07-27", 103.0)]


def test_get_latest_snapshots_returns_most_recent_per_ticker(db):
    db.upsert_snapshot(make_row(ticker="NVDA", snapshot_date="2026-07-25", market_cap=900.0))
    db.upsert_snapshot(make_row(ticker="NVDA", snapshot_date="2026-07-27", market_cap=1100.0))
    db.upsert_snapshot(make_row(ticker="AMD", snapshot_date="2026-07-27", market_cap=200.0))
    latest = db.get_latest_snapshots()
    nvda_rows = [r for r in latest if r["ticker"] == "NVDA"]
    assert len(nvda_rows) == 1
    assert nvda_rows[0]["market_cap"] == 1100.0
    assert len(latest) == 2


def test_list_snapshot_dates_returns_sorted_distinct_dates(db):
    db.upsert_snapshot(make_row(ticker="NVDA", snapshot_date="2026-07-25"))
    db.upsert_snapshot(make_row(ticker="AMD", snapshot_date="2026-07-25"))
    db.upsert_snapshot(make_row(ticker="NVDA", snapshot_date="2026-07-27"))
    assert db.list_snapshot_dates() == ["2026-07-25", "2026-07-27"]


def test_sector_pe_by_date_averages_and_ignores_none(db):
    db.upsert_snapshot(make_row(ticker="NVDA", snapshot_date="2026-07-27", pe=40.0))
    db.upsert_snapshot(make_row(ticker="AMD", snapshot_date="2026-07-27", pe=60.0))
    row = make_row(ticker="MU", snapshot_date="2026-07-27")
    row["pe_trailing"] = None
    db.upsert_snapshot(row)
    trend = db.sector_pe_by_date()
    assert trend == [("2026-07-27", 50.0)]


def test_get_price_history_empty_for_unknown_ticker(db):
    assert db.get_price_history("UNKNOWN") == []

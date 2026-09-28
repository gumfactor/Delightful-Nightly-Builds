import sqlite3

import pytest

from src.storage import Storage


def make_row(forecast_date, sync_day, fetched_at, running_score=70.0, golf_score=60.0):
    return dict(
        location_name="Toronto, ON", lat=43.65, lon=-79.38,
        forecast_date=forecast_date, sync_day=sync_day, fetched_at=fetched_at,
        temp_max=15.0, temp_min=8.0, precip_prob_max=10.0, precip_sum=0.0,
        wind_max=10.0, windgust_max=18.0, uv_index_max=3.0, weathercode=1,
        aqi_max=40.0, aqi_mean=30.0, pm25_mean=8.0,
        running_score=running_score, golf_score=golf_score,
    )


@pytest.fixture
def storage(tmp_path):
    db_path = tmp_path / "test.db"
    with Storage(db_path) as s:
        yield s


def test_schema_created_on_init(storage):
    tables = storage._conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='forecast_snapshots';"
    ).fetchall()
    assert len(tables) == 1


def test_upsert_inserts_new_row(storage):
    storage.upsert_snapshots([make_row("2026-09-28", "2026-09-28", "2026-09-28T08:00:00")])
    rows = storage.latest_snapshots("Toronto, ON")
    assert len(rows) == 1
    assert rows[0]["forecast_date"] == "2026-09-28"


def test_upsert_same_sync_day_updates_in_place_no_duplicate(storage):
    storage.upsert_snapshots([make_row("2026-09-28", "2026-09-28", "2026-09-28T08:00:00", running_score=50.0)])
    storage.upsert_snapshots([make_row("2026-09-28", "2026-09-28", "2026-09-28T14:00:00", running_score=90.0)])
    rows = storage.latest_snapshots("Toronto, ON")
    assert len(rows) == 1
    assert rows[0]["running_score"] == 90.0


def test_upsert_new_sync_day_adds_row_preserves_old_snapshot(storage):
    storage.upsert_snapshots([make_row("2026-09-29", "2026-09-28", "2026-09-28T08:00:00", running_score=50.0)])
    storage.upsert_snapshots([make_row("2026-09-29", "2026-09-29", "2026-09-29T08:00:00", running_score=95.0)])
    raw_count = storage._conn.execute(
        "SELECT COUNT(*) AS n FROM forecast_snapshots WHERE forecast_date='2026-09-29';"
    ).fetchone()["n"]
    assert raw_count == 2
    latest = storage.latest_snapshots("Toronto, ON")
    assert len(latest) == 1
    assert latest[0]["running_score"] == 95.0


def test_latest_snapshots_returns_most_recent_per_date_sorted(storage):
    storage.upsert_snapshots([
        make_row("2026-09-29", "2026-09-28", "2026-09-28T08:00:00"),
        make_row("2026-09-28", "2026-09-28", "2026-09-28T08:00:00"),
    ])
    rows = storage.latest_snapshots("Toronto, ON")
    assert [r["forecast_date"] for r in rows] == ["2026-09-28", "2026-09-29"]


def test_sync_count_counts_distinct_sync_days(storage):
    storage.upsert_snapshots([make_row("2026-09-28", "2026-09-28", "2026-09-28T08:00:00")])
    storage.upsert_snapshots([make_row("2026-09-28", "2026-09-28", "2026-09-28T14:00:00")])
    storage.upsert_snapshots([make_row("2026-09-28", "2026-09-29", "2026-09-29T08:00:00")])
    assert storage.sync_count("Toronto, ON") == 2


def test_last_sync_time_returns_latest_fetched_at(storage):
    storage.upsert_snapshots([make_row("2026-09-28", "2026-09-28", "2026-09-28T08:00:00")])
    storage.upsert_snapshots([make_row("2026-09-29", "2026-09-29", "2026-09-29T09:30:00")])
    assert storage.last_sync_time("Toronto, ON") == "2026-09-29T09:30:00"


def test_last_sync_time_none_when_no_data(storage):
    assert storage.last_sync_time("Nowhere") is None


def test_latest_snapshots_excludes_dates_that_rolled_out_of_the_current_horizon(storage):
    # Day 1 sync covers Sep 28-Oct 4. Day 2 sync (the forecast window having
    # rolled forward) covers Sep 29-Oct 5, so Sep 28 is no longer synced.
    day1_dates = ["2026-09-28", "2026-09-29", "2026-09-30", "2026-10-01",
                  "2026-10-02", "2026-10-03", "2026-10-04"]
    day2_dates = ["2026-09-29", "2026-09-30", "2026-10-01", "2026-10-02",
                  "2026-10-03", "2026-10-04", "2026-10-05"]
    storage.upsert_snapshots([make_row(d, "2026-09-28", "2026-09-28T08:00:00") for d in day1_dates])
    storage.upsert_snapshots([make_row(d, "2026-09-29", "2026-09-29T08:00:00") for d in day2_dates])

    latest = storage.latest_snapshots("Toronto, ON")
    latest_dates = [r["forecast_date"] for r in latest]

    assert latest_dates == day2_dates
    assert "2026-09-28" not in latest_dates

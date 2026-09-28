"""SQLite persistence for synced forecast snapshots.

One row per (location, forecast_date, sync_day). Re-syncing the same UTC day
updates that day's row in place (upsert); syncing on a later day adds new
rows and preserves earlier snapshots, so a real multi-day forecast history
accumulates with repeated real-world use.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional, TypedDict

SCHEMA = """
CREATE TABLE IF NOT EXISTS forecast_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_name TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    forecast_date TEXT NOT NULL,
    sync_day TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    temp_max REAL,
    temp_min REAL,
    precip_prob_max REAL,
    precip_sum REAL,
    wind_max REAL,
    windgust_max REAL,
    uv_index_max REAL,
    weathercode INTEGER,
    aqi_max REAL,
    aqi_mean REAL,
    pm25_mean REAL,
    running_score REAL NOT NULL,
    golf_score REAL NOT NULL,
    UNIQUE(location_name, forecast_date, sync_day)
);
"""

UPSERT_SQL = """
INSERT INTO forecast_snapshots (
    location_name, lat, lon, forecast_date, sync_day, fetched_at,
    temp_max, temp_min, precip_prob_max, precip_sum, wind_max, windgust_max,
    uv_index_max, weathercode, aqi_max, aqi_mean, pm25_mean, running_score, golf_score
) VALUES (
    :location_name, :lat, :lon, :forecast_date, :sync_day, :fetched_at,
    :temp_max, :temp_min, :precip_prob_max, :precip_sum, :wind_max, :windgust_max,
    :uv_index_max, :weathercode, :aqi_max, :aqi_mean, :pm25_mean, :running_score, :golf_score
)
ON CONFLICT(location_name, forecast_date, sync_day) DO UPDATE SET
    fetched_at=excluded.fetched_at,
    temp_max=excluded.temp_max, temp_min=excluded.temp_min,
    precip_prob_max=excluded.precip_prob_max, precip_sum=excluded.precip_sum,
    wind_max=excluded.wind_max, windgust_max=excluded.windgust_max,
    uv_index_max=excluded.uv_index_max, weathercode=excluded.weathercode,
    aqi_max=excluded.aqi_max, aqi_mean=excluded.aqi_mean, pm25_mean=excluded.pm25_mean,
    running_score=excluded.running_score, golf_score=excluded.golf_score;
"""


class SnapshotRow(TypedDict):
    location_name: str
    lat: float
    lon: float
    forecast_date: str
    sync_day: str
    fetched_at: str
    temp_max: float
    temp_min: float
    precip_prob_max: float
    precip_sum: float
    wind_max: float
    windgust_max: float
    uv_index_max: float
    weathercode: int
    aqi_max: Optional[float]
    aqi_mean: Optional[float]
    pm25_mean: Optional[float]
    running_score: float
    golf_score: float


class Storage:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Storage":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def upsert_snapshots(self, rows: List[SnapshotRow]) -> None:
        self._conn.executemany(UPSERT_SQL, rows)
        self._conn.commit()

    def latest_snapshots(self, location_name: str) -> List[sqlite3.Row]:
        """Return every row from the most recent sync_day only, sorted by date.

        Restricting to a single sync_day (rather than the latest row per
        forecast_date across all history) matters because forecast_date
        values roll forward each day: a date synced once and never synced
        again (because it has since fallen out of the forecast window)
        would otherwise keep showing up forever as a stale "latest" row for
        that date, growing the dashboard's day list without bound and
        potentially mislabeling an expired date as "today".
        """
        query = """
            SELECT s.*
            FROM forecast_snapshots s
            WHERE s.location_name = ?
              AND s.sync_day = (
                  SELECT MAX(sync_day) FROM forecast_snapshots WHERE location_name = ?
              )
            ORDER BY s.forecast_date ASC;
        """
        return list(self._conn.execute(query, (location_name, location_name)).fetchall())

    def sync_count(self, location_name: str) -> int:
        query = "SELECT COUNT(DISTINCT sync_day) AS n FROM forecast_snapshots WHERE location_name = ?;"
        row = self._conn.execute(query, (location_name,)).fetchone()
        return int(row["n"]) if row else 0

    def last_sync_time(self, location_name: str) -> Optional[str]:
        query = "SELECT MAX(fetched_at) AS latest FROM forecast_snapshots WHERE location_name = ?;"
        row = self._conn.execute(query, (location_name,)).fetchone()
        return row["latest"] if row and row["latest"] else None

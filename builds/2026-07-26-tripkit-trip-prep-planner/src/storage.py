"""SQLite persistence for trips and their weather snapshots."""

from __future__ import annotations

import json
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    destination_query TEXT NOT NULL,
    resolved_name TEXT NOT NULL,
    country TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    activity_tags TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weather_snapshots (
    trip_id INTEGER NOT NULL,
    mode TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    daily_json TEXT NOT NULL,
    FOREIGN KEY (trip_id) REFERENCES trips(id)
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def add_trip(
    conn: sqlite3.Connection,
    name: str,
    destination_query: str,
    resolved_name: str,
    country: str,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    activity_tags: list[str],
    created_at: str,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO trips
            (name, destination_query, resolved_name, country, latitude, longitude,
             start_date, end_date, activity_tags, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            destination_query,
            resolved_name,
            country,
            latitude,
            longitude,
            start_date,
            end_date,
            ",".join(activity_tags),
            created_at,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def _row_to_trip(row: sqlite3.Row) -> dict:
    trip = dict(row)
    trip["activity_tags"] = [tag for tag in trip["activity_tags"].split(",") if tag]
    return trip


def get_trip(conn: sqlite3.Connection, trip_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
    return _row_to_trip(row) if row else None


def list_trips(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM trips ORDER BY start_date ASC").fetchall()
    return [_row_to_trip(row) for row in rows]


def delete_trip(conn: sqlite3.Connection, trip_id: int) -> bool:
    conn.execute("DELETE FROM weather_snapshots WHERE trip_id = ?", (trip_id,))
    cursor = conn.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    conn.commit()
    return cursor.rowcount > 0


def save_weather_snapshot(
    conn: sqlite3.Connection, trip_id: int, mode: str, fetched_at: str, daily_readings: list[dict]
) -> None:
    conn.execute("DELETE FROM weather_snapshots WHERE trip_id = ?", (trip_id,))
    conn.execute(
        "INSERT INTO weather_snapshots (trip_id, mode, fetched_at, daily_json) VALUES (?, ?, ?, ?)",
        (trip_id, mode, fetched_at, json.dumps(daily_readings)),
    )
    conn.commit()


def get_latest_weather_snapshot(conn: sqlite3.Connection, trip_id: int) -> dict | None:
    row = conn.execute(
        "SELECT mode, fetched_at, daily_json FROM weather_snapshots WHERE trip_id = ? LIMIT 1",
        (trip_id,),
    ).fetchone()
    if not row:
        return None
    return {
        "mode": row["mode"],
        "fetched_at": row["fetched_at"],
        "daily": json.loads(row["daily_json"]),
    }

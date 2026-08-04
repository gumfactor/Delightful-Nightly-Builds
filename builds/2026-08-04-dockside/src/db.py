"""SQLite persistence for Dockside.

Every table lives in a single .db file the CLI creates in the current
working directory (or wherever --db points) - nothing here ever reads or
writes outside that one file.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    place_name TEXT,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    marine_available INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL REFERENCES sites(id),
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    window_start_month INTEGER NOT NULL,
    window_end_month INTEGER NOT NULL,
    max_wind_kmh REAL,
    min_water_temp_c REAL,
    dry_days_required INTEGER,
    frost_free_required INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL REFERENCES tasks(id),
    season_year INTEGER NOT NULL,
    completed_date TEXT NOT NULL,
    UNIQUE(task_id, season_year)
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL REFERENCES sites(id),
    obs_date TEXT NOT NULL,
    temp_min_c REAL,
    temp_max_c REAL,
    precip_mm REAL,
    wind_speed_max_kmh REAL,
    wave_height_max_m REAL,
    water_temp_c REAL,
    fetched_at TEXT NOT NULL,
    UNIQUE(site_id, obs_date)
);

CREATE TABLE IF NOT EXISTS briefings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER NOT NULL REFERENCES sites(id),
    generated_at TEXT NOT NULL,
    source TEXT NOT NULL,
    text TEXT NOT NULL
);
"""

VALID_CATEGORIES = {"dock", "boat", "water_system", "structure", "other"}


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def add_site(conn, name: str, place_name: Optional[str], latitude: float, longitude: float) -> int:
    cur = conn.execute(
        "INSERT INTO sites (name, place_name, latitude, longitude, marine_available, created_at) "
        "VALUES (?, ?, ?, ?, NULL, ?)",
        (name, place_name, latitude, longitude, datetime.utcnow().isoformat()),
    )
    conn.commit()
    return cur.lastrowid


def get_site_by_name(conn, name: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM sites WHERE name = ?", (name,)).fetchone()


def list_sites(conn) -> list:
    return conn.execute("SELECT * FROM sites ORDER BY name").fetchall()


def set_marine_available(conn, site_id: int, available: bool) -> None:
    conn.execute(
        "UPDATE sites SET marine_available = ? WHERE id = ?",
        (1 if available else 0, site_id),
    )
    conn.commit()


def add_task(conn, site_id: int, name: str, category: str, window_start_month: int,
             window_end_month: int, max_wind_kmh: Optional[float] = None,
             min_water_temp_c: Optional[float] = None, dry_days_required: Optional[int] = None,
             frost_free_required: bool = False) -> int:
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Must be one of {sorted(VALID_CATEGORIES)}")
    if not (1 <= window_start_month <= 12) or not (1 <= window_end_month <= 12):
        raise ValueError("window_start_month and window_end_month must be between 1 and 12")
    cur = conn.execute(
        "INSERT INTO tasks (site_id, name, category, window_start_month, window_end_month, "
        "max_wind_kmh, min_water_temp_c, dry_days_required, frost_free_required, active, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)",
        (site_id, name, category, window_start_month, window_end_month, max_wind_kmh,
         min_water_temp_c, dry_days_required, 1 if frost_free_required else 0,
         datetime.utcnow().isoformat()),
    )
    conn.commit()
    return cur.lastrowid


def list_tasks(conn, site_id: Optional[int] = None, active_only: bool = True) -> list:
    query = "SELECT * FROM tasks WHERE 1=1"
    params: list = []
    if site_id is not None:
        query += " AND site_id = ?"
        params.append(site_id)
    if active_only:
        query += " AND active = 1"
    query += " ORDER BY id"
    return conn.execute(query, params).fetchall()


def get_task(conn, task_id: int) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()


def upsert_observation(conn, site_id: int, obs_date: str, temp_min_c, temp_max_c, precip_mm,
                        wind_speed_max_kmh, wave_height_max_m, water_temp_c) -> None:
    conn.execute(
        """
        INSERT INTO observations
            (site_id, obs_date, temp_min_c, temp_max_c, precip_mm, wind_speed_max_kmh,
             wave_height_max_m, water_temp_c, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(site_id, obs_date) DO UPDATE SET
            temp_min_c = excluded.temp_min_c,
            temp_max_c = excluded.temp_max_c,
            precip_mm = excluded.precip_mm,
            wind_speed_max_kmh = excluded.wind_speed_max_kmh,
            wave_height_max_m = excluded.wave_height_max_m,
            water_temp_c = excluded.water_temp_c,
            fetched_at = excluded.fetched_at
        """,
        (site_id, obs_date, temp_min_c, temp_max_c, precip_mm, wind_speed_max_kmh,
         wave_height_max_m, water_temp_c, datetime.utcnow().isoformat()),
    )
    conn.commit()


def list_observations(conn, site_id: int) -> list:
    return conn.execute(
        "SELECT * FROM observations WHERE site_id = ? ORDER BY obs_date", (site_id,)
    ).fetchall()


def count_observations(conn, site_id: int) -> int:
    row = conn.execute(
        "SELECT COUNT(*) as c FROM observations WHERE site_id = ?", (site_id,)
    ).fetchone()
    return row["c"]


def record_completion(conn, task_id: int, season_year: int, completed_date: str) -> None:
    conn.execute(
        "INSERT INTO completions (task_id, season_year, completed_date) VALUES (?, ?, ?) "
        "ON CONFLICT(task_id, season_year) DO UPDATE SET completed_date = excluded.completed_date",
        (task_id, season_year, completed_date),
    )
    conn.commit()


def get_last_completion_year(conn, task_id: int) -> Optional[int]:
    row = conn.execute(
        "SELECT MAX(season_year) as y FROM completions WHERE task_id = ?", (task_id,)
    ).fetchone()
    return row["y"] if row and row["y"] is not None else None


def save_briefing(conn, site_id: int, source: str, text: str) -> None:
    conn.execute(
        "INSERT INTO briefings (site_id, generated_at, source, text) VALUES (?, ?, ?, ?)",
        (site_id, datetime.utcnow().isoformat(), source, text),
    )
    conn.commit()


def get_latest_briefing(conn, site_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM briefings WHERE site_id = ? ORDER BY generated_at DESC LIMIT 1",
        (site_id,),
    ).fetchone()

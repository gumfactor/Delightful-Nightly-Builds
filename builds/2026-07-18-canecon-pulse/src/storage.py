"""SQLite persistence for CanEcon Pulse observation history."""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Tuple

from src.models import Observation

SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id    TEXT NOT NULL,
    series_label TEXT NOT NULL,
    unit         TEXT NOT NULL,
    source       TEXT NOT NULL,
    obs_date     TEXT NOT NULL,
    value        REAL NOT NULL,
    fetched_at   TEXT NOT NULL,
    UNIQUE(series_id, obs_date)
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    """Open (and create if needed) the SQLite database at db_path."""
    parent = Path(db_path).parent
    if str(parent) not in ("", "."):
        parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def insert_observations(conn: sqlite3.Connection, observations: List[Observation]) -> int:
    """Insert observations, skipping any (series_id, obs_date) already stored.

    Returns the number of genuinely new rows inserted.
    """
    if not observations:
        return 0
    fetched_at = datetime.now(timezone.utc).isoformat()
    rows = [
        (
            obs.series_id,
            obs.series_label,
            obs.unit,
            obs.source,
            obs.obs_date.isoformat(),
            obs.value,
            fetched_at,
        )
        for obs in observations
    ]
    before = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    conn.executemany(
        """
        INSERT OR IGNORE INTO observations
            (series_id, series_label, unit, source, obs_date, value, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    after = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    return after - before


def get_series_ids(conn: sqlite3.Connection) -> List[str]:
    cursor = conn.execute("SELECT DISTINCT series_id FROM observations ORDER BY series_id")
    return [row[0] for row in cursor.fetchall()]


def get_history(conn: sqlite3.Connection, series_id: str) -> List[Tuple[date, float]]:
    """Return (date, value) pairs for a series, ordered oldest to newest."""
    cursor = conn.execute(
        "SELECT obs_date, value FROM observations WHERE series_id = ? ORDER BY obs_date ASC",
        (series_id,),
    )
    return [(_parse_iso_date(row[0]), row[1]) for row in cursor.fetchall()]


def get_latest_fetched_at(conn: sqlite3.Connection, series_id: str) -> str | None:
    cursor = conn.execute(
        "SELECT fetched_at FROM observations WHERE series_id = ? ORDER BY obs_date DESC LIMIT 1",
        (series_id,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def _parse_iso_date(raw: str) -> date:
    return date.fromisoformat(raw)

"""SQLite persistence for dependency-pin snapshots.

One row per (repo, ecosystem, dependency, date). A same-day re-sync
upserts in place; different dates accumulate real history, matching the
snapshot pattern this catalog's other multi-run tools already establish.
"""
from __future__ import annotations

import sqlite3
from typing import Dict, List, Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo TEXT NOT NULL,
    ecosystem TEXT NOT NULL CHECK (ecosystem IN ('python', 'npm')),
    dependency TEXT NOT NULL,
    pinned_version TEXT,
    pin_kind TEXT NOT NULL CHECK (pin_kind IN ('exact', 'range', 'unparseable')),
    latest_version TEXT,
    fetched_at_date TEXT NOT NULL,
    UNIQUE(repo, ecosystem, dependency, fetched_at_date)
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def upsert_snapshot(
    conn: sqlite3.Connection,
    repo: str,
    ecosystem: str,
    dependency: str,
    pinned_version: Optional[str],
    pin_kind: str,
    latest_version: Optional[str],
    fetched_at_date: str,
) -> None:
    conn.execute(
        """
        INSERT INTO snapshots (repo, ecosystem, dependency, pinned_version, pin_kind, latest_version, fetched_at_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(repo, ecosystem, dependency, fetched_at_date)
        DO UPDATE SET pinned_version=excluded.pinned_version,
                      pin_kind=excluded.pin_kind,
                      latest_version=excluded.latest_version
        """,
        (repo, ecosystem, dependency, pinned_version, pin_kind, latest_version, fetched_at_date),
    )


def commit(conn: sqlite3.Connection) -> None:
    conn.commit()


def latest_snapshot_date(conn: sqlite3.Connection) -> Optional[str]:
    row = conn.execute("SELECT MAX(fetched_at_date) AS d FROM snapshots").fetchone()
    return row["d"] if row and row["d"] else None


def snapshots_for_date(conn: sqlite3.Connection, date: str) -> List[Dict]:
    rows = conn.execute(
        "SELECT repo, ecosystem, dependency, pinned_version, pin_kind, latest_version, fetched_at_date "
        "FROM snapshots WHERE fetched_at_date = ? ORDER BY dependency, repo",
        (date,),
    ).fetchall()
    return [dict(row) for row in rows]


def history_for_dependency(conn: sqlite3.Connection, ecosystem: str, dependency: str) -> List[Dict]:
    rows = conn.execute(
        "SELECT repo, ecosystem, dependency, pinned_version, pin_kind, latest_version, fetched_at_date "
        "FROM snapshots WHERE ecosystem = ? AND dependency = ? "
        "ORDER BY fetched_at_date ASC, repo ASC",
        (ecosystem, dependency),
    ).fetchall()
    return [dict(row) for row in rows]

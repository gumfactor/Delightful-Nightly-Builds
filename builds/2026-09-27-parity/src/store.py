"""SQLite persistence for sync runs and their item-level results.

Schema is created on first use so a fresh (nonexistent) database file
just works. One `save_run` call persists a run and all its items in a
single transaction.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from matcher import MatchResult

SCHEMA = """
CREATE TABLE IF NOT EXISTS sync_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TEXT NOT NULL,
    matched_ok INTEGER NOT NULL,
    status_conflict INTEGER NOT NULL,
    teamwork_only INTEGER NOT NULL,
    coda_only INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES sync_runs(id),
    bucket TEXT NOT NULL,
    teamwork_title TEXT,
    teamwork_url TEXT,
    coda_title TEXT,
    coda_url TEXT,
    detail TEXT
);
"""


@dataclass
class SyncRun:
    id: int
    run_at: str
    matched_ok: int
    status_conflict: int
    teamwork_only: int
    coda_only: int

    @property
    def gap_size(self) -> int:
        return self.status_conflict + self.teamwork_only + self.coda_only


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def save_run(conn: sqlite3.Connection, results: list[MatchResult]) -> int:
    """Persist one sync run and all its item results. Returns the new run id."""
    counts = {"matched_ok": 0, "status_conflict": 0, "teamwork_only": 0, "coda_only": 0}
    for r in results:
        counts[r.bucket] += 1

    run_at = datetime.now(timezone.utc).isoformat()
    with conn:
        cursor = conn.execute(
            "INSERT INTO sync_runs (run_at, matched_ok, status_conflict, teamwork_only, coda_only) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                run_at,
                counts["matched_ok"],
                counts["status_conflict"],
                counts["teamwork_only"],
                counts["coda_only"],
            ),
        )
        run_id = cursor.lastrowid
        for r in results:
            conn.execute(
                "INSERT INTO sync_items (run_id, bucket, teamwork_title, teamwork_url, "
                "coda_title, coda_url, detail) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    r.bucket,
                    r.teamwork_item["title"] if r.teamwork_item else None,
                    r.teamwork_item["url"] if r.teamwork_item else None,
                    r.coda_item["title"] if r.coda_item else None,
                    r.coda_item["url"] if r.coda_item else None,
                    r.detail or None,
                ),
            )
    return run_id


def history(conn: sqlite3.Connection) -> list[SyncRun]:
    """All sync runs, oldest first."""
    rows = conn.execute(
        "SELECT id, run_at, matched_ok, status_conflict, teamwork_only, coda_only "
        "FROM sync_runs ORDER BY id ASC"
    ).fetchall()
    return [SyncRun(*row) for row in rows]


def latest_run_items(conn: sqlite3.Connection) -> tuple[SyncRun | None, list[dict]]:
    """The most recent run and its full item list, or (None, []) if no runs exist."""
    runs = history(conn)
    if not runs:
        return None, []
    latest = runs[-1]
    rows = conn.execute(
        "SELECT bucket, teamwork_title, teamwork_url, coda_title, coda_url, detail "
        "FROM sync_items WHERE run_id = ? ORDER BY id ASC",
        (latest.id,),
    ).fetchall()
    items = [
        {
            "bucket": row[0],
            "teamwork_title": row[1],
            "teamwork_url": row[2],
            "coda_title": row[3],
            "coda_url": row[4],
            "detail": row[5],
        }
        for row in rows
    ]
    return latest, items

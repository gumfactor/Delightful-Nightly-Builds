"""SQLite persistence for Landing Pattern sync snapshots."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS syncs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo TEXT NOT NULL,
    synced_at TEXT NOT NULL,
    report_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_syncs_repo_time ON syncs(repo, synced_at);
"""


def connect(db_path: str) -> sqlite3.Connection:
    """Open (creating if needed) the snapshot database at `db_path`."""
    parent = Path(db_path).parent
    parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def save_snapshot(conn: sqlite3.Connection, report: dict[str, Any]) -> int:
    """Persist a computed report as a new snapshot row. Returns the new row id."""
    cursor = conn.execute(
        "INSERT INTO syncs (repo, synced_at, report_json) VALUES (?, ?, ?)",
        (report["repo"], report["synced_at"], json.dumps(report)),
    )
    conn.commit()
    return cursor.lastrowid  # type: ignore[return-value]


def latest_snapshot(conn: sqlite3.Connection, repo: str) -> dict[str, Any] | None:
    """Most recent stored report for `repo`, or None if never synced."""
    row = conn.execute(
        "SELECT report_json FROM syncs WHERE repo = ? ORDER BY synced_at DESC, id DESC LIMIT 1",
        (repo,),
    ).fetchone()
    if row is None:
        return None
    return json.loads(row[0])


def snapshot_by_id(conn: sqlite3.Connection, run_id: int) -> dict[str, Any] | None:
    """A specific stored snapshot by its row id, or None if it doesn't exist."""
    row = conn.execute("SELECT report_json FROM syncs WHERE id = ?", (run_id,)).fetchone()
    if row is None:
        return None
    return json.loads(row[0])


def history_for_pr(conn: sqlite3.Connection, repo: str, pr_number: int) -> list[dict[str, Any]]:
    """Every snapshot's view of one PR, oldest first: [{synced_at, label, age_days}, ...]."""
    rows = conn.execute(
        "SELECT synced_at, report_json FROM syncs WHERE repo = ? ORDER BY synced_at ASC, id ASC",
        (repo,),
    ).fetchall()
    history: list[dict[str, Any]] = []
    for synced_at, report_json in rows:
        report = json.loads(report_json)
        match = next((pr for pr in report["prs"] if pr["number"] == pr_number), None)
        if match is not None:
            history.append(
                {"synced_at": synced_at, "label": match["label"], "age_days": match["age_days"]}
            )
    return history

"""SQLite persistence for the Manuscript Pipeline tracker."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import Any

VALID_STATUSES = (
    "submitted",
    "under_review",
    "revise_resubmit",
    "accepted",
    "rejected",
    "published",
    "withdrawn",
)

TERMINAL_STATUSES = ("published", "rejected", "withdrawn")

VALID_TYPES = ("original-research", "review", "commentary", "other")

SCHEMA = """
CREATE TABLE IF NOT EXISTS manuscripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    authors TEXT NOT NULL,
    journal TEXT NOT NULL,
    manuscript_type TEXT NOT NULL,
    submitted_date TEXT NOT NULL,
    expected_review_days INTEGER NOT NULL DEFAULT 90,
    status TEXT NOT NULL,
    revision_deadline TEXT,
    doi TEXT,
    published_date TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS status_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manuscript_id INTEGER NOT NULL REFERENCES manuscripts(id),
    status TEXT NOT NULL,
    note TEXT,
    source TEXT NOT NULL,
    logged_at TEXT NOT NULL
);
"""


class ManuscriptNotFoundError(Exception):
    pass


class InvalidStatusError(Exception):
    pass


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def add_manuscript(
    conn: sqlite3.Connection,
    title: str,
    authors: str,
    journal: str,
    manuscript_type: str,
    submitted_date: str,
    expected_review_days: int = 90,
) -> int:
    if manuscript_type not in VALID_TYPES:
        raise InvalidStatusError(f"Invalid manuscript_type: {manuscript_type!r}")
    now = datetime.utcnow().isoformat()
    cur = conn.execute(
        """INSERT INTO manuscripts
           (title, authors, journal, manuscript_type, submitted_date,
            expected_review_days, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, 'submitted', ?)""",
        (title, authors, journal, manuscript_type, submitted_date, expected_review_days, now),
    )
    conn.commit()
    manuscript_id = cur.lastrowid
    _append_log(conn, manuscript_id, "submitted", "Manuscript registered.", "manual")
    return manuscript_id


def get_manuscript(conn: sqlite3.Connection, manuscript_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM manuscripts WHERE id = ?", (manuscript_id,)).fetchone()
    if row is None:
        raise ManuscriptNotFoundError(f"No manuscript with id {manuscript_id}")
    return row


def list_manuscripts(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM manuscripts ORDER BY submitted_date ASC").fetchall()


def update_status(
    conn: sqlite3.Connection,
    manuscript_id: int,
    status: str,
    note: str | None = None,
    source: str = "manual",
    revision_deadline: str | None = None,
    doi: str | None = None,
    published_date: str | None = None,
) -> None:
    if status not in VALID_STATUSES:
        raise InvalidStatusError(f"Invalid status: {status!r}. Must be one of {VALID_STATUSES}")
    get_manuscript(conn, manuscript_id)  # raises ManuscriptNotFoundError if missing

    conn.execute(
        """UPDATE manuscripts
           SET status = ?, revision_deadline = ?, doi = COALESCE(?, doi),
               published_date = COALESCE(?, published_date)
           WHERE id = ?""",
        (status, revision_deadline, doi, published_date, manuscript_id),
    )
    conn.commit()
    _append_log(conn, manuscript_id, status, note, source)


def get_status_log(conn: sqlite3.Connection, manuscript_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM status_log WHERE manuscript_id = ? ORDER BY logged_at ASC",
        (manuscript_id,),
    ).fetchall()


def _append_log(conn: sqlite3.Connection, manuscript_id: int, status: str, note: str | None, source: str) -> None:
    conn.execute(
        """INSERT INTO status_log (manuscript_id, status, note, source, logged_at)
           VALUES (?, ?, ?, ?, ?)""",
        (manuscript_id, status, note, source, datetime.utcnow().isoformat()),
    )
    conn.commit()


def days_in_stage(manuscript: sqlite3.Row, today: date | None = None) -> int:
    """Days since the manuscript's submission date (proxy for time in the current
    pipeline stage, since our status log timestamps the *event*, not a stage entry
    date distinct from submission for the initial submitted/under_review stages)."""
    today = today or date.today()
    submitted = date.fromisoformat(manuscript["submitted_date"])
    return (today - submitted).days


def is_at_risk(manuscript: sqlite3.Row, today: date | None = None) -> bool:
    today = today or date.today()
    status = manuscript["status"]
    if status in ("submitted", "under_review"):
        return days_in_stage(manuscript, today) > manuscript["expected_review_days"]
    if status == "revise_resubmit" and manuscript["revision_deadline"]:
        deadline = date.fromisoformat(manuscript["revision_deadline"])
        return today > deadline
    return False


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}

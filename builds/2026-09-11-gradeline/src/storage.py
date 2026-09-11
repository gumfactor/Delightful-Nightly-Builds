"""Local SQLite persistence for graded batches.

Every `grade` run creates one new batch row — batches are never overwritten,
so `compare` can look at two real runs' class-level statistics over time.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rubric_name TEXT NOT NULL,
    rubric_json TEXT NOT NULL,
    source_path TEXT NOT NULL,
    graded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL REFERENCES batches(id),
    identifier TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    citation_count INTEGER NOT NULL,
    flesch_score REAL,
    compliance_json TEXT NOT NULL,
    criteria_json TEXT NOT NULL,
    ai_feedback_json TEXT
);

CREATE TABLE IF NOT EXISTS similarity_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER NOT NULL REFERENCES batches(id),
    submission_a_id INTEGER NOT NULL REFERENCES submissions(id),
    submission_b_id INTEGER NOT NULL REFERENCES submissions(id),
    score REAL NOT NULL
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_batch(conn: sqlite3.Connection, rubric_name: str, rubric_json: str, source_path: str) -> int:
    cursor = conn.execute(
        "INSERT INTO batches (rubric_name, rubric_json, source_path, graded_at) VALUES (?, ?, ?, ?)",
        (rubric_name, rubric_json, source_path, _now()),
    )
    conn.commit()
    return cursor.lastrowid


def add_submission(
    conn: sqlite3.Connection,
    batch_id: int,
    identifier: str,
    word_count: int,
    citation_count: int,
    flesch_score: float | None,
    compliance: dict,
    criteria: list[dict],
    ai_feedback: dict | None,
) -> int:
    cursor = conn.execute(
        """INSERT INTO submissions
           (batch_id, identifier, word_count, citation_count, flesch_score,
            compliance_json, criteria_json, ai_feedback_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            batch_id,
            identifier,
            word_count,
            citation_count,
            flesch_score,
            json.dumps(compliance),
            json.dumps(criteria),
            json.dumps(ai_feedback) if ai_feedback is not None else None,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def add_similarity_pair(
    conn: sqlite3.Connection, batch_id: int, sub_a_id: int, sub_b_id: int, score: float
) -> None:
    conn.execute(
        "INSERT INTO similarity_pairs (batch_id, submission_a_id, submission_b_id, score) "
        "VALUES (?, ?, ?, ?)",
        (batch_id, sub_a_id, sub_b_id, score),
    )
    conn.commit()


def list_batches(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM batches ORDER BY id DESC").fetchall()


def get_batch(conn: sqlite3.Connection, batch_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM batches WHERE id = ?", (batch_id,)).fetchone()


def get_submissions(conn: sqlite3.Connection, batch_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM submissions WHERE batch_id = ? ORDER BY id ASC", (batch_id,)
    ).fetchall()


def get_similarity_pairs(conn: sqlite3.Connection, batch_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM similarity_pairs WHERE batch_id = ? ORDER BY score DESC", (batch_id,)
    ).fetchall()

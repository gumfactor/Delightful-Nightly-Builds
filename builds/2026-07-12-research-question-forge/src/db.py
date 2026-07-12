"""SQLite persistence layer for the Research Question Forge library."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    population TEXT NOT NULL,
    construct TEXT NOT NULL,
    outcome TEXT NOT NULL,
    method TEXT NOT NULL,
    frame TEXT NOT NULL,
    skeleton TEXT NOT NULL,
    rationale TEXT NOT NULL,
    testability TEXT NOT NULL,
    novelty_score REAL NOT NULL,
    ai_polish TEXT,
    ai_source TEXT NOT NULL DEFAULT 'template',
    starred INTEGER NOT NULL DEFAULT 0,
    used INTEGER NOT NULL DEFAULT 0,
    tag TEXT
);
"""


def connect(db_path: Path | str) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create the schema if it does not already exist. Safe to call repeatedly."""
    conn.execute(SCHEMA)
    conn.commit()


def insert_question(conn: sqlite3.Connection, created_at: str, question: dict[str, Any]) -> int:
    cur = conn.execute(
        """
        INSERT INTO questions
            (created_at, population, construct, outcome, method, frame,
             skeleton, rationale, testability, novelty_score, ai_polish, ai_source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            created_at,
            question["population"],
            question["construct"],
            question["outcome"],
            question["method"],
            question["frame"],
            question["skeleton"],
            question["rationale"],
            question["testability"],
            question["novelty_score"],
            question.get("ai_polish"),
            question.get("ai_source", "template"),
        ),
    )
    conn.commit()
    return cur.lastrowid


def all_skeletons(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT skeleton FROM questions").fetchall()
    return [row["skeleton"] for row in rows]


def list_questions(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM questions ORDER BY created_at DESC, id DESC").fetchall()


def get_question(conn: sqlite3.Connection, question_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()


def set_starred(conn: sqlite3.Connection, question_id: int, starred: bool) -> bool:
    cur = conn.execute("UPDATE questions SET starred = ? WHERE id = ?", (int(starred), question_id))
    conn.commit()
    return cur.rowcount > 0


def set_used(conn: sqlite3.Connection, question_id: int, used: bool) -> bool:
    cur = conn.execute("UPDATE questions SET used = ? WHERE id = ?", (int(used), question_id))
    conn.commit()
    return cur.rowcount > 0


def set_tag(conn: sqlite3.Connection, question_id: int, tag: str) -> bool:
    cur = conn.execute("UPDATE questions SET tag = ? WHERE id = ?", (tag, question_id))
    conn.commit()
    return cur.rowcount > 0


def search_questions(conn: sqlite3.Connection, query: str) -> list[sqlite3.Row]:
    like = f"%{query}%"
    return conn.execute(
        """
        SELECT * FROM questions
        WHERE skeleton LIKE ? OR rationale LIKE ? OR tag LIKE ? OR ai_polish LIKE ?
        ORDER BY created_at DESC, id DESC
        """,
        (like, like, like, like),
    ).fetchall()

"""SQLite persistence for Deadline Guardian."""

from __future__ import annotations

import os
import sqlite3
from datetime import date, datetime, timezone

from . import recurrence

VALID_CATEGORIES = (
    "Grant",
    "IRB/Ethics",
    "Course",
    "Student Evaluation",
    "Conference",
    "Manuscript",
    "Other",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS deadlines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    due_date TEXT NOT NULL,
    recurrence TEXT NOT NULL,
    recurrence_months INTEGER,
    notes TEXT,
    source_text TEXT,
    extraction_method TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    created_at TEXT NOT NULL
);
"""


class DeadlineNotFoundError(LookupError):
    pass


class AlreadyCompletedError(ValueError):
    pass


class InvalidCategoryError(ValueError):
    pass


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection(db_path: str) -> sqlite3.Connection:
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def validate_category(category: str) -> None:
    if category not in VALID_CATEGORIES:
        raise InvalidCategoryError(
            f"category must be one of {VALID_CATEGORIES}, got {category!r}"
        )


def add_deadline(
    conn: sqlite3.Connection,
    title: str,
    category: str,
    due_date: date,
    recurrence_rule: str = "none",
    recurrence_months: int | None = None,
    notes: str | None = None,
    source_text: str | None = None,
    extraction_method: str = "manual",
) -> int:
    validate_category(category)
    recurrence.validate_recurrence(recurrence_rule, recurrence_months)
    cursor = conn.execute(
        """
        INSERT INTO deadlines
            (title, category, due_date, recurrence, recurrence_months,
             notes, source_text, extraction_method, completed, completed_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, ?)
        """,
        (
            title,
            category,
            due_date.isoformat(),
            recurrence_rule,
            recurrence_months,
            notes,
            source_text,
            extraction_method,
            _utcnow_iso(),
        ),
    )
    conn.commit()
    return cursor.lastrowid


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "category": row["category"],
        "due_date": row["due_date"],
        "recurrence": row["recurrence"],
        "recurrence_months": row["recurrence_months"],
        "notes": row["notes"],
        "source_text": row["source_text"],
        "extraction_method": row["extraction_method"],
        "completed": bool(row["completed"]),
        "completed_at": row["completed_at"],
        "created_at": row["created_at"],
    }


def list_deadlines(conn: sqlite3.Connection, include_completed: bool = True) -> list[dict]:
    query = "SELECT * FROM deadlines"
    if not include_completed:
        query += " WHERE completed = 0"
    query += " ORDER BY due_date ASC"
    rows = conn.execute(query).fetchall()
    return [_row_to_dict(r) for r in rows]


def get_deadline(conn: sqlite3.Connection, deadline_id: int) -> dict:
    row = conn.execute("SELECT * FROM deadlines WHERE id = ?", (deadline_id,)).fetchone()
    if row is None:
        raise DeadlineNotFoundError(f"No deadline with id={deadline_id}")
    return _row_to_dict(row)


def complete_deadline(
    conn: sqlite3.Connection, deadline_id: int, completed_on: date | None = None
) -> tuple[dict, dict | None]:
    """Mark a deadline complete. If it recurs, create the next occurrence.

    Returns (completed_deadline, next_deadline_or_None).
    """
    deadline = get_deadline(conn, deadline_id)
    if deadline["completed"]:
        raise AlreadyCompletedError(f"Deadline id={deadline_id} is already completed")

    completed_on = completed_on or date.today()
    conn.execute(
        "UPDATE deadlines SET completed = 1, completed_at = ? WHERE id = ?",
        (completed_on.isoformat(), deadline_id),
    )
    conn.commit()
    deadline["completed"] = True
    deadline["completed_at"] = completed_on.isoformat()

    next_due = recurrence.next_due_date(
        date.fromisoformat(deadline["due_date"]),
        deadline["recurrence"],
        deadline["recurrence_months"],
    )
    if next_due is None:
        return deadline, None

    next_id = add_deadline(
        conn,
        title=deadline["title"],
        category=deadline["category"],
        due_date=next_due,
        recurrence_rule=deadline["recurrence"],
        recurrence_months=deadline["recurrence_months"],
        notes=deadline["notes"],
        source_text=None,
        extraction_method="manual",
    )
    next_deadline = get_deadline(conn, next_id)
    return deadline, next_deadline

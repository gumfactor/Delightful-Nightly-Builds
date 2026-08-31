"""SQLite persistence for habit completions."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterator

_SCHEMA = """
CREATE TABLE IF NOT EXISTS completions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id TEXT NOT NULL,
    date TEXT NOT NULL,
    source TEXT NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(habit_id, date)
);
"""


class StreakDB:
    """Thin wrapper around a single SQLite file storing habit completions."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(_SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def add_completion(
        self,
        habit_id: str,
        completion_date: date,
        source: str,
        detail: str | None = None,
    ) -> bool:
        """Insert a completion. Returns False (not an error) if one already
        exists for this habit on this day — callers treat that as
        "already recorded", not a failure.
        """
        date_str = completion_date.isoformat()
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT 1 FROM completions WHERE habit_id = ? AND date = ?",
                (habit_id, date_str),
            ).fetchone()
            if existing:
                return False
            conn.execute(
                "INSERT INTO completions (habit_id, date, source, detail, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (habit_id, date_str, source, detail, datetime.now(timezone.utc).isoformat()),
            )
            return True

    def remove_completion(self, habit_id: str, completion_date: date) -> bool:
        """Delete a completion. Returns True if a row was actually removed."""
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM completions WHERE habit_id = ? AND date = ?",
                (habit_id, completion_date.isoformat()),
            )
            return cur.rowcount > 0

    def get_dates(self, habit_id: str) -> set[date]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT date FROM completions WHERE habit_id = ?", (habit_id,)
            ).fetchall()
        return {date.fromisoformat(row[0]) for row in rows}

    def get_all(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT habit_id, date, source, detail, created_at FROM completions "
                "ORDER BY date ASC"
            ).fetchall()
        return [
            {
                "habit_id": r[0],
                "date": r[1],
                "source": r[2],
                "detail": r[3],
                "created_at": r[4],
            }
            for r in rows
        ]

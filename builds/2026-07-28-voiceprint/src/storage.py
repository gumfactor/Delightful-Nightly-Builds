"""Local SQLite history for Voiceprint runs — no personal data, no network."""

from __future__ import annotations

import json
import os
import sqlite3


class HistoryStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        directory = os.path.dirname(os.path.abspath(db_path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    run_at TEXT NOT NULL,
                    word_count INTEGER NOT NULL,
                    score REAL NOT NULL,
                    flag_count INTEGER NOT NULL,
                    details_json TEXT NOT NULL
                )
                """
            )

    def record_run(
        self,
        file_path: str,
        run_at: str,
        word_count: int,
        score: float,
        flag_count: int,
        details: dict,
    ) -> int:
        normalized_path = os.path.abspath(file_path)
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO runs (file_path, run_at, word_count, score, flag_count, details_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized_path,
                    run_at,
                    word_count,
                    score,
                    flag_count,
                    json.dumps(details),
                ),
            )
            return cursor.lastrowid

    def get_history(self, file_path: str) -> list[dict]:
        normalized_path = os.path.abspath(file_path)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, file_path, run_at, word_count, score, flag_count, details_json
                FROM runs WHERE file_path = ? ORDER BY run_at ASC, id ASC
                """,
                (normalized_path,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "file_path": row["file_path"],
                "run_at": row["run_at"],
                "word_count": row["word_count"],
                "score": row["score"],
                "flag_count": row["flag_count"],
                "details": json.loads(row["details_json"]),
            }
            for row in rows
        ]

    def list_files(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT file_path FROM runs ORDER BY file_path ASC"
            ).fetchall()
        return [row["file_path"] for row in rows]

"""SQLite cache layer for Stats Coach.

Caches AI-generated explanations keyed on design parameter hash,
so repeated identical queries skip the API call.
"""

from __future__ import annotations
import hashlib
import json
import sqlite3
from pathlib import Path


def _hash_design(params: dict) -> str:
    canonical = json.dumps(params, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


class AdviceCache:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    design_hash TEXT UNIQUE NOT NULL,
                    test_name TEXT NOT NULL,
                    ai_explanation TEXT NOT NULL,
                    r_code TEXT NOT NULL,
                    python_code TEXT NOT NULL,
                    interpretation TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
            conn.commit()

    def get(self, params: dict) -> dict | None:
        design_hash = _hash_design(params)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM cache WHERE design_hash = ?", (design_hash,)
            ).fetchone()
        if row is None:
            return None
        return dict(row)

    def put(self, params: dict, data: dict) -> None:
        design_hash = _hash_design(params)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache
                    (design_hash, test_name, ai_explanation, r_code, python_code, interpretation)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    design_hash,
                    data["test_name"],
                    data["ai_explanation"],
                    data["r_code"],
                    data["python_code"],
                    data["interpretation"],
                ),
            )
            conn.commit()

    def hash_for(self, params: dict) -> str:
        return _hash_design(params)

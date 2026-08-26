"""Append-only SQLite persistence. Every check() call inserts a new row;
nothing is ever updated or deleted. The caller supplies run_timestamp so
this module never calls datetime.now() itself, keeping it deterministic
and trivially testable.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    thesis_text TEXT NOT NULL,
    run_timestamp TEXT NOT NULL,
    fetched_data_json TEXT NOT NULL,
    triggered_json TEXT NOT NULL,
    persona_scores_json TEXT NOT NULL,
    overall_score INTEGER NOT NULL,
    ai_polished INTEGER NOT NULL
);
"""


@dataclass
class CheckRow:
    id: int
    ticker: str
    thesis_text: str
    run_timestamp: str
    fetched_data: dict
    triggered: list
    persona_scores: dict
    overall_score: int
    ai_polished: bool


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def insert_check(conn: sqlite3.Connection, *, ticker: str, thesis_text: str, run_timestamp: str,
                  fetched_data: dict, triggered: list, persona_scores: dict,
                  overall_score: int, ai_polished: bool) -> int:
    cursor = conn.execute(
        """INSERT INTO checks
           (ticker, thesis_text, run_timestamp, fetched_data_json, triggered_json,
            persona_scores_json, overall_score, ai_polished)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            ticker,
            thesis_text,
            run_timestamp,
            json.dumps(fetched_data),
            json.dumps(triggered),
            json.dumps(persona_scores),
            overall_score,
            1 if ai_polished else 0,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def _row_to_check(row: tuple) -> CheckRow:
    (id_, ticker, thesis_text, run_timestamp, fetched_json, triggered_json,
     persona_json, overall_score, ai_polished) = row
    return CheckRow(
        id=id_,
        ticker=ticker,
        thesis_text=thesis_text,
        run_timestamp=run_timestamp,
        fetched_data=json.loads(fetched_json),
        triggered=json.loads(triggered_json),
        persona_scores=json.loads(persona_json),
        overall_score=overall_score,
        ai_polished=bool(ai_polished),
    )


def get_check(conn: sqlite3.Connection, check_id: int) -> Optional[CheckRow]:
    row = conn.execute("SELECT * FROM checks WHERE id = ?", (check_id,)).fetchone()
    return _row_to_check(row) if row else None


def history_for_ticker(conn: sqlite3.Connection, ticker: str) -> list[CheckRow]:
    rows = conn.execute(
        "SELECT * FROM checks WHERE ticker = ? ORDER BY id ASC", (ticker.upper(),)
    ).fetchall()
    return [_row_to_check(r) for r in rows]


def list_all(conn: sqlite3.Connection) -> list[CheckRow]:
    rows = conn.execute("SELECT * FROM checks ORDER BY id ASC").fetchall()
    return [_row_to_check(r) for r in rows]

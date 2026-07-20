"""Versioned local storage for CanFile knowledge cards (SQLite)."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    qid TEXT,
    wikidata_facts_json TEXT NOT NULL,
    wikipedia_summary TEXT,
    assessment_text TEXT NOT NULL,
    confidence TEXT NOT NULL,
    verdict TEXT NOT NULL,
    source_urls_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    version INTEGER NOT NULL
);
"""


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def _next_version(conn: sqlite3.Connection, company_name: str) -> int:
    row = conn.execute(
        "SELECT MAX(version) AS max_version FROM cards WHERE company_name = ?",
        (company_name,),
    ).fetchone()
    current_max = row["max_version"]
    return (current_max or 0) + 1


def insert_card(
    conn: sqlite3.Connection,
    company_name: str,
    qid: str | None,
    wikidata_facts: dict[str, Any],
    wikipedia_summary: str | None,
    assessment_text: str,
    confidence: str,
    verdict: str,
    source_urls: list[str],
) -> dict[str, Any]:
    version = _next_version(conn, company_name)
    created_at = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO cards (
            company_name, qid, wikidata_facts_json, wikipedia_summary,
            assessment_text, confidence, verdict, source_urls_json,
            created_at, version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            company_name,
            qid,
            json.dumps(wikidata_facts),
            wikipedia_summary,
            assessment_text,
            confidence,
            verdict,
            json.dumps(source_urls),
            created_at,
            version,
        ),
    )
    conn.commit()
    return _row_to_card(
        conn.execute("SELECT * FROM cards WHERE id = ?", (cursor.lastrowid,)).fetchone()
    )


def _row_to_card(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "company_name": row["company_name"],
        "qid": row["qid"],
        "wikidata_facts": json.loads(row["wikidata_facts_json"]),
        "wikipedia_summary": row["wikipedia_summary"],
        "assessment_text": row["assessment_text"],
        "confidence": row["confidence"],
        "verdict": row["verdict"],
        "source_urls": json.loads(row["source_urls_json"]),
        "created_at": row["created_at"],
        "version": row["version"],
    }


def list_latest(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT c.* FROM cards c
        INNER JOIN (
            SELECT company_name, MAX(version) AS max_version
            FROM cards GROUP BY company_name
        ) latest
        ON c.company_name = latest.company_name AND c.version = latest.max_version
        ORDER BY c.company_name COLLATE NOCASE ASC
        """
    ).fetchall()
    return [_row_to_card(row) for row in rows]


def get_history(conn: sqlite3.Connection, company_name: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM cards WHERE company_name = ? ORDER BY version ASC",
        (company_name,),
    ).fetchall()
    return [_row_to_card(row) for row in rows]


def search(conn: sqlite3.Connection, term: str) -> list[dict[str, Any]]:
    like_term = f"%{term}%"
    rows = conn.execute(
        """
        SELECT c.* FROM cards c
        INNER JOIN (
            SELECT company_name, MAX(version) AS max_version
            FROM cards GROUP BY company_name
        ) latest
        ON c.company_name = latest.company_name AND c.version = latest.max_version
        WHERE c.company_name LIKE ? COLLATE NOCASE OR c.assessment_text LIKE ? COLLATE NOCASE
        ORDER BY c.company_name COLLATE NOCASE ASC
        """,
        (like_term, like_term),
    ).fetchall()
    return [_row_to_card(row) for row in rows]

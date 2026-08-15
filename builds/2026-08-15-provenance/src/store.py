"""SQLite-backed cache and append-only history for business resolutions.

A business is never overwritten — every ``save_resolution`` call inserts a
new versioned row, and ``get_latest`` returns the newest one. This mirrors
the "never overwrite, always version" pattern the rest of this catalog's
research-ledger builds (CanFile, Manuscript Pipeline, Panel Prep) use, so a
business's classification history stays inspectable across repeated runs.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS resolutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    business_key TEXT NOT NULL,
    business_name TEXT NOT NULL,
    website TEXT,
    wikidata_qid TEXT,
    verdict TEXT NOT NULL,
    confidence REAL NOT NULL,
    evidence TEXT NOT NULL,
    ai_note TEXT,
    resolved_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_business_key ON resolutions(business_key);
"""

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_key(name: str) -> str:
    """Normalize a business name into a stable cache key."""
    collapsed = _WHITESPACE_RE.sub(" ", (name or "").strip())
    return collapsed.casefold()


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def save_resolution(
    conn: sqlite3.Connection,
    *,
    business_name: str,
    website: Optional[str],
    wikidata_qid: Optional[str],
    verdict: str,
    confidence: float,
    evidence: str,
    ai_note: Optional[str],
    resolved_at: str,
) -> int:
    """Insert a new resolution version for a business. Returns the new row id."""
    key = normalize_key(business_name)
    cursor = conn.execute(
        """
        INSERT INTO resolutions
            (business_key, business_name, website, wikidata_qid, verdict, confidence, evidence, ai_note, resolved_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (key, business_name, website, wikidata_qid, verdict, confidence, evidence, ai_note, resolved_at),
    )
    conn.commit()
    return cursor.lastrowid


def get_latest(conn: sqlite3.Connection, business_name: str) -> Optional[sqlite3.Row]:
    """Return the most recent resolution for a business, or None if never resolved."""
    key = normalize_key(business_name)
    row = conn.execute(
        "SELECT * FROM resolutions WHERE business_key = ? ORDER BY id DESC LIMIT 1",
        (key,),
    ).fetchone()
    return row


def get_history(conn: sqlite3.Connection, business_name: str) -> list[sqlite3.Row]:
    """Return every resolution version for a business, oldest first."""
    key = normalize_key(business_name)
    return conn.execute(
        "SELECT * FROM resolutions WHERE business_key = ? ORDER BY id ASC",
        (key,),
    ).fetchall()

"""SQLite storage and search ranking for Snipvault."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS snippets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    language TEXT NOT NULL,
    code TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '',
    source TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    usage_count INTEGER NOT NULL DEFAULT 0
);
"""


@dataclass
class Snippet:
    id: int
    title: str
    language: str
    code: str
    description: str = ""
    tags: list = field(default_factory=list)
    source: str | None = None
    created_at: str = ""
    updated_at: str = ""
    usage_count: int = 0

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Snippet":
        tags = [t for t in row["tags"].split(",") if t]
        return cls(
            id=row["id"],
            title=row["title"],
            language=row["language"],
            code=row["code"],
            description=row["description"],
            tags=tags,
            source=row["source"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            usage_count=row["usage_count"],
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def add_snippet(
    conn: sqlite3.Connection,
    title: str,
    language: str,
    code: str,
    description: str = "",
    tags: list | None = None,
    source: str | None = None,
) -> Snippet:
    if not title.strip():
        raise ValueError("title must not be empty")
    if not code.strip():
        raise ValueError("code must not be empty")
    tags = tags or []
    normalized_tags = ",".join(sorted({t.strip().lower() for t in tags if t.strip()}))
    now = _now()
    cur = conn.execute(
        """INSERT INTO snippets (title, language, code, description, tags, source, created_at, updated_at, usage_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)""",
        (title, language, code, description, normalized_tags, source, now, now),
    )
    conn.commit()
    return get_snippet(conn, cur.lastrowid, bump_usage=False)


def get_snippet(conn: sqlite3.Connection, snippet_id: int, bump_usage: bool = True) -> Snippet | None:
    row = conn.execute("SELECT * FROM snippets WHERE id = ?", (snippet_id,)).fetchone()
    if row is None:
        return None
    if bump_usage:
        conn.execute("UPDATE snippets SET usage_count = usage_count + 1 WHERE id = ?", (snippet_id,))
        conn.commit()
        row = conn.execute("SELECT * FROM snippets WHERE id = ?", (snippet_id,)).fetchone()
    return Snippet.from_row(row)


def remove_snippet(conn: sqlite3.Connection, snippet_id: int) -> bool:
    cur = conn.execute("DELETE FROM snippets WHERE id = ?", (snippet_id,))
    conn.commit()
    return cur.rowcount > 0


def list_snippets(
    conn: sqlite3.Connection,
    language: str | None = None,
    tag: str | None = None,
) -> list:
    query = "SELECT * FROM snippets WHERE 1=1"
    params: list = []
    if language:
        query += " AND lower(language) = ?"
        params.append(language.lower())
    if tag:
        query += " AND (',' || tags || ',') LIKE ?"
        params.append(f"%,{tag.lower()},%")
    query += " ORDER BY updated_at DESC"
    rows = conn.execute(query, params).fetchall()
    return [Snippet.from_row(r) for r in rows]


def search_snippets(conn: sqlite3.Connection, keywords: list) -> list:
    """Deterministic ranked keyword search.

    Weighting: title match > tag match > description match > code match,
    with usage_count and recency as tie-breakers. A snippet must match at
    least one keyword in at least one field to be returned.
    """
    keywords = [k.strip().lower() for k in keywords if k.strip()]
    if not keywords:
        return []

    rows = conn.execute("SELECT * FROM snippets").fetchall()
    scored = []
    for row in rows:
        title = row["title"].lower()
        tags = row["tags"].lower()
        description = row["description"].lower()
        code = row["code"].lower()

        score = 0
        for kw in keywords:
            if kw in title:
                score += 8
            if kw in tags:
                score += 5
            if kw in description:
                score += 3
            if kw in code:
                score += 1
        if score > 0:
            scored.append((score, row))

    # Higher score wins; usage_count and updated_at (ISO 8601, sorts lexicographically) break ties.
    scored.sort(key=lambda pair: (pair[0], pair[1]["usage_count"], pair[1]["updated_at"]), reverse=True)

    return [Snippet.from_row(row) for _, row in scored]

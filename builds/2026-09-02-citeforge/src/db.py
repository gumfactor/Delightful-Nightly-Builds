"""Local SQLite persistence: the reference library and a Crossref DOI cache."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

from .models import Author, Reference

SCHEMA = """
CREATE TABLE IF NOT EXISTS references_lib (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ref_type TEXT NOT NULL,
    authors_json TEXT NOT NULL,
    year TEXT,
    title TEXT NOT NULL,
    container_title TEXT,
    volume TEXT,
    issue TEXT,
    pages TEXT,
    doi TEXT,
    url TEXT,
    source TEXT,
    needs_review INTEGER NOT NULL DEFAULT 0,
    dedupe_key TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS crossref_cache (
    doi TEXT PRIMARY KEY,
    raw_json TEXT NOT NULL,
    fetched_at TEXT NOT NULL
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_reference(conn: sqlite3.Connection, ref: Reference) -> tuple[int, bool]:
    """Insert or update by dedupe_key. Returns (id, was_new)."""
    key = ref.dedupe_key()
    row = conn.execute("SELECT id FROM references_lib WHERE dedupe_key = ?", (key,)).fetchone()
    authors_json = json.dumps([a.to_dict() for a in ref.authors])
    if row:
        conn.execute(
            """UPDATE references_lib SET ref_type=?, authors_json=?, year=?, title=?,
               container_title=?, volume=?, issue=?, pages=?, doi=?, url=?, source=?,
               needs_review=? WHERE id=?""",
            (
                ref.ref_type, authors_json, ref.year, ref.title, ref.container_title,
                ref.volume, ref.issue, ref.pages, ref.doi, ref.url, ref.source,
                int(ref.needs_review), row["id"],
            ),
        )
        conn.commit()
        return row["id"], False
    cursor = conn.execute(
        """INSERT INTO references_lib
           (ref_type, authors_json, year, title, container_title, volume, issue,
            pages, doi, url, source, needs_review, dedupe_key, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            ref.ref_type, authors_json, ref.year, ref.title, ref.container_title,
            ref.volume, ref.issue, ref.pages, ref.doi, ref.url, ref.source,
            int(ref.needs_review), key, _now(),
        ),
    )
    conn.commit()
    return cursor.lastrowid, True


def _row_to_reference(row: sqlite3.Row) -> Reference:
    authors = [Author.from_dict(d) for d in json.loads(row["authors_json"])]
    return Reference(
        ref_type=row["ref_type"],
        authors=authors,
        year=row["year"] or "",
        title=row["title"] or "",
        container_title=row["container_title"] or "",
        volume=row["volume"] or "",
        issue=row["issue"] or "",
        pages=row["pages"] or "",
        doi=row["doi"] or "",
        url=row["url"] or "",
        source=row["source"] or "manual",
        needs_review=bool(row["needs_review"]),
        ref_id=row["id"],
    )


def list_references(conn: sqlite3.Connection) -> list[Reference]:
    rows = conn.execute("SELECT * FROM references_lib ORDER BY id ASC").fetchall()
    return [_row_to_reference(r) for r in rows]


def get_references(conn: sqlite3.Connection, ids: list[int]) -> list[Reference]:
    if not ids:
        return list_references(conn)
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"SELECT * FROM references_lib WHERE id IN ({placeholders}) ORDER BY id ASC", ids  # noqa: S608 (fixed placeholder count, no interpolated values)
    ).fetchall()
    return [_row_to_reference(r) for r in rows]


def remove_reference(conn: sqlite3.Connection, ref_id: int) -> bool:
    cursor = conn.execute("DELETE FROM references_lib WHERE id = ?", (ref_id,))
    conn.commit()
    return cursor.rowcount > 0


def get_cached_crossref(conn: sqlite3.Connection, doi: str) -> dict | None:
    row = conn.execute("SELECT raw_json FROM crossref_cache WHERE doi = ?", (doi,)).fetchone()
    if row:
        return json.loads(row["raw_json"])
    return None


def set_cached_crossref(conn: sqlite3.Connection, doi: str, message: dict) -> None:
    conn.execute(
        "INSERT INTO crossref_cache (doi, raw_json, fetched_at) VALUES (?, ?, ?) "
        "ON CONFLICT(doi) DO UPDATE SET raw_json=excluded.raw_json, fetched_at=excluded.fetched_at",
        (doi, json.dumps(message), _now()),
    )
    conn.commit()

"""SQLite storage layer for the Connectome knowledge base."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    indexed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT UNIQUE NOT NULL,
    doc_freq INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS note_concepts (
    note_id INTEGER NOT NULL REFERENCES notes(id),
    concept_id INTEGER NOT NULL REFERENCES concepts(id),
    weight REAL NOT NULL,
    PRIMARY KEY (note_id, concept_id)
);

CREATE TABLE IF NOT EXISTS links (
    note_a INTEGER NOT NULL REFERENCES notes(id),
    note_b INTEGER NOT NULL REFERENCES notes(id),
    score REAL NOT NULL,
    shared_concepts TEXT NOT NULL,
    PRIMARY KEY (note_a, note_b)
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_note_by_path(conn: sqlite3.Connection, path: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM notes WHERE path = ?", (path,)).fetchone()


def all_notes(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM notes ORDER BY title").fetchall()


def upsert_note(conn: sqlite3.Connection, path: str, title: str, body: str, content_hash: str) -> int:
    existing = get_note_by_path(conn, path)
    if existing:
        conn.execute(
            "UPDATE notes SET title=?, body=?, content_hash=?, indexed_at=? WHERE id=?",
            (title, body, content_hash, now_iso(), existing["id"]),
        )
        return existing["id"]
    cursor = conn.execute(
        "INSERT INTO notes (path, title, body, content_hash, indexed_at) VALUES (?, ?, ?, ?, ?)",
        (path, title, body, content_hash, now_iso()),
    )
    return cursor.lastrowid


def delete_note(conn: sqlite3.Connection, note_id: int) -> None:
    conn.execute("DELETE FROM note_concepts WHERE note_id = ?", (note_id,))
    conn.execute("DELETE FROM links WHERE note_a = ? OR note_b = ?", (note_id, note_id))
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))


def replace_note_concepts(conn: sqlite3.Connection, note_id: int, concepts: list[tuple[str, float]]) -> None:
    conn.execute("DELETE FROM note_concepts WHERE note_id = ?", (note_id,))
    for term, weight in concepts:
        concept_id = get_or_create_concept(conn, term)
        conn.execute(
            "INSERT INTO note_concepts (note_id, concept_id, weight) VALUES (?, ?, ?)",
            (note_id, concept_id, weight),
        )


def get_or_create_concept(conn: sqlite3.Connection, term: str) -> int:
    row = conn.execute("SELECT id FROM concepts WHERE term = ?", (term,)).fetchone()
    if row:
        return row["id"]
    cursor = conn.execute("INSERT INTO concepts (term, doc_freq) VALUES (?, 0)", (term,))
    return cursor.lastrowid


def recompute_doc_frequencies(conn: sqlite3.Connection) -> None:
    conn.execute("""
        UPDATE concepts SET doc_freq = (
            SELECT COUNT(DISTINCT note_id) FROM note_concepts WHERE concept_id = concepts.id
        )
    """)
    conn.execute("DELETE FROM concepts WHERE doc_freq = 0")


def get_note_concepts(conn: sqlite3.Connection, note_id: int) -> dict[str, float]:
    rows = conn.execute("""
        SELECT c.term, nc.weight FROM note_concepts nc
        JOIN concepts c ON c.id = nc.concept_id
        WHERE nc.note_id = ?
    """, (note_id,)).fetchall()
    return {row["term"]: row["weight"] for row in rows}


def get_all_note_concepts(conn: sqlite3.Connection) -> dict[int, dict[str, float]]:
    result: dict[int, dict[str, float]] = {}
    for note in all_notes(conn):
        result[note["id"]] = get_note_concepts(conn, note["id"])
    return result


def get_doc_frequencies(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute("SELECT term, doc_freq FROM concepts").fetchall()
    return {row["term"]: row["doc_freq"] for row in rows}


def replace_all_links(conn: sqlite3.Connection, links) -> None:
    conn.execute("DELETE FROM links")
    for link in links:
        conn.execute(
            "INSERT INTO links (note_a, note_b, score, shared_concepts) VALUES (?, ?, ?, ?)",
            (link.note_a, link.note_b, link.score, ",".join(link.shared_concepts)),
        )


def get_all_links(conn: sqlite3.Connection):
    from linking import Link
    rows = conn.execute("SELECT * FROM links").fetchall()
    return [
        Link(
            row["note_a"],
            row["note_b"],
            row["score"],
            row["shared_concepts"].split(",") if row["shared_concepts"] else [],
        )
        for row in rows
    ]


def search_notes(conn: sqlite3.Connection, query: str) -> list[sqlite3.Row]:
    like = f"%{query.lower()}%"
    return conn.execute("""
        SELECT DISTINCT n.* FROM notes n
        LEFT JOIN note_concepts nc ON nc.note_id = n.id
        LEFT JOIN concepts c ON c.id = nc.concept_id
        WHERE LOWER(n.title) LIKE ? OR LOWER(n.body) LIKE ? OR LOWER(c.term) LIKE ?
        ORDER BY n.title
    """, (like, like, like)).fetchall()

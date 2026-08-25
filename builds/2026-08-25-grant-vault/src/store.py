"""SQLite persistence for Grant Vault."""

import hashlib
import json
import sqlite3
from datetime import datetime, timezone

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    content_hash TEXT NOT NULL,
    ingested_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    chunk_index INTEGER NOT NULL,
    section_type TEXT NOT NULL,
    text TEXT NOT NULL,
    reuse_score INTEGER NOT NULL,
    reuse_tier TEXT NOT NULL,
    tags TEXT NOT NULL,
    ai_summary TEXT,
    created_at TEXT NOT NULL
);
"""


def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn


def compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_document_hash(conn: sqlite3.Connection, path: str) -> str | None:
    row = conn.execute(
        "SELECT content_hash FROM documents WHERE path = ?", (path,)
    ).fetchone()
    return row["content_hash"] if row else None


def get_document_id(conn: sqlite3.Connection, path: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM documents WHERE path = ?", (path,)
    ).fetchone()
    return row["id"] if row else None


def upsert_document(conn: sqlite3.Connection, path: str, content_hash: str) -> int:
    now = datetime.now(timezone.utc).isoformat()
    existing_id = get_document_id(conn, path)
    if existing_id is not None:
        conn.execute(
            "UPDATE documents SET content_hash = ?, ingested_at = ? WHERE id = ?",
            (content_hash, now, existing_id),
        )
        conn.commit()
        return existing_id

    cursor = conn.execute(
        "INSERT INTO documents (path, content_hash, ingested_at) VALUES (?, ?, ?)",
        (path, content_hash, now),
    )
    conn.commit()
    return cursor.lastrowid


def delete_chunks_for_document(conn: sqlite3.Connection, document_id: int) -> None:
    conn.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
    conn.commit()


def insert_chunk(
    conn: sqlite3.Connection,
    document_id: int,
    chunk_index: int,
    section_type: str,
    text: str,
    reuse_score: int,
    reuse_tier: str,
    tags: list[str],
    ai_summary: str | None,
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        """INSERT INTO chunks
           (document_id, chunk_index, section_type, text, reuse_score,
            reuse_tier, tags, ai_summary, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            document_id,
            chunk_index,
            section_type,
            text,
            reuse_score,
            reuse_tier,
            json.dumps(tags),
            ai_summary,
            now,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_all_chunks(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """SELECT chunks.*, documents.path AS document_path
           FROM chunks JOIN documents ON chunks.document_id = documents.id
           ORDER BY documents.path, chunks.chunk_index"""
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_all_chunk_texts(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT text FROM chunks").fetchall()
    return [row["text"] for row in rows]


def _row_to_dict(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["tags"] = json.loads(data["tags"])
    return data

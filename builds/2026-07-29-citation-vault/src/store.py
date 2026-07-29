"""SQLite persistence for Citation Vault: papers and notes."""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

VALID_STATUSES = ("to-read", "reading", "read", "cited")

SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doi TEXT UNIQUE,
    title TEXT NOT NULL,
    authors TEXT NOT NULL DEFAULT '[]',
    year INTEGER,
    journal TEXT,
    abstract TEXT,
    status TEXT NOT NULL DEFAULT 'to-read',
    tags TEXT NOT NULL DEFAULT '[]',
    added_at TEXT NOT NULL,
    status_changed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER NOT NULL REFERENCES papers(id),
    text TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


class DuplicateDoiError(Exception):
    pass


class PaperNotFoundError(Exception):
    pass


class InvalidStatusError(Exception):
    pass


def add_paper(
    conn: sqlite3.Connection,
    title: str,
    authors: list,
    year: Optional[int] = None,
    journal: Optional[str] = None,
    abstract: Optional[str] = None,
    doi: Optional[str] = None,
    status: str = "to-read",
    tags: Optional[list] = None,
) -> int:
    if status not in VALID_STATUSES:
        raise InvalidStatusError(f"Invalid status: {status}")
    if doi:
        existing = conn.execute("SELECT id FROM papers WHERE doi = ?", (doi,)).fetchone()
        if existing:
            raise DuplicateDoiError(f"A paper with DOI {doi} already exists (id={existing['id']})")
    ts = now_iso()
    cur = conn.execute(
        """INSERT INTO papers (doi, title, authors, year, journal, abstract, status, tags, added_at, status_changed_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            doi,
            title,
            json.dumps(authors or []),
            year,
            journal,
            abstract,
            status,
            json.dumps(tags or []),
            ts,
            ts,
        ),
    )
    conn.commit()
    return cur.lastrowid


def get_paper(conn: sqlite3.Connection, paper_id: int) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
    if row is None:
        raise PaperNotFoundError(f"No paper with id {paper_id}")
    return row


def list_papers(
    conn: sqlite3.Connection,
    status: Optional[str] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
) -> list:
    rows = conn.execute("SELECT * FROM papers ORDER BY added_at DESC").fetchall()
    result = []
    for row in rows:
        if status and row["status"] != status:
            continue
        if tag and tag not in json.loads(row["tags"]):
            continue
        if search:
            haystack = f"{row['title']} {row['authors']} {row['abstract'] or ''}".lower()
            if search.lower() not in haystack:
                continue
        result.append(row)
    return result


def set_status(conn: sqlite3.Connection, paper_id: int, status: str) -> None:
    if status not in VALID_STATUSES:
        raise InvalidStatusError(f"Invalid status: {status}")
    get_paper(conn, paper_id)
    conn.execute(
        "UPDATE papers SET status = ?, status_changed_at = ? WHERE id = ?",
        (status, now_iso(), paper_id),
    )
    conn.commit()


def set_tags(conn: sqlite3.Connection, paper_id: int, tags: list) -> None:
    get_paper(conn, paper_id)
    conn.execute("UPDATE papers SET tags = ? WHERE id = ?", (json.dumps(tags), paper_id))
    conn.commit()


def add_note(conn: sqlite3.Connection, paper_id: int, text: str) -> int:
    get_paper(conn, paper_id)
    cur = conn.execute(
        "INSERT INTO notes (paper_id, text, created_at) VALUES (?, ?, ?)",
        (paper_id, text, now_iso()),
    )
    conn.commit()
    return cur.lastrowid


def get_notes(conn: sqlite3.Connection, paper_id: int) -> list:
    return conn.execute(
        "SELECT * FROM notes WHERE paper_id = ? ORDER BY created_at ASC", (paper_id,)
    ).fetchall()


def paper_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "doi": row["doi"],
        "title": row["title"],
        "authors": json.loads(row["authors"]),
        "year": row["year"],
        "journal": row["journal"],
        "abstract": row["abstract"],
        "status": row["status"],
        "tags": json.loads(row["tags"]),
        "added_at": row["added_at"],
        "status_changed_at": row["status_changed_at"],
    }

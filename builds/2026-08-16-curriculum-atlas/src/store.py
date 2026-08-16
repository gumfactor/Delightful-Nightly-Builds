"""SQLite persistence layer for Curriculum Atlas."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field

SCHEMA = """
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    course_id INTEGER NOT NULL REFERENCES courses(id),
    term TEXT NOT NULL,
    source_path TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    raw_char_count INTEGER NOT NULL,
    UNIQUE(course_id, term, source_path)
);

CREATE TABLE IF NOT EXISTS concepts (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    display_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    source TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS objectives (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS concept_notes (
    normalized_name TEXT PRIMARY KEY,
    note TEXT NOT NULL,
    generated_at TEXT NOT NULL
);
"""


@dataclass
class Course:
    id: int
    name: str


@dataclass
class Document:
    id: int
    course_id: int
    course_name: str
    term: str
    source_path: str
    ingested_at: str
    raw_char_count: int


@dataclass
class Concept:
    id: int
    document_id: int
    display_name: str
    normalized_name: str
    source: str


@dataclass
class Objective:
    id: int
    document_id: int
    text: str


@dataclass
class ParsedDocument:
    concepts: list = field(default_factory=list)
    objectives: list = field(default_factory=list)


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def add_course(conn: sqlite3.Connection, name: str) -> Course:
    """Create a course if it doesn't exist yet; idempotent by name."""
    name = name.strip()
    if not name:
        raise ValueError("course name cannot be empty")
    conn.execute("INSERT OR IGNORE INTO courses (name) VALUES (?)", (name,))
    conn.commit()
    row = conn.execute("SELECT id, name FROM courses WHERE name = ?", (name,)).fetchone()
    return Course(id=row["id"], name=row["name"])


def get_course(conn: sqlite3.Connection, name: str) -> Course | None:
    row = conn.execute("SELECT id, name FROM courses WHERE name = ?", (name,)).fetchone()
    if row is None:
        return None
    return Course(id=row["id"], name=row["name"])


def list_courses(conn: sqlite3.Connection) -> list[Course]:
    rows = conn.execute("SELECT id, name FROM courses ORDER BY name").fetchall()
    return [Course(id=r["id"], name=r["name"]) for r in rows]


def ingest_document(
    conn: sqlite3.Connection,
    course_id: int,
    term: str,
    source_path: str,
    ingested_at: str,
    raw_char_count: int,
    parsed: ParsedDocument,
) -> Document:
    """Insert or replace a document and its concepts/objectives.

    Re-ingesting the same (course_id, term, source_path) deletes the prior
    document's concepts/objectives rather than duplicating them.
    """
    existing = conn.execute(
        "SELECT id FROM documents WHERE course_id = ? AND term = ? AND source_path = ?",
        (course_id, term, source_path),
    ).fetchone()
    if existing is not None:
        doc_id = existing["id"]
        conn.execute("DELETE FROM concepts WHERE document_id = ?", (doc_id,))
        conn.execute("DELETE FROM objectives WHERE document_id = ?", (doc_id,))
        conn.execute(
            "UPDATE documents SET ingested_at = ?, raw_char_count = ? WHERE id = ?",
            (ingested_at, raw_char_count, doc_id),
        )
    else:
        cur = conn.execute(
            "INSERT INTO documents (course_id, term, source_path, ingested_at, raw_char_count) "
            "VALUES (?, ?, ?, ?, ?)",
            (course_id, term, source_path, ingested_at, raw_char_count),
        )
        doc_id = cur.lastrowid

    for c in parsed.concepts:
        conn.execute(
            "INSERT INTO concepts (document_id, display_name, normalized_name, source) "
            "VALUES (?, ?, ?, ?)",
            (doc_id, c.display_name, c.normalized_name, c.source),
        )
    for o in parsed.objectives:
        conn.execute(
            "INSERT INTO objectives (document_id, text) VALUES (?, ?)",
            (doc_id, o.text),
        )
    conn.commit()

    course_row = conn.execute("SELECT name FROM courses WHERE id = ?", (course_id,)).fetchone()
    return Document(
        id=doc_id,
        course_id=course_id,
        course_name=course_row["name"],
        term=term,
        source_path=source_path,
        ingested_at=ingested_at,
        raw_char_count=raw_char_count,
    )


def get_document(
    conn: sqlite3.Connection, course_id: int, term: str, source_path: str
) -> Document | None:
    row = conn.execute(
        "SELECT d.id, d.course_id, c.name AS course_name, d.term, d.source_path, "
        "d.ingested_at, d.raw_char_count FROM documents d "
        "JOIN courses c ON c.id = d.course_id "
        "WHERE d.course_id = ? AND d.term = ? AND d.source_path = ?",
        (course_id, term, source_path),
    ).fetchone()
    if row is None:
        return None
    return Document(**dict(row))


def list_documents(conn: sqlite3.Connection, course_id: int | None = None) -> list[Document]:
    query = (
        "SELECT d.id, d.course_id, c.name AS course_name, d.term, d.source_path, "
        "d.ingested_at, d.raw_char_count FROM documents d "
        "JOIN courses c ON c.id = d.course_id"
    )
    params: tuple = ()
    if course_id is not None:
        query += " WHERE d.course_id = ?"
        params = (course_id,)
    query += " ORDER BY c.name, d.term, d.source_path"
    rows = conn.execute(query, params).fetchall()
    return [Document(**dict(r)) for r in rows]


def list_concepts(
    conn: sqlite3.Connection, course_id: int | None = None, term: str | None = None
) -> list[dict]:
    """Return concepts joined with their document/course/term context."""
    query = (
        "SELECT co.id AS concept_id, co.display_name, co.normalized_name, co.source, "
        "d.id AS document_id, d.term, d.source_path, c.id AS course_id, c.name AS course_name "
        "FROM concepts co "
        "JOIN documents d ON d.id = co.document_id "
        "JOIN courses c ON c.id = d.course_id"
    )
    clauses = []
    params: list = []
    if course_id is not None:
        clauses.append("c.id = ?")
        params.append(course_id)
    if term is not None:
        clauses.append("d.term = ?")
        params.append(term)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY co.normalized_name"
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def list_objectives(
    conn: sqlite3.Connection, course_id: int | None = None, term: str | None = None
) -> list[dict]:
    query = (
        "SELECT o.id AS objective_id, o.text, d.id AS document_id, d.term, d.source_path, "
        "c.id AS course_id, c.name AS course_name "
        "FROM objectives o "
        "JOIN documents d ON d.id = o.document_id "
        "JOIN courses c ON c.id = d.course_id"
    )
    clauses = []
    params: list = []
    if course_id is not None:
        clauses.append("c.id = ?")
        params.append(course_id)
    if term is not None:
        clauses.append("d.term = ?")
        params.append(term)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY o.id"
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_cached_note(conn: sqlite3.Connection, normalized_name: str) -> str | None:
    row = conn.execute(
        "SELECT note FROM concept_notes WHERE normalized_name = ?", (normalized_name,)
    ).fetchone()
    return row["note"] if row else None


def save_note(conn: sqlite3.Connection, normalized_name: str, note: str, generated_at: str) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO concept_notes (normalized_name, note, generated_at) "
        "VALUES (?, ?, ?)",
        (normalized_name, note, generated_at),
    )
    conn.commit()

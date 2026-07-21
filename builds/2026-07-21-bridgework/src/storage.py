"""Local SQLite persistence for the Bridgework analogy library. Every
generated analogy is inserted as a new row — the library never overwrites
an entry, so the same (concept, domain, audience) triple can be regenerated
over time and both versions remain browsable.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS analogies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id TEXT NOT NULL,
    concept_name TEXT NOT NULL,
    subdomain TEXT NOT NULL,
    domain_id TEXT NOT NULL,
    domain_name TEXT NOT NULL,
    audience TEXT NOT NULL,
    hook TEXT NOT NULL,
    analogy TEXT NOT NULL,
    caveat TEXT NOT NULL,
    source TEXT NOT NULL,
    novelty_score REAL NOT NULL,
    created_at TEXT NOT NULL
);
"""

_COLUMNS = (
    "id",
    "concept_id",
    "concept_name",
    "subdomain",
    "domain_id",
    "domain_name",
    "audience",
    "hook",
    "analogy",
    "caveat",
    "source",
    "novelty_score",
    "created_at",
)


def connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in _COLUMNS}


def insert_analogy(conn: sqlite3.Connection, record: dict) -> int:
    cursor = conn.execute(
        """
        INSERT INTO analogies
            (concept_id, concept_name, subdomain, domain_id, domain_name,
             audience, hook, analogy, caveat, source, novelty_score, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record["concept_id"],
            record["concept_name"],
            record["subdomain"],
            record["domain_id"],
            record["domain_name"],
            record["audience"],
            record["hook"],
            record["analogy"],
            record["caveat"],
            record["source"],
            record["novelty_score"],
            record["created_at"],
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_analogy(conn: sqlite3.Connection, entry_id: int) -> Optional[dict]:
    row = conn.execute("SELECT * FROM analogies WHERE id = ?", (entry_id,)).fetchone()
    return _row_to_dict(row) if row else None


def list_analogies(
    conn: sqlite3.Connection,
    concept_id: Optional[str] = None,
    domain_id: Optional[str] = None,
    audience: Optional[str] = None,
    search: Optional[str] = None,
    limit: Optional[int] = None,
) -> list:
    clauses = []
    params: list = []
    if concept_id:
        clauses.append("concept_id = ?")
        params.append(concept_id)
    if domain_id:
        clauses.append("domain_id = ?")
        params.append(domain_id)
    if audience:
        clauses.append("audience = ?")
        params.append(audience)
    if search:
        clauses.append("(analogy LIKE ? OR hook LIKE ? OR concept_name LIKE ? OR domain_name LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like, like, like])

    query = "SELECT * FROM analogies"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY id DESC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    rows = conn.execute(query, params).fetchall()
    return [_row_to_dict(row) for row in rows]


def count_triple(conn: sqlite3.Connection, concept_id: str, domain_id: str, audience: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM analogies WHERE concept_id = ? AND domain_id = ? AND audience = ?",
        (concept_id, domain_id, audience),
    ).fetchone()
    return row["n"]


def usage_counts(conn: sqlite3.Connection) -> dict:
    rows = conn.execute(
        "SELECT concept_id, domain_id, audience, COUNT(*) AS n FROM analogies "
        "GROUP BY concept_id, domain_id, audience"
    ).fetchall()
    return {(row["concept_id"], row["domain_id"], row["audience"]): row["n"] for row in rows}


def all_analogy_texts(conn: sqlite3.Connection) -> list:
    rows = conn.execute("SELECT analogy FROM analogies").fetchall()
    return [row["analogy"] for row in rows]


def stats(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) AS n FROM analogies").fetchone()["n"]
    by_subdomain = conn.execute(
        "SELECT subdomain, COUNT(*) AS n FROM analogies GROUP BY subdomain"
    ).fetchall()
    by_source = conn.execute(
        "SELECT source, COUNT(*) AS n FROM analogies GROUP BY source"
    ).fetchall()
    distinct_triples = conn.execute(
        "SELECT COUNT(*) AS n FROM (SELECT DISTINCT concept_id, domain_id, audience FROM analogies)"
    ).fetchone()["n"]
    return {
        "total": total,
        "distinct_triples": distinct_triples,
        "by_subdomain": {row["subdomain"]: row["n"] for row in by_subdomain},
        "by_source": {row["source"]: row["n"] for row in by_source},
    }

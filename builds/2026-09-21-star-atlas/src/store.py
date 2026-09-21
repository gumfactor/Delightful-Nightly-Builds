"""SQLite persistence for Star Atlas."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS repos (
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    description TEXT,
    html_url TEXT NOT NULL,
    language TEXT,
    topics_json TEXT NOT NULL,
    stargazers_count INTEGER NOT NULL DEFAULT 0,
    starred_at TEXT NOT NULL,
    tag TEXT NOT NULL,
    note TEXT NOT NULL,
    source TEXT NOT NULL,
    ingested_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_repos_starred_at ON repos(starred_at);
CREATE INDEX IF NOT EXISTS idx_repos_tag ON repos(tag);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_repo(conn: sqlite3.Connection, repo: dict) -> None:
    conn.execute(
        """
        INSERT INTO repos (
            id, full_name, description, html_url, language, topics_json,
            stargazers_count, starred_at, tag, note, source, ingested_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            full_name=excluded.full_name,
            description=excluded.description,
            html_url=excluded.html_url,
            language=excluded.language,
            topics_json=excluded.topics_json,
            stargazers_count=excluded.stargazers_count,
            starred_at=excluded.starred_at,
            tag=excluded.tag,
            note=excluded.note,
            source=excluded.source,
            ingested_at=excluded.ingested_at
        """,
        (
            repo["id"],
            repo["full_name"],
            repo.get("description"),
            repo["html_url"],
            repo.get("language"),
            json.dumps(repo.get("topics") or []),
            repo.get("stargazers_count", 0),
            repo["starred_at"],
            repo["tag"],
            repo["note"],
            repo["source"],
            repo.get("ingested_at") or datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()


def latest_starred_at(conn: sqlite3.Connection) -> Optional[str]:
    row = conn.execute("SELECT MAX(starred_at) AS m FROM repos").fetchone()
    return row["m"] if row and row["m"] else None


def count_repos(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS c FROM repos").fetchone()
    return row["c"]


def _row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["topics"] = json.loads(d.pop("topics_json"))
    return d


def search_repos(
    conn: sqlite3.Connection,
    query: Optional[str] = None,
    tag: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 50,
) -> list:
    clauses = []
    params: list = []

    if query:
        clauses.append(
            "(full_name LIKE ? OR description LIKE ? OR topics_json LIKE ?)"
        )
        like = f"%{query}%"
        params.extend([like, like, like])
    if tag:
        clauses.append("tag = ?")
        params.append(tag)
    if language:
        clauses.append("language = ?")
        params.append(language)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT * FROM repos {where} ORDER BY starred_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    return [_row_to_dict(r) for r in rows]


def list_repos(
    conn: sqlite3.Connection,
    tag: Optional[str] = None,
    language: Optional[str] = None,
    limit: int = 200,
) -> list:
    return search_repos(conn, query=None, tag=tag, language=language, limit=limit)


def stats(conn: sqlite3.Connection) -> dict:
    total = count_repos(conn)
    by_tag = {
        r["tag"]: r["c"]
        for r in conn.execute(
            "SELECT tag, COUNT(*) AS c FROM repos GROUP BY tag ORDER BY c DESC"
        ).fetchall()
    }
    by_language = {
        (r["language"] or "Unknown"): r["c"]
        for r in conn.execute(
            "SELECT language, COUNT(*) AS c FROM repos GROUP BY language ORDER BY c DESC"
        ).fetchall()
    }
    latest = latest_starred_at(conn)
    return {
        "total": total,
        "by_tag": by_tag,
        "by_language": by_language,
        "latest_starred_at": latest,
    }

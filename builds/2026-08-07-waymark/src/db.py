"""SQLite storage layer for Waymark."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS repos (
    label TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    last_indexed_at TEXT
);

CREATE TABLE IF NOT EXISTS commits (
    repo_label TEXT NOT NULL,
    commit_hash TEXT NOT NULL,
    author TEXT,
    committed_at TEXT,
    subject TEXT,
    body TEXT,
    files_changed INTEGER,
    insertions INTEGER,
    deletions INTEGER,
    decision_score INTEGER,
    tags TEXT,
    summary TEXT,
    ai_summary TEXT,
    PRIMARY KEY (repo_label, commit_hash),
    FOREIGN KEY (repo_label) REFERENCES repos(label)
);

CREATE INDEX IF NOT EXISTS idx_commits_score ON commits(decision_score);
CREATE INDEX IF NOT EXISTS idx_commits_repo ON commits(repo_label);
"""


def default_db_path() -> Path:
    return Path.home() / ".waymark" / "waymark.db"


def connect(db_path: Path) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_repo(conn: sqlite3.Connection, label: str, path: str, indexed_at: str) -> None:
    conn.execute(
        """
        INSERT INTO repos (label, path, last_indexed_at)
        VALUES (?, ?, ?)
        ON CONFLICT(label) DO UPDATE SET path = excluded.path,
                                          last_indexed_at = excluded.last_indexed_at
        """,
        (label, path, indexed_at),
    )
    conn.commit()


def known_commit_hashes(conn: sqlite3.Connection, repo_label: str) -> set[str]:
    rows = conn.execute(
        "SELECT commit_hash FROM commits WHERE repo_label = ?", (repo_label,)
    ).fetchall()
    return {row["commit_hash"] for row in rows}


def insert_commits(conn: sqlite3.Connection, repo_label: str, records: Iterable[dict[str, Any]]) -> int:
    rows = list(records)
    if not rows:
        return 0
    conn.executemany(
        """
        INSERT OR IGNORE INTO commits (
            repo_label, commit_hash, author, committed_at, subject, body,
            files_changed, insertions, deletions, decision_score, tags,
            summary, ai_summary
        ) VALUES (
            :repo_label, :commit_hash, :author, :committed_at, :subject, :body,
            :files_changed, :insertions, :deletions, :decision_score, :tags,
            :summary, :ai_summary
        )
        """,
        [
            {
                "repo_label": repo_label,
                "commit_hash": r["commit_hash"],
                "author": r.get("author"),
                "committed_at": r.get("committed_at"),
                "subject": r.get("subject"),
                "body": r.get("body"),
                "files_changed": r.get("files_changed", 0),
                "insertions": r.get("insertions", 0),
                "deletions": r.get("deletions", 0),
                "decision_score": r.get("decision_score", 0),
                "tags": json.dumps(r.get("tags", [])),
                "summary": r.get("summary", ""),
                "ai_summary": r.get("ai_summary"),
            }
            for r in rows
        ],
    )
    conn.commit()
    return len(rows)


def list_repos(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT r.label, r.path, r.last_indexed_at,
               COUNT(c.commit_hash) AS commit_count,
               SUM(CASE WHEN c.decision_score >= 5 THEN 1 ELSE 0 END) AS decision_count
        FROM repos r
        LEFT JOIN commits c ON c.repo_label = r.label
        GROUP BY r.label
        ORDER BY r.label
        """
    ).fetchall()


def search_commits(
    conn: sqlite3.Connection,
    query: str | None = None,
    repo_label: str | None = None,
    tag: str | None = None,
    since: str | None = None,
    min_score: int = 0,
) -> list[sqlite3.Row]:
    clauses = ["decision_score >= ?"]
    params: list[Any] = [min_score]

    if repo_label:
        clauses.append("repo_label = ?")
        params.append(repo_label)
    if since:
        clauses.append("committed_at >= ?")
        params.append(since)
    if tag:
        clauses.append("tags LIKE ?")
        params.append(f'%"{tag}"%')
    if query:
        clauses.append("(subject LIKE ? OR body LIKE ? OR summary LIKE ? OR IFNULL(ai_summary, '') LIKE ?)")
        like = f"%{query}%"
        params.extend([like, like, like, like])

    where = " AND ".join(clauses)
    sql = f"""
        SELECT * FROM commits
        WHERE {where}
        ORDER BY decision_score DESC, committed_at DESC
    """
    return conn.execute(sql, params).fetchall()


def all_commits(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM commits ORDER BY committed_at DESC"
    ).fetchall()


def commits_needing_enrichment(conn: sqlite3.Connection, repo_label: str | None, limit: int) -> list[sqlite3.Row]:
    clauses = ["ai_summary IS NULL", "decision_score >= 5"]
    params: list[Any] = []
    if repo_label:
        clauses.append("repo_label = ?")
        params.append(repo_label)
    where = " AND ".join(clauses)
    params.append(limit)
    return conn.execute(
        f"""
        SELECT * FROM commits
        WHERE {where}
        ORDER BY decision_score DESC
        LIMIT ?
        """,
        params,
    ).fetchall()


def set_ai_summary(conn: sqlite3.Connection, repo_label: str, commit_hash: str, ai_summary: str) -> None:
    conn.execute(
        "UPDATE commits SET ai_summary = ? WHERE repo_label = ? AND commit_hash = ?",
        (ai_summary, repo_label, commit_hash),
    )
    conn.commit()

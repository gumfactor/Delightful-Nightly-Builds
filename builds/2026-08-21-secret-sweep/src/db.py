"""SQLite-backed finding baseline: dedup across re-scans, and an ack workflow
for confirmed false positives. Never stores a raw secret value — only a
masked preview and a SHA-256 hash (see src/redact.py).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repo_path TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    scope TEXT NOT NULL,
    file_path TEXT NOT NULL,
    line_number INTEGER,
    commit_sha TEXT NOT NULL DEFAULT '',
    pattern_name TEXT NOT NULL,
    severity TEXT NOT NULL,
    entropy REAL,
    masked_preview TEXT NOT NULL,
    match_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    ai_verdict TEXT,
    ai_rationale TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    UNIQUE(repo_path, scope, file_path, match_hash, commit_sha)
);
"""

_INSERT_FIELDS = [
    "repo_path", "repo_name", "scope", "file_path", "line_number", "commit_sha",
    "pattern_name", "severity", "entropy", "masked_preview", "match_hash",
    "ai_verdict", "ai_rationale",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def upsert_finding(conn: sqlite3.Connection, finding: dict) -> None:
    """Insert a new finding, or refresh last_seen (and AI fields) if it already exists."""
    now = utc_now_iso()
    row = {k: finding.get(k) for k in _INSERT_FIELDS}
    row["commit_sha"] = row["commit_sha"] or ""  # never NULL — NULLs don't dedup under UNIQUE
    placeholders = ", ".join(f":{k}" for k in _INSERT_FIELDS)
    columns = ", ".join(_INSERT_FIELDS)
    conn.execute(
        f"""
        INSERT INTO findings ({columns}, first_seen, last_seen)
        VALUES ({placeholders}, :first_seen, :last_seen)
        ON CONFLICT(repo_path, scope, file_path, match_hash, commit_sha)
        DO UPDATE SET last_seen = excluded.last_seen,
                      ai_verdict = excluded.ai_verdict,
                      ai_rationale = excluded.ai_rationale
        """,
        {**row, "first_seen": now, "last_seen": now},
    )
    conn.commit()


def get_findings(
    conn: sqlite3.Connection,
    repo_path: str | None = None,
    status: str | None = None,
    scope: str | None = None,
) -> list[sqlite3.Row]:
    query = "SELECT * FROM findings WHERE 1=1"
    params: list = []
    if repo_path is not None:
        query += " AND repo_path = ?"
        params.append(repo_path)
    if status is not None:
        query += " AND status = ?"
        params.append(status)
    if scope is not None:
        query += " AND scope = ?"
        params.append(scope)
    query += " ORDER BY severity ASC, last_seen DESC"
    return list(conn.execute(query, params).fetchall())


def ack_finding(conn: sqlite3.Connection, finding_id: int) -> bool:
    cursor = conn.execute(
        "UPDATE findings SET status = 'acknowledged' WHERE id = ?", (finding_id,)
    )
    conn.commit()
    return cursor.rowcount > 0


def count_new(conn: sqlite3.Connection, repo_path: str | None = None) -> int:
    query = "SELECT COUNT(*) FROM findings WHERE status = 'new'"
    params: list = []
    if repo_path is not None:
        query += " AND repo_path = ?"
        params.append(repo_path)
    return conn.execute(query, params).fetchone()[0]

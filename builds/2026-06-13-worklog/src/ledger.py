"""
SQLite event ledger — schema creation, event insertion with deduplication,
decision storage, workstream upsert, and query helpers.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Optional

SCHEMA_VERSION = 1

DDL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id            TEXT PRIMARY KEY,
    timestamp     TEXT NOT NULL,
    project_id    TEXT NOT NULL,
    type          TEXT NOT NULL,
    actor_kind    TEXT,
    actor_name    TEXT,
    summary       TEXT,
    status        TEXT,
    workstream_id TEXT,
    provider      TEXT NOT NULL,
    source_ref    TEXT,
    source_url    TEXT,
    metadata      TEXT
);

CREATE TABLE IF NOT EXISTS workstreams (
    id         TEXT PRIMARY KEY,
    title      TEXT,
    status     TEXT,
    created_at TEXT,
    updated_at TEXT,
    evidence   TEXT
);

CREATE TABLE IF NOT EXISTS decisions (
    id             TEXT PRIMARY KEY,
    event_id       TEXT,
    workstream_id  TEXT,
    summary        TEXT,
    reason         TEXT,
    alternatives   TEXT,
    timestamp      TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_project    ON events(project_id);
CREATE INDEX IF NOT EXISTS idx_events_type       ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_workstream ON events(workstream_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp  ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_decisions_ws      ON decisions(workstream_id);
"""


def make_event_id(provider: str, source_ref: str, event_type: str) -> str:
    """Deterministic event ID from provider + source ref + type (for deduplication)."""
    raw = f"{provider}:{event_type}:{source_ref}"
    return "evt_" + hashlib.sha256(raw.encode()).hexdigest()[:24]


def make_decision_id(event_id: str, summary: str) -> str:
    raw = f"{event_id}:{summary}"
    return "dec_" + hashlib.sha256(raw.encode()).hexdigest()[:24]


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@contextmanager
def open_db(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    """Context manager yielding an initialised, WAL-mode connection."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema(db_path: Path) -> None:
    """Create tables and record the schema version if not already done."""
    with open_db(db_path) as conn:
        conn.executescript(DDL)
        existing = conn.execute(
            "SELECT version FROM schema_version WHERE version = ?",
            (SCHEMA_VERSION,),
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, utcnow()),
            )


def insert_event(db_path: Path, event: dict[str, Any]) -> bool:
    """
    Insert an event row.  Returns True if inserted, False if it already existed
    (deduplication via deterministic primary key).
    """
    with open_db(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM events WHERE id = ?", (event["id"],)
        ).fetchone()
        if existing:
            return False
        conn.execute(
            """INSERT INTO events
               (id, timestamp, project_id, type, actor_kind, actor_name,
                summary, status, workstream_id, provider, source_ref, source_url, metadata)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                event["id"],
                event["timestamp"],
                event["project_id"],
                event["type"],
                event.get("actor_kind"),
                event.get("actor_name"),
                event.get("summary"),
                event.get("status"),
                event.get("workstream_id"),
                event["provider"],
                event.get("source_ref"),
                event.get("source_url"),
                json.dumps(event.get("metadata", {})),
            ),
        )
        return True


def insert_decision(db_path: Path, decision: dict[str, Any]) -> bool:
    """Insert a decision row. Returns True if inserted, False if duplicate."""
    with open_db(db_path) as conn:
        existing = conn.execute(
            "SELECT id FROM decisions WHERE id = ?", (decision["id"],)
        ).fetchone()
        if existing:
            return False
        conn.execute(
            """INSERT INTO decisions
               (id, event_id, workstream_id, summary, reason, alternatives, timestamp)
               VALUES (?,?,?,?,?,?,?)""",
            (
                decision["id"],
                decision.get("event_id"),
                decision.get("workstream_id"),
                decision.get("summary"),
                decision.get("reason"),
                json.dumps(decision.get("alternatives", [])),
                decision.get("timestamp", utcnow()),
            ),
        )
        return True


def upsert_workstream(db_path: Path, ws: dict[str, Any]) -> None:
    """Insert or update a workstream record."""
    with open_db(db_path) as conn:
        now = utcnow()
        conn.execute(
            """INSERT INTO workstreams (id, title, status, created_at, updated_at, evidence)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 title=excluded.title,
                 status=excluded.status,
                 updated_at=?,
                 evidence=excluded.evidence""",
            (
                ws["id"],
                ws.get("title"),
                ws.get("status", "active"),
                now,
                now,
                json.dumps(ws.get("evidence", [])),
                now,
            ),
        )


def assign_workstream(db_path: Path, event_id: str, workstream_id: str) -> None:
    """Update an event's workstream assignment."""
    with open_db(db_path) as conn:
        conn.execute(
            "UPDATE events SET workstream_id = ? WHERE id = ?",
            (workstream_id, event_id),
        )


def query_events(
    db_path: Path,
    project_id: str,
    since: Optional[str] = None,
    event_type: Optional[str] = None,
    workstream_id: Optional[str] = None,
    limit: int = 500,
) -> list[dict]:
    """Query events with optional filters; returns list of dicts."""
    clauses = ["project_id = ?"]
    params: list[Any] = [project_id]

    if since:
        clauses.append("timestamp >= ?")
        params.append(since)
    if event_type:
        clauses.append("type = ?")
        params.append(event_type)
    if workstream_id:
        clauses.append("workstream_id = ?")
        params.append(workstream_id)

    where = " AND ".join(clauses)
    params.append(limit)

    with open_db(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM events WHERE {where} ORDER BY timestamp DESC LIMIT ?",
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def query_workstreams(db_path: Path, project_id: str) -> list[dict]:
    """Return all workstreams that have at least one event for this project."""
    with open_db(db_path) as conn:
        rows = conn.execute(
            """SELECT w.*, COUNT(e.id) as event_count
               FROM workstreams w
               JOIN events e ON e.workstream_id = w.id AND e.project_id = ?
               GROUP BY w.id
               ORDER BY w.updated_at DESC""",
            (project_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def query_decisions(
    db_path: Path,
    keyword: Optional[str] = None,
    workstream_id: Optional[str] = None,
) -> list[dict]:
    """Return decisions, optionally filtered by keyword and/or workstream."""
    clauses: list[str] = []
    params: list[Any] = []

    if keyword:
        clauses.append("(summary LIKE ? OR reason LIKE ?)")
        like = f"%{keyword}%"
        params.extend([like, like])
    if workstream_id:
        clauses.append("workstream_id = ?")
        params.append(workstream_id)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    with open_db(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM decisions {where} ORDER BY timestamp DESC",
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def get_latest_event_of_type(db_path: Path, project_id: str, event_type: str) -> Optional[dict]:
    """Return the most recent event of a given type for this project."""
    with open_db(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM events WHERE project_id = ? AND type = ? ORDER BY timestamp DESC LIMIT 1",
            (project_id, event_type),
        ).fetchone()
    return dict(row) if row else None

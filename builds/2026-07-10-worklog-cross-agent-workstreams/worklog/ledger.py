"""SQLite-backed append-oriented event ledger."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Optional

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL,
    actor_kind TEXT NOT NULL,
    actor_name TEXT NOT NULL,
    summary TEXT NOT NULL,
    status TEXT NOT NULL,
    workstream_id TEXT,
    source_provider TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    source_url TEXT,
    relations TEXT NOT NULL,
    metadata TEXT NOT NULL,
    correlation TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_project ON events(project_id);
CREATE INDEX IF NOT EXISTS idx_events_workstream ON events(workstream_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);

CREATE TABLE IF NOT EXISTS workstreams (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_state (
    project_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    PRIMARY KEY (project_id, key)
);
"""


@dataclass
class Event:
    id: str
    project_id: str
    timestamp: str
    type: str
    actor_kind: str
    actor_name: str
    summary: str
    status: str
    source_provider: str
    source_ref: str
    workstream_id: Optional[str] = None
    source_url: Optional[str] = None
    relations: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    correlation: dict = field(default_factory=dict)

    def to_row(self) -> tuple:
        return (
            self.id,
            self.project_id,
            self.timestamp,
            self.type,
            self.actor_kind,
            self.actor_name,
            self.summary,
            self.status,
            self.workstream_id,
            self.source_provider,
            self.source_ref,
            self.source_url,
            json.dumps(self.relations),
            json.dumps(self.metadata),
            json.dumps(self.correlation),
        )

    @staticmethod
    def from_row(row: sqlite3.Row) -> "Event":
        return Event(
            id=row["id"],
            project_id=row["project_id"],
            timestamp=row["timestamp"],
            type=row["type"],
            actor_kind=row["actor_kind"],
            actor_name=row["actor_name"],
            summary=row["summary"],
            status=row["status"],
            workstream_id=row["workstream_id"],
            source_provider=row["source_provider"],
            source_ref=row["source_ref"],
            source_url=row["source_url"],
            relations=json.loads(row["relations"]),
            metadata=json.loads(row["metadata"]),
            correlation=json.loads(row["correlation"]),
        )


class Ledger:
    """Thin SQLite wrapper. One Ledger instance = one open connection to one data dir."""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self.db_path = os.path.join(data_dir, "ledger.db")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    def _init_schema(self) -> None:
        with self.conn:
            self.conn.executescript(_SCHEMA)
            self.conn.execute(
                "INSERT OR IGNORE INTO schema_meta (key, value) VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "Ledger":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- events -----------------------------------------------------------------

    def upsert_event(self, event: Event) -> bool:
        """Insert an event if it doesn't already exist. Returns True if newly inserted."""
        with self.conn:
            cursor = self.conn.execute(
                "INSERT OR IGNORE INTO events "
                "(id, project_id, timestamp, type, actor_kind, actor_name, summary, status, "
                " workstream_id, source_provider, source_ref, source_url, relations, "
                " metadata, correlation) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                event.to_row(),
            )
            return cursor.rowcount > 0

    def set_event_workstream(self, event_id: str, workstream_id: str, correlation: dict) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE events SET workstream_id = ?, correlation = ? WHERE id = ?",
                (workstream_id, json.dumps(correlation), event_id),
            )

    def get_event(self, event_id: str) -> Optional[Event]:
        row = self.conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        return Event.from_row(row) if row else None

    def events_for_project(self, project_id: str, event_type: Optional[str] = None) -> list[Event]:
        if event_type:
            rows = self.conn.execute(
                "SELECT * FROM events WHERE project_id = ? AND type = ? ORDER BY timestamp ASC",
                (project_id, event_type),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM events WHERE project_id = ? ORDER BY timestamp ASC",
                (project_id,),
            ).fetchall()
        return [Event.from_row(r) for r in rows]

    def events_for_workstream(self, workstream_id: str) -> list[Event]:
        rows = self.conn.execute(
            "SELECT * FROM events WHERE workstream_id = ? ORDER BY timestamp ASC",
            (workstream_id,),
        ).fetchall()
        return [Event.from_row(r) for r in rows]

    def recent_commit_events(self, project_id: str, limit: int = 50) -> list[Event]:
        rows = self.conn.execute(
            "SELECT * FROM events WHERE project_id = ? AND type = 'commit' "
            "ORDER BY timestamp DESC LIMIT ?",
            (project_id, limit),
        ).fetchall()
        return [Event.from_row(r) for r in rows]

    def find_event_by_source_ref(self, project_id: str, source_provider: str, source_ref: str) -> Optional[Event]:
        row = self.conn.execute(
            "SELECT * FROM events WHERE project_id = ? AND source_provider = ? AND source_ref = ?",
            (project_id, source_provider, source_ref),
        ).fetchone()
        return Event.from_row(row) if row else None

    def search_events(self, project_id: str, query: str) -> list[Event]:
        like = f"%{query.lower()}%"
        rows = self.conn.execute(
            "SELECT * FROM events WHERE project_id = ? AND "
            "(LOWER(summary) LIKE ? OR LOWER(metadata) LIKE ?) ORDER BY timestamp ASC",
            (project_id, like, like),
        ).fetchall()
        return [Event.from_row(r) for r in rows]

    # -- workstreams --------------------------------------------------------------

    def upsert_workstream(self, workstream_id: str, project_id: str, title: str, timestamp: str) -> None:
        with self.conn:
            existing = self.conn.execute(
                "SELECT id FROM workstreams WHERE id = ?", (workstream_id,)
            ).fetchone()
            if existing:
                self.conn.execute(
                    "UPDATE workstreams SET updated_at = ? WHERE id = ? AND updated_at < ?",
                    (timestamp, workstream_id, timestamp),
                )
            else:
                self.conn.execute(
                    "INSERT INTO workstreams (id, project_id, title, created_at, updated_at) "
                    "VALUES (?,?,?,?,?)",
                    (workstream_id, project_id, title, timestamp, timestamp),
                )

    def get_workstream(self, workstream_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM workstreams WHERE id = ?", (workstream_id,)
        ).fetchone()
        return dict(row) if row else None

    def workstreams_for_project(self, project_id: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM workstreams WHERE project_id = ? ORDER BY updated_at DESC",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def find_workstream_by_issue(self, project_id: str, issue_number: int) -> Optional[str]:
        target_ref = f"issue:{issue_number}"
        row = self.conn.execute(
            "SELECT workstream_id FROM events WHERE project_id = ? AND source_provider = 'github' "
            "AND source_ref = ? AND workstream_id IS NOT NULL LIMIT 1",
            (project_id, target_ref),
        ).fetchone()
        if row:
            return row["workstream_id"]
        # Also allow correlation to a PR that closes/references the same number.
        row = self.conn.execute(
            "SELECT workstream_id FROM events WHERE project_id = ? AND type = 'commit' "
            "AND metadata LIKE ? AND workstream_id IS NOT NULL LIMIT 1",
            (project_id, f'%"issue_refs": [{issue_number}%'),
        ).fetchone()
        return row["workstream_id"] if row else None

    def find_workstream_by_branch(self, project_id: str, branch: str) -> Optional[str]:
        row = self.conn.execute(
            "SELECT workstream_id FROM events WHERE project_id = ? AND "
            "json_extract(metadata, '$.branch') = ? AND workstream_id IS NOT NULL LIMIT 1",
            (project_id, branch),
        ).fetchone()
        return row["workstream_id"] if row else None

    # -- sync state -----------------------------------------------------------------

    def set_state(self, project_id: str, key: str, value: Any) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO sync_state (project_id, key, value) VALUES (?,?,?) "
                "ON CONFLICT(project_id, key) DO UPDATE SET value = excluded.value",
                (project_id, key, json.dumps(value)),
            )

    def get_state(self, project_id: str, key: str, default: Any = None) -> Any:
        row = self.conn.execute(
            "SELECT value FROM sync_state WHERE project_id = ? AND key = ?",
            (project_id, key),
        ).fetchone()
        if not row:
            return default
        return json.loads(row["value"])

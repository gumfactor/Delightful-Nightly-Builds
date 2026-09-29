"""SQLite event ledger: append-oriented, deterministic IDs, rebuildable views."""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

from .redact import redact

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    project_id TEXT NOT NULL,
    type TEXT NOT NULL,
    actor_kind TEXT NOT NULL,
    actor_name TEXT NOT NULL,
    provider TEXT NOT NULL,
    summary TEXT NOT NULL,
    status TEXT NOT NULL,
    ref TEXT NOT NULL,
    url TEXT,
    keys TEXT NOT NULL,
    files TEXT NOT NULL,
    metadata TEXT NOT NULL,
    ingested_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_project_ts ON events(project_id, ts);
CREATE TABLE IF NOT EXISTS overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS state (
    project_id TEXT PRIMARY KEY,
    snapshot TEXT NOT NULL,
    observed_at TEXT NOT NULL
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_utc(iso: str) -> str:
    """Normalise any ISO-8601 timestamp to UTC 'YYYY-MM-DDTHH:MM:SSZ'."""
    parsed = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def event_id(provider: str, etype: str, ref: str) -> str:
    """Deterministic ID so re-ingesting the same source record never duplicates."""
    digest = hashlib.sha1(f"{provider}:{etype}:{ref}".encode()).hexdigest()
    return f"evt_{digest[:24]}"


def make_event(*, ts: str, project_id: str, etype: str, provider: str, ref: str, summary: str,
               actor_kind: str = "human", actor_name: str = "unknown", status: str = "completed",
               url: Optional[str] = None, keys: Optional[list[str]] = None,
               files: Optional[list[str]] = None, metadata: Optional[dict] = None) -> dict:
    """Build a normalised, redacted event dict."""
    return redact({
        "id": event_id(provider, etype, ref),
        "ts": to_utc(ts),
        "project_id": project_id,
        "type": etype,
        "actor_kind": actor_kind,
        "actor_name": actor_name,
        "provider": provider,
        "summary": summary.strip().splitlines()[0][:300] if summary.strip() else "(no summary)",
        "status": status,
        "ref": ref,
        "url": url,
        "keys": sorted(set(keys or [])),
        "files": sorted(set(files or [])),
        "metadata": metadata or {},
    })


class Ledger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path), timeout=30)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)
        self.conn.execute("INSERT OR IGNORE INTO meta VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Atomic write scope: all-or-nothing."""
        try:
            self.conn.execute("BEGIN IMMEDIATE")
            yield self.conn
            self.conn.commit()
        except BaseException:
            self.conn.rollback()
            raise

    def upsert(self, event: dict, replace: bool = False) -> str:
        """Insert an event. Returns 'inserted', 'unchanged' or 'updated'.

        Immutable source records are ignored on re-ingest; `replace=True` is for
        records that are legitimately revised (e.g. a per-session agent checkpoint).
        """
        row = self.conn.execute("SELECT summary, status, keys, files, metadata, ts FROM events WHERE id=?",
                                (event["id"],)).fetchone()
        values = (event["ts"], event["project_id"], event["type"], event["actor_kind"], event["actor_name"],
                  event["provider"], event["summary"], event["status"], event["ref"], event["url"],
                  json.dumps(event["keys"]), json.dumps(event["files"]),
                  json.dumps(event["metadata"], sort_keys=True), utc_now())
        if row is None:
            self.conn.execute("INSERT INTO events (ts, project_id, type, actor_kind, actor_name, provider, summary,"
                              " status, ref, url, keys, files, metadata, ingested_at, id)"
                              " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values + (event["id"],))
            return "inserted"
        if not replace:
            return "unchanged"
        same = (row["summary"] == event["summary"] and row["status"] == event["status"]
                and row["ts"] == event["ts"] and json.loads(row["keys"]) == event["keys"]
                and json.loads(row["files"]) == event["files"]
                and json.loads(row["metadata"]) == event["metadata"])
        if same:
            return "unchanged"
        self.conn.execute("UPDATE events SET ts=?, project_id=?, type=?, actor_kind=?, actor_name=?, provider=?,"
                          " summary=?, status=?, ref=?, url=?, keys=?, files=?, metadata=?, ingested_at=?"
                          " WHERE id=?", values + (event["id"],))
        return "updated"

    def ingest(self, events: list[dict], replace: bool = False) -> dict[str, int]:
        counts = {"inserted": 0, "unchanged": 0, "updated": 0}
        with self.transaction():
            for event in events:
                counts[self.upsert(event, replace=replace)] += 1
        return counts

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        event = dict(row)
        for field in ("keys", "files", "metadata"):
            event[field] = json.loads(event[field])
        return event

    def events(self, project_id: str, *, since: Optional[str] = None, etype: Optional[str] = None,
               provider: Optional[str] = None, actor_kind: Optional[str] = None) -> list[dict]:
        sql, args = "SELECT * FROM events WHERE project_id=?", [project_id]
        for column, value in (("type", etype), ("provider", provider), ("actor_kind", actor_kind)):
            if value:
                sql += f" AND {column}=?"
                args.append(value)
        if since:
            sql += " AND ts>=?"
            args.append(since)
        sql += " ORDER BY ts, id"
        return [self._decode(row) for row in self.conn.execute(sql, args)]

    def get_event(self, prefix: str) -> Optional[dict]:
        """Look up by event-id prefix, or by source ref (e.g. a commit SHA) of at least 7 characters."""
        rows = self.conn.execute("SELECT * FROM events WHERE substr(id, 1, ?)=?", (len(prefix), prefix)).fetchall()
        if not rows and len(prefix) >= 7:
            rows = self.conn.execute("SELECT * FROM events WHERE substr(ref, 1, ?)=?", (len(prefix), prefix)).fetchall()
        return self._decode(rows[0]) if len(rows) == 1 else None

    def count(self, project_id: str) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM events WHERE project_id=?", (project_id,)).fetchone()[0]

    def prune_children(self, ref_prefix: str, keep: list[str]) -> int:
        """Remove events whose ref starts with `ref_prefix` and whose id is not in `keep`."""
        with self.transaction():
            rows = self.conn.execute("SELECT id, ref FROM events WHERE substr(ref, 1, ?)=?",
                                     (len(ref_prefix), ref_prefix)).fetchall()
            stale = [row["id"] for row in rows if row["id"] not in keep]
            for stale_id in stale:
                self.conn.execute("DELETE FROM events WHERE id=?", (stale_id,))
        return len(stale)

    def add_override(self, project_id: str, kind: str, payload: dict) -> None:
        with self.transaction():
            self.conn.execute("INSERT INTO overrides (project_id, kind, payload, created_at) VALUES (?,?,?,?)",
                              (project_id, kind, json.dumps(payload), utc_now()))

    def overrides(self, project_id: str) -> list[dict]:
        rows = self.conn.execute("SELECT kind, payload FROM overrides WHERE project_id=? ORDER BY id",
                                 (project_id,)).fetchall()
        return [{"kind": row["kind"], **json.loads(row["payload"])} for row in rows]

    def save_state(self, project_id: str, snapshot: dict) -> None:
        with self.transaction():
            self.conn.execute("INSERT OR REPLACE INTO state VALUES (?,?,?)",
                              (project_id, json.dumps(redact(snapshot)), utc_now()))

    def load_state(self, project_id: str) -> Optional[dict]:
        row = self.conn.execute("SELECT snapshot, observed_at FROM state WHERE project_id=?",
                                (project_id,)).fetchone()
        return {**json.loads(row["snapshot"]), "observed_at": row["observed_at"]} if row else None

    def purge(self, project_id: str) -> int:
        """Delete everything recorded for a project. Derived views rebuild from `sync`."""
        with self.transaction():
            deleted = self.conn.execute("DELETE FROM events WHERE project_id=?", (project_id,)).rowcount
            self.conn.execute("DELETE FROM overrides WHERE project_id=?", (project_id,))
            self.conn.execute("DELETE FROM state WHERE project_id=?", (project_id,))
        return deleted

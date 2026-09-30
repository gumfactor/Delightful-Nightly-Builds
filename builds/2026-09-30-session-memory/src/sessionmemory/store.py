"""SQLite + FTS5 store. Source transcripts are never modified."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import Message, Session

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY, source TEXT NOT NULL, project TEXT NOT NULL, title TEXT NOT NULL,
  started TEXT, ended TEXT, msg_count INTEGER, files_json TEXT, branch TEXT, path TEXT,
  content_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  idx INTEGER NOT NULL, role TEXT NOT NULL, ts TEXT, text TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, idx);
CREATE VIRTUAL TABLE IF NOT EXISTS msg_fts USING fts5(text, tokenize='porter unicode61');
CREATE TABLE IF NOT EXISTS summaries (
  session_id TEXT PRIMARY KEY REFERENCES sessions(id) ON DELETE CASCADE,
  content_hash TEXT NOT NULL, kind TEXT NOT NULL, json TEXT NOT NULL, created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS briefs (
  project TEXT NOT NULL, kind TEXT NOT NULL, markdown TEXT NOT NULL, created TEXT NOT NULL,
  PRIMARY KEY (project, kind)
);
"""

HIGHLIGHT_START, HIGHLIGHT_END = "\x02", "\x03"


def session_hash(session: Session) -> str:
    digest = hashlib.sha256()
    digest.update(session.title.encode())
    for message in session.messages:
        digest.update(f"{message.role}\x00{message.ts}\x00{message.text}\x01".encode())
    return digest.hexdigest()


def fts_query(user_query: str) -> str | None:
    """Turn free text into a safe FTS5 query: quoted terms ANDed, last term prefix-matched."""
    terms = re.findall(r"[\w'-]+", user_query, flags=re.UNICODE)
    terms = [term.strip("'-") for term in terms if term.strip("'-")]
    if not terms:
        return None
    quoted = [f'"{term}"' for term in terms]
    quoted[-1] += "*"
    return " ".join(quoted)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class Store:
    def __init__(self, db_path: str | Path = "sessionmemory.db") -> None:
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    # ---- ingest -------------------------------------------------------
    def upsert_session(self, session: Session) -> str:
        """Returns 'added', 'updated' or 'unchanged'."""
        digest = session_hash(session)
        row = self.conn.execute("SELECT content_hash FROM sessions WHERE id=?", (session.id,)).fetchone()
        if row and row["content_hash"] == digest:
            return "unchanged"
        with self.conn:
            if row:
                self._delete_messages(session.id)
            self.conn.execute(
                "INSERT OR REPLACE INTO sessions VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (session.id, session.source, session.project, session.title, session.started, session.ended,
                 len(session.messages), json.dumps(session.files), session.branch, session.path, digest),
            )
            for idx, message in enumerate(session.messages):
                cursor = self.conn.execute(
                    "INSERT INTO messages(session_id, idx, role, ts, text) VALUES (?,?,?,?,?)",
                    (session.id, idx, message.role, message.ts, message.text),
                )
                self.conn.execute("INSERT INTO msg_fts(rowid, text) VALUES (?,?)", (cursor.lastrowid, message.text))
        return "updated" if row else "added"

    def _delete_messages(self, session_id: str) -> None:
        ids = [r["id"] for r in self.conn.execute("SELECT id FROM messages WHERE session_id=?", (session_id,))]
        self.conn.executemany("DELETE FROM msg_fts WHERE rowid=?", [(i,) for i in ids])
        self.conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))

    def ingest(self, sessions: Any) -> dict[str, int]:
        counts = {"added": 0, "updated": 0, "unchanged": 0}
        for session in sessions:
            counts[self.upsert_session(session)] += 1
        return counts

    # ---- queries ------------------------------------------------------
    def projects(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT project, COUNT(*) AS sessions, MAX(ended) AS last_active, SUM(msg_count) AS messages "
            "FROM sessions GROUP BY project ORDER BY last_active DESC"
        )
        return [dict(r) for r in rows]

    def sessions(self, project: str | None = None, source: str | None = None, limit: int = 200) -> list[dict[str, Any]]:
        sql, args = "SELECT * FROM sessions WHERE 1=1", []
        if project:
            sql += " AND project=?"
            args.append(project)
        if source:
            sql += " AND source=?"
            args.append(source)
        sql += " ORDER BY ended DESC LIMIT ?"
        args.append(limit)
        return [self._session_row(r) for r in self.conn.execute(sql, args)]

    @staticmethod
    def _session_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["files"] = json.loads(data.pop("files_json") or "[]")
        data.pop("content_hash", None)
        return data

    def session(self, session_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            return None
        data = self._session_row(row)
        data["messages"] = [dict(r) for r in self.conn.execute(
            "SELECT role, ts, text FROM messages WHERE session_id=? ORDER BY idx", (session_id,))]
        return data

    def session_object(self, session_id: str) -> Session | None:
        data = self.session(session_id)
        if not data:
            return None
        return Session(
            id=data["id"], source=data["source"], project=data["project"], title=data["title"],
            started=data["started"] or "", ended=data["ended"] or "", branch=data["branch"] or "",
            path=data["path"] or "", files=data["files"],
            messages=[Message(m["role"], m["text"], m["ts"] or "") for m in data["messages"]],
        )

    def content_hash(self, session_id: str) -> str | None:
        row = self.conn.execute("SELECT content_hash FROM sessions WHERE id=?", (session_id,)).fetchone()
        return row["content_hash"] if row else None

    def search(self, query: str, project: str | None = None, source: str | None = None,
               limit: int = 30) -> list[dict[str, Any]]:
        match = fts_query(query)
        if not match:
            return []
        sql = (
            "SELECT s.id AS session_id, s.title, s.project, s.source, s.ended, m.idx, m.role, "
            f"snippet(msg_fts, 0, '{HIGHLIGHT_START}', '{HIGHLIGHT_END}', '…', 28) AS snippet "
            "FROM msg_fts JOIN messages m ON m.id = msg_fts.rowid JOIN sessions s ON s.id = m.session_id "
            "WHERE msg_fts MATCH ?"
        )
        args: list[Any] = [match]
        if project:
            sql += " AND s.project=?"
            args.append(project)
        if source:
            sql += " AND s.source=?"
            args.append(source)
        sql += " ORDER BY bm25(msg_fts) LIMIT ?"
        args.append(limit)
        return [dict(r) for r in self.conn.execute(sql, args)]

    # ---- summaries & briefs -------------------------------------------
    def save_summary(self, session_id: str, kind: str, payload: dict[str, Any]) -> None:
        digest = self.content_hash(session_id)
        if digest is None:
            raise KeyError(session_id)
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO summaries VALUES (?,?,?,?,?)",
                (session_id, digest, kind, json.dumps(payload), _now()),
            )

    def get_summary(self, session_id: str, kind: str | None = None) -> dict[str, Any] | None:
        """Cached summary if it still matches the session content (stale ones are ignored)."""
        row = self.conn.execute(
            "SELECT s.kind, s.json, s.content_hash AS h, x.content_hash AS current "
            "FROM summaries s JOIN sessions x ON x.id = s.session_id WHERE s.session_id=?", (session_id,)
        ).fetchone()
        if not row or row["h"] != row["current"] or (kind and row["kind"] != kind):
            return None
        return {"kind": row["kind"], **json.loads(row["json"])}

    def save_brief(self, project: str, kind: str, markdown: str) -> None:
        with self.conn:
            self.conn.execute("INSERT OR REPLACE INTO briefs VALUES (?,?,?,?)", (project, kind, markdown, _now()))

    def get_brief(self, project: str, kind: str) -> str | None:
        row = self.conn.execute("SELECT markdown FROM briefs WHERE project=? AND kind=?", (project, kind)).fetchone()
        return row["markdown"] if row else None

    def stats(self) -> dict[str, Any]:
        row = self.conn.execute("SELECT COUNT(*) AS sessions, COALESCE(SUM(msg_count),0) AS messages FROM sessions").fetchone()
        by_source = {r["source"]: r["n"] for r in self.conn.execute("SELECT source, COUNT(*) AS n FROM sessions GROUP BY source")}
        return {"sessions": row["sessions"], "messages": row["messages"], "by_source": by_source}

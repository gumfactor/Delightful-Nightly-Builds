"""SQLite + FTS5 vault: incremental indexing and search."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from .parser import parse_session

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions(
  id TEXT PRIMARY KEY, project TEXT, cwd TEXT, branch TEXT, started TEXT, ended TEXT,
  msg_count INTEGER, first_prompt TEXT, hint_title TEXT, source_path TEXT UNIQUE,
  size INTEGER, mtime REAL, summary_json TEXT, summarized_at TEXT);
CREATE TABLE IF NOT EXISTS messages(
  id INTEGER PRIMARY KEY, session_id TEXT, idx INTEGER, role TEXT, ts TEXT, text TEXT);
CREATE INDEX IF NOT EXISTS messages_session ON messages(session_id, idx);
CREATE TABLE IF NOT EXISTS session_files(session_id TEXT, path TEXT, touches INTEGER);
CREATE INDEX IF NOT EXISTS files_session ON session_files(session_id);
CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
  text, content='messages', content_rowid='id', tokenize='porter unicode61');
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    if str(db_path) != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _delete_session(conn: sqlite3.Connection, session_id: str) -> None:
    conn.execute(
        "INSERT INTO messages_fts(messages_fts, rowid, text) "
        "SELECT 'delete', id, text FROM messages WHERE session_id=?", (session_id,))
    conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
    conn.execute("DELETE FROM session_files WHERE session_id=?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))


def index_directory(conn: sqlite3.Connection, root: str | Path) -> dict[str, int]:
    """Index all *.jsonl under root. Unchanged files are skipped; vanished ones removed."""
    root = Path(root)
    stats = {"indexed": 0, "skipped": 0, "removed": 0, "empty": 0}
    seen: set[str] = set()
    for path in sorted(root.glob("*/*.jsonl")):
        source = str(path)
        seen.add(source)
        info = path.stat()
        row = conn.execute(
            "SELECT id, size, mtime FROM sessions WHERE source_path=?", (source,)).fetchone()
        if row and row["size"] == info.st_size and row["mtime"] == info.st_mtime:
            stats["skipped"] += 1
            continue
        parsed = parse_session(path)
        if row:
            summary = conn.execute(
                "SELECT summary_json, summarized_at FROM sessions WHERE id=?", (row["id"],)
            ).fetchone()
            _delete_session(conn, row["id"])
        else:
            summary = None
        if parsed is None:
            stats["empty"] += 1
            continue
        # a session id can appear in two files (resumed sessions); newest file wins
        conn.execute("DELETE FROM sessions WHERE id=? AND source_path<>?", (parsed.session_id, source))
        first_user = next((m.text for m in parsed.messages if m.role == "user"), "")
        conn.execute(
            "INSERT OR REPLACE INTO sessions VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (parsed.session_id, parsed.project, parsed.cwd, parsed.branch, parsed.started,
             parsed.ended, len(parsed.messages), first_user[:300], parsed.hint_title, source,
             info.st_size, info.st_mtime,
             summary["summary_json"] if summary else None,
             summary["summarized_at"] if summary else None))
        for msg in parsed.messages:
            cur = conn.execute(
                "INSERT INTO messages(session_id, idx, role, ts, text) VALUES(?,?,?,?,?)",
                (parsed.session_id, msg.idx, msg.role, msg.ts, msg.text))
            conn.execute("INSERT INTO messages_fts(rowid, text) VALUES(?,?)", (cur.lastrowid, msg.text))
        conn.executemany(
            "INSERT INTO session_files VALUES(?,?,?)",
            [(parsed.session_id, p, n) for p, n in parsed.files.items()])
        stats["indexed"] += 1
    for row in conn.execute("SELECT id, source_path FROM sessions").fetchall():
        if row["source_path"] not in seen:
            _delete_session(conn, row["id"])
            stats["removed"] += 1
    conn.commit()
    return stats


def fts_query(raw: str) -> str:
    """Turn arbitrary user input into a safe FTS5 query (AND of stemmed-or-prefix terms)."""
    terms = re.findall(r"[\w\-\.]+", raw, flags=re.UNICODE)
    terms = [t.strip("-.") for t in terms]
    # exact form is porter-stemmed by FTS5 (merging~merged); the prefix form covers partial words
    quoted = ['"%s"' % t.replace('"', '""') for t in terms if t]
    return " AND ".join(f"({q} OR {q}*)" for q in quoted)


def search(conn: sqlite3.Connection, query: str, project: str | None = None,
           limit: int = 30) -> list[dict]:
    match = fts_query(query)
    if not match:
        return []
    sql = ("SELECT m.session_id, m.idx, m.role, m.ts, s.project, s.hint_title, s.summary_json, "
           "snippet(messages_fts, 0, '[[', ']]', '…', 24) AS snippet "
           "FROM messages_fts JOIN messages m ON m.id = messages_fts.rowid "
           "JOIN sessions s ON s.id = m.session_id WHERE messages_fts MATCH ?")
    args: list = [match]
    if project:
        sql += " AND s.project = ?"
        args.append(project)
    sql += " ORDER BY bm25(messages_fts) LIMIT ?"
    args.append(limit)
    results = []
    for row in conn.execute(sql, args):
        item = dict(row)
        summary = item.pop("summary_json")
        item["title"] = (json.loads(summary).get("title") if summary else "") or item["hint_title"]
        results.append(item)
    return results


def list_projects(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT project, COUNT(*) AS sessions, SUM(msg_count) AS messages, MAX(ended) AS last_active, "
        "SUM(summary_json IS NOT NULL) AS summarized FROM sessions GROUP BY project "
        "ORDER BY last_active DESC")
    return [dict(r) for r in rows]


def list_sessions(conn: sqlite3.Connection, project: str | None = None) -> list[dict]:
    sql = ("SELECT id, project, branch, started, ended, msg_count, first_prompt, hint_title, "
           "summary_json FROM sessions")
    args: list = []
    if project:
        sql += " WHERE project=?"
        args.append(project)
    sql += " ORDER BY ended DESC"
    out = []
    for row in conn.execute(sql, args):
        item = dict(row)
        summary = item.pop("summary_json")
        item["summary"] = json.loads(summary) if summary else None
        item["title"] = (item["summary"] or {}).get("title") or item["hint_title"] or item["first_prompt"][:80]
        out.append(item)
    return out


def get_session(conn: sqlite3.Connection, session_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    if not row:
        return None
    item = dict(row)
    item["summary"] = json.loads(item.pop("summary_json")) if item["summary_json"] else None
    item["messages"] = [dict(r) for r in conn.execute(
        "SELECT idx, role, ts, text FROM messages WHERE session_id=? ORDER BY idx", (session_id,))]
    item["files"] = [dict(r) for r in conn.execute(
        "SELECT path, touches FROM session_files WHERE session_id=? ORDER BY touches DESC", (session_id,))]
    return item


def save_summary(conn: sqlite3.Connection, session_id: str, summary: dict, when: str) -> None:
    conn.execute("UPDATE sessions SET summary_json=?, summarized_at=? WHERE id=?",
                 (json.dumps(summary), when, session_id))
    conn.commit()

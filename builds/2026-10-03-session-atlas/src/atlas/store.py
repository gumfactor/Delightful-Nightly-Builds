"""SQLite index with incremental re-indexing and prompt search."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from .parser import Session, finalize_cost, parse_session_file, project_label

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, size INTEGER, mtime REAL);
CREATE TABLE IF NOT EXISTS sessions (
    source TEXT PRIMARY KEY, id TEXT, project TEXT, project_path TEXT, branch TEXT,
    start TEXT, end TEXT, active_seconds INTEGER, prompts INTEGER, assistant_msgs INTEGER,
    sidechain_msgs INTEGER, tool_errors INTEGER, input_tokens INTEGER, output_tokens INTEGER,
    cache_write_tokens INTEGER, cache_read_tokens INTEGER, cost_usd REAL, unpriced INTEGER,
    models_json TEXT, tools_json TEXT, files_json TEXT, title TEXT,
    first_prompt TEXT, last_prompt TEXT, last_assistant TEXT, summary TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS prompts (source TEXT, ts TEXT, text TEXT);
CREATE INDEX IF NOT EXISTS prompts_source ON prompts(source);
"""


class Store:
    def __init__(self, db_path: str | Path):
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.fts = self._init_fts()

    def _init_fts(self) -> bool:
        try:
            self.conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS prompts_fts USING fts5(text, source UNINDEXED, ts UNINDEXED)"
            )
            return True
        except sqlite3.OperationalError:
            return False

    def close(self) -> None:
        self.conn.close()

    # ---- indexing -------------------------------------------------------
    def index_directory(
        self, root: str | Path, prices: dict[str, dict[str, float]], idle_gap: int = 300
    ) -> dict[str, int]:
        """Index every *.jsonl under root. Returns counts: parsed, skipped, removed, empty."""
        root_path = Path(root)
        counts = {"parsed": 0, "skipped": 0, "removed": 0, "empty": 0}
        present: set[str] = set()
        for path in sorted(root_path.rglob("*.jsonl")):
            try:
                stat = path.stat()
            except OSError:
                continue
            key = str(path)
            present.add(key)
            row = self.conn.execute("SELECT size, mtime FROM files WHERE path=?", (key,)).fetchone()
            if row and row["size"] == stat.st_size and row["mtime"] == stat.st_mtime:
                counts["skipped"] += 1
                continue
            session = parse_session_file(path, idle_gap)
            self._forget(key)
            if session is None:
                counts["empty"] += 1
            else:
                if not session.project:
                    session.project = _decode_dir_name(path.parent.name)
                self._save(finalize_cost(session, prices))
                counts["parsed"] += 1
            self.conn.execute(
                "INSERT OR REPLACE INTO files(path,size,mtime) VALUES (?,?,?)",
                (key, stat.st_size, stat.st_mtime),
            )
        stale = [r["path"] for r in self.conn.execute("SELECT path FROM files") if r["path"] not in present]
        # Only prune files that lived under this root.
        for key in stale:
            if _is_within(key, root_path):
                self._forget(key)
                self.conn.execute("DELETE FROM files WHERE path=?", (key,))
                counts["removed"] += 1
        self.conn.commit()
        return counts

    def reprice(self, prices: dict[str, dict[str, float]]) -> None:
        """Recompute costs for stored sessions (price table changed)."""
        from .pricing import estimate_cost

        for row in self.conn.execute("SELECT source, models_json FROM sessions").fetchall():
            usage = json.loads(row["models_json"])
            cost, unpriced = estimate_cost(usage, prices)
            self.conn.execute(
                "UPDATE sessions SET cost_usd=?, unpriced=? WHERE source=?", (cost, int(unpriced), row["source"])
            )
        self.conn.commit()

    def _forget(self, source: str) -> None:
        self.conn.execute("DELETE FROM sessions WHERE source=?", (source,))
        self.conn.execute("DELETE FROM prompts WHERE source=?", (source,))
        if self.fts:
            self.conn.execute("DELETE FROM prompts_fts WHERE source=?", (source,))

    def _save(self, s: Session) -> None:
        prompts = s.prompts
        self.conn.execute(
            "INSERT INTO sessions(source,id,project,project_path,branch,start,end,active_seconds,prompts,"
            "assistant_msgs,sidechain_msgs,tool_errors,input_tokens,output_tokens,cache_write_tokens,"
            "cache_read_tokens,cost_usd,unpriced,models_json,tools_json,files_json,title,first_prompt,"
            "last_prompt,last_assistant) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                s.source, s.id, project_label(s.project), s.project, s.branch, s.start, s.end,
                s.active_seconds, len(prompts), s.assistant_msgs, s.sidechain_msgs, s.tool_errors,
                s.total("input"), s.total("output"), s.total("cache_write"), s.total("cache_read"),
                s.cost_usd, int(s.unpriced), json.dumps(s.usage_by_model), json.dumps(dict(s.tools)),
                json.dumps(dict(s.files)), s.title,
                prompts[0][1] if prompts else "", prompts[-1][1] if prompts else "", s.last_assistant,
            ),
        )
        self.conn.executemany(
            "INSERT INTO prompts(source,ts,text) VALUES (?,?,?)", [(s.source, ts, text) for ts, text in prompts]
        )
        if self.fts:
            self.conn.executemany(
                "INSERT INTO prompts_fts(text,source,ts) VALUES (?,?,?)",
                [(text, s.source, ts) for ts, text in prompts],
            )

    # ---- queries --------------------------------------------------------
    def sessions(self, since: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM sessions"
        args: tuple[Any, ...] = ()
        if since:
            sql += " WHERE start >= ?"
            args = (since,)
        sql += " ORDER BY start DESC"
        return [_row_to_dict(row) for row in self.conn.execute(sql, args)]

    def search(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        """Search prompt text. Uses FTS5 when available, otherwise a LIKE scan."""
        query = query.strip()
        if not query:
            return []
        rows = None
        if self.fts:
            match = _fts_query(query)
            if match:
                try:
                    rows = self.conn.execute(
                        "SELECT f.source, f.ts, snippet(prompts_fts, 0, '[', ']', '…', 12) AS snip "
                        "FROM prompts_fts f WHERE prompts_fts MATCH ? ORDER BY rank LIMIT ?",
                        (match, limit),
                    ).fetchall()
                except sqlite3.OperationalError:
                    rows = None
        if rows is None:
            terms = [t for t in re.split(r"\s+", query) if t]
            clause = " AND ".join("text LIKE ? ESCAPE '\\'" for _ in terms)
            args = [f"%{_like_escape(t)}%" for t in terms]
            rows = self.conn.execute(
                f"SELECT source, ts, text AS snip FROM prompts WHERE {clause} ORDER BY ts DESC LIMIT ?",
                (*args, limit),
            ).fetchall()
        results = []
        for row in rows:
            meta = self.conn.execute(
                "SELECT id, project, start FROM sessions WHERE source=?", (row["source"],)
            ).fetchone()
            if meta is None:
                continue
            results.append(
                {"session": meta["id"], "project": meta["project"], "ts": row["ts"], "snippet": row["snip"][:300]}
            )
        return results

    def cached_summary(self, source: str) -> str:
        row = self.conn.execute("SELECT summary FROM sessions WHERE source=?", (source,)).fetchone()
        return row["summary"] if row else ""

    def save_summary(self, source: str, summary: str) -> None:
        self.conn.execute("UPDATE sessions SET summary=? WHERE source=?", (summary, source))
        self.conn.commit()


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    data["models"] = json.loads(data.pop("models_json") or "{}")
    data["tools"] = json.loads(data.pop("tools_json") or "{}")
    data["files"] = json.loads(data.pop("files_json") or "{}")
    data["unpriced"] = bool(data["unpriced"])
    return data


def _fts_query(text: str) -> str:
    words = re.findall(r"[\w]+", text)
    return " ".join(f'"{w}"' for w in words)


def _like_escape(term: str) -> str:
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _decode_dir_name(name: str) -> str:
    """Claude Code names project dirs after the cwd with '/' replaced by '-'."""
    return name.replace("-", "/") if name.startswith("-") else name


def _is_within(path: str, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def prompts_by_source(store: "Store", limit_per_session: int = 40, clip: int = 300) -> dict[str, list[dict[str, str]]]:
    """Prompt text per session, clipped, for the HTML explorer's client-side search."""
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in store.conn.execute("SELECT source, ts, text FROM prompts ORDER BY ts"):
        bucket = grouped.setdefault(row["source"], [])
        if len(bucket) < limit_per_session:
            bucket.append({"ts": row["ts"], "text": row["text"][:clip]})
    return grouped

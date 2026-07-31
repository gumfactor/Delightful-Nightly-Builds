import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional


SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT UNIQUE NOT NULL,
    slug         TEXT UNIQUE NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    type         TEXT NOT NULL DEFAULT 'code',
    github_repos TEXT NOT NULL DEFAULT '[]',
    status       TEXT NOT NULL DEFAULT 'active',
    color        TEXT NOT NULL DEFAULT '#4a9eff',
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id),
    source      TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    title       TEXT NOT NULL,
    detail      TEXT NOT NULL DEFAULT '',
    occurred_at TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    UNIQUE(project_id, source, event_type, title)
);

CREATE INDEX IF NOT EXISTS idx_activity_project
    ON activity_log(project_id, occurred_at);
"""


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = _connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def add_project(
    db_path: str,
    name: str,
    description: str,
    proj_type: str,
    github_repos: List[str],
    color: str = "#4a9eff",
    now: Optional[str] = None,
) -> int:
    slug = slugify(name)
    ts = now or datetime.now(timezone.utc).isoformat()
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            """INSERT INTO projects
               (name, slug, description, type, github_repos, status, color, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?)""",
            (name, slug, description, proj_type, json.dumps(github_repos), color, ts, ts),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_project(db_path: str, slug: str) -> Optional[dict]:
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM projects WHERE slug = ?", (slug,)
        ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["github_repos"] = json.loads(result["github_repos"])
        return result
    finally:
        conn.close()


def list_projects(db_path: str, status: str = "active") -> List[dict]:
    conn = _connect(db_path)
    try:
        if status == "all":
            rows = conn.execute(
                "SELECT * FROM projects ORDER BY updated_at DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM projects WHERE status = ? ORDER BY updated_at DESC",
                (status,),
            ).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d["github_repos"] = json.loads(d["github_repos"])
            result.append(d)
        return result
    finally:
        conn.close()


def update_project_status(db_path: str, slug: str, status: str) -> bool:
    ts = datetime.now(timezone.utc).isoformat()
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "UPDATE projects SET status = ?, updated_at = ? WHERE slug = ?",
            (status, ts, slug),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def log_activity(
    db_path: str,
    project_id: int,
    source: str,
    event_type: str,
    title: str,
    detail: str = "",
    occurred_at: Optional[str] = None,
) -> Optional[int]:
    ts = datetime.now(timezone.utc).isoformat()
    occurred = occurred_at or ts
    conn = _connect(db_path)
    try:
        try:
            cur = conn.execute(
                """INSERT INTO activity_log
                   (project_id, source, event_type, title, detail, occurred_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (project_id, source, event_type, title, detail, occurred, ts),
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None
    finally:
        conn.close()


def get_recent_activity(
    db_path: str, project_id: int, days: int = 30
) -> List[dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """SELECT * FROM activity_log
               WHERE project_id = ? AND occurred_at >= ?
               ORDER BY occurred_at DESC""",
            (project_id, cutoff),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all_recent_activity(db_path: str, days: int = 30) -> List[dict]:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """SELECT al.*, p.name AS project_name, p.slug AS project_slug,
                      p.color AS project_color
               FROM activity_log al
               JOIN projects p ON al.project_id = p.id
               WHERE al.occurred_at >= ?
               ORDER BY al.occurred_at DESC""",
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_last_activity_date(db_path: str, project_id: int) -> Optional[str]:
    conn = _connect(db_path)
    try:
        row = conn.execute(
            """SELECT occurred_at FROM activity_log
               WHERE project_id = ?
               ORDER BY occurred_at DESC LIMIT 1""",
            (project_id,),
        ).fetchone()
        return row["occurred_at"] if row else None
    finally:
        conn.close()

"""SQLite persistence for Panel Prep projects and their submitted versions.

A "project" is a named, ongoing proposal (e.g. "R01 Empathy Renewal"). Every
`submit` appends a new, permanently-kept version row for that project —
nothing is ever overwritten — so score trend across revisions is a real,
queryable history rather than a single snapshot.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    version_num INTEGER NOT NULL,
    submitted_at TEXT NOT NULL,
    source_path TEXT,
    sections_json TEXT NOT NULL,
    checklist_json TEXT NOT NULL,
    review_json TEXT NOT NULL,
    checklist_pass_rate REAL NOT NULL,
    overall_impact REAL NOT NULL,
    ai_used INTEGER NOT NULL,
    UNIQUE(project_id, version_num)
);
"""


class ProjectNotFoundError(Exception):
    pass


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_or_create_project(conn: sqlite3.Connection, name: str) -> int:
    row = conn.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()
    if row:
        return row["id"]
    cursor = conn.execute(
        "INSERT INTO projects (name, created_at) VALUES (?, ?)",
        (name, _now()),
    )
    conn.commit()
    return cursor.lastrowid


def get_project_id(conn: sqlite3.Connection, name: str) -> int:
    row = conn.execute("SELECT id FROM projects WHERE name = ?", (name,)).fetchone()
    if not row:
        raise ProjectNotFoundError(f"No project named {name!r}")
    return row["id"]


def _next_version_num(conn: sqlite3.Connection, project_id: int) -> int:
    row = conn.execute(
        "SELECT MAX(version_num) AS max_version FROM versions WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    return (row["max_version"] or 0) + 1


def insert_version(
    conn: sqlite3.Connection,
    project_name: str,
    sections: dict[str, str],
    checklist_result: dict,
    review: dict,
    source_path: str | None = None,
) -> dict:
    project_id = get_or_create_project(conn, project_name)
    version_num = _next_version_num(conn, project_id)

    conn.execute(
        """INSERT INTO versions
           (project_id, version_num, submitted_at, source_path, sections_json,
            checklist_json, review_json, checklist_pass_rate, overall_impact, ai_used)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            project_id,
            version_num,
            _now(),
            source_path,
            json.dumps(sections),
            json.dumps(checklist_result),
            json.dumps(review),
            checklist_result["overall_pass_rate"],
            review["overall_impact"],
            1 if review["ai_used"] else 0,
        ),
    )
    conn.commit()
    return {"project_id": project_id, "version_num": version_num}


def _row_to_version(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "version_num": row["version_num"],
        "submitted_at": row["submitted_at"],
        "source_path": row["source_path"],
        "sections": json.loads(row["sections_json"]),
        "checklist": json.loads(row["checklist_json"]),
        "review": json.loads(row["review_json"]),
        "checklist_pass_rate": row["checklist_pass_rate"],
        "overall_impact": row["overall_impact"],
        "ai_used": bool(row["ai_used"]),
    }


def get_history(conn: sqlite3.Connection, project_name: str) -> list[dict]:
    project_id = get_project_id(conn, project_name)
    rows = conn.execute(
        "SELECT * FROM versions WHERE project_id = ? ORDER BY version_num ASC",
        (project_id,),
    ).fetchall()
    return [_row_to_version(row) for row in rows]


def get_latest(conn: sqlite3.Connection, project_name: str) -> dict | None:
    history = get_history(conn, project_name)
    return history[-1] if history else None


def list_projects(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """SELECT p.name AS name, p.created_at AS created_at,
                  COUNT(v.id) AS version_count,
                  MAX(v.version_num) AS latest_version_num
           FROM projects p
           LEFT JOIN versions v ON v.project_id = p.id
           GROUP BY p.id
           ORDER BY p.name ASC"""
    ).fetchall()

    results = []
    for row in rows:
        latest = None
        if row["latest_version_num"]:
            latest_row = conn.execute(
                """SELECT v.* FROM versions v
                   JOIN projects p ON p.id = v.project_id
                   WHERE p.name = ? AND v.version_num = ?""",
                (row["name"], row["latest_version_num"]),
            ).fetchone()
            latest = _row_to_version(latest_row)
        results.append({
            "name": row["name"],
            "created_at": row["created_at"],
            "version_count": row["version_count"],
            "latest": latest,
        })
    return results

"""SQLite storage for GrantScope: schema, dedupe-by-project_num upsert, and query helpers."""

import sqlite3
from datetime import date
from typing import Any, Dict, List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    project_num TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    pi_name TEXT,
    org_name TEXT,
    org_city TEXT,
    org_state TEXT,
    ic_admin TEXT,
    activity_code TEXT,
    award_amount INTEGER,
    fiscal_year INTEGER,
    project_start TEXT,
    project_end TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS briefings (
    topic TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    source TEXT NOT NULL
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def _today() -> str:
    return date.today().isoformat()


def upsert_project(conn: sqlite3.Connection, project: Dict[str, Any], today: Optional[str] = None) -> None:
    """Insert a project, or update last_seen (and refresh other fields) if it already exists."""
    today = today or _today()
    existing = conn.execute(
        "SELECT first_seen FROM projects WHERE project_num = ?", (project["project_num"],)
    ).fetchone()

    if existing is None:
        conn.execute(
            """
            INSERT INTO projects (
                project_num, topic, title, abstract, pi_name, org_name, org_city, org_state,
                ic_admin, activity_code, award_amount, fiscal_year, project_start, project_end,
                first_seen, last_seen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project["project_num"],
                project["topic"],
                project["title"],
                project.get("abstract", ""),
                project.get("pi_name"),
                project.get("org_name"),
                project.get("org_city"),
                project.get("org_state"),
                project.get("ic_admin"),
                project.get("activity_code"),
                project.get("award_amount"),
                project.get("fiscal_year"),
                project.get("project_start"),
                project.get("project_end"),
                today,
                today,
            ),
        )
    else:
        conn.execute(
            """
            UPDATE projects SET
                topic = ?, title = ?, abstract = ?, pi_name = ?, org_name = ?, org_city = ?,
                org_state = ?, ic_admin = ?, activity_code = ?, award_amount = ?, fiscal_year = ?,
                project_start = ?, project_end = ?, last_seen = ?
            WHERE project_num = ?
            """,
            (
                project["topic"],
                project["title"],
                project.get("abstract", ""),
                project.get("pi_name"),
                project.get("org_name"),
                project.get("org_city"),
                project.get("org_state"),
                project.get("ic_admin"),
                project.get("activity_code"),
                project.get("award_amount"),
                project.get("fiscal_year"),
                project.get("project_start"),
                project.get("project_end"),
                today,
                project["project_num"],
            ),
        )
    conn.commit()


def upsert_projects(conn: sqlite3.Connection, projects: List[Dict[str, Any]], today: Optional[str] = None) -> int:
    """Upsert many projects; returns the count processed."""
    today = today or _today()
    for project in projects:
        upsert_project(conn, project, today=today)
    return len(projects)


def all_projects(conn: sqlite3.Connection, topic: Optional[str] = None) -> List[sqlite3.Row]:
    if topic:
        return conn.execute(
            "SELECT * FROM projects WHERE topic = ? ORDER BY fiscal_year DESC, award_amount DESC", (topic,)
        ).fetchall()
    return conn.execute("SELECT * FROM projects ORDER BY fiscal_year DESC, award_amount DESC").fetchall()


def distinct_topics(conn: sqlite3.Connection) -> List[str]:
    rows = conn.execute("SELECT DISTINCT topic FROM projects ORDER BY topic").fetchall()
    return [row["topic"] for row in rows]


def search_projects(conn: sqlite3.Connection, query: str) -> List[sqlite3.Row]:
    like = f"%{query}%"
    return conn.execute(
        """
        SELECT * FROM projects
        WHERE title LIKE ? OR abstract LIKE ? OR org_name LIKE ? OR pi_name LIKE ?
        ORDER BY fiscal_year DESC
        """,
        (like, like, like, like),
    ).fetchall()


def project_count(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS n FROM projects").fetchone()
    return row["n"]


def save_briefing(conn: sqlite3.Connection, topic: str, text: str, source: str, generated_at: Optional[str] = None) -> None:
    generated_at = generated_at or _today()
    conn.execute(
        """
        INSERT INTO briefings (topic, text, generated_at, source) VALUES (?, ?, ?, ?)
        ON CONFLICT(topic) DO UPDATE SET text = excluded.text, generated_at = excluded.generated_at, source = excluded.source
        """,
        (topic, text, generated_at, source),
    )
    conn.commit()


def get_briefing(conn: sqlite3.Connection, topic: str) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM briefings WHERE topic = ?", (topic,)).fetchone()


def all_briefings(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute("SELECT * FROM briefings ORDER BY topic").fetchall()

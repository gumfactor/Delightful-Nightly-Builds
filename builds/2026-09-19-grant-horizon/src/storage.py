"""SQLite persistence for Grant Horizon.

One table, `projects`, primary-keyed on (topic, project_num) so re-running
`sync` upserts instead of duplicating rows.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from reporter_client import Project

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    topic TEXT NOT NULL,
    project_num TEXT NOT NULL,
    core_project_num TEXT NOT NULL,
    title TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    award_amount REAL NOT NULL,
    org_name TEXT NOT NULL,
    org_city TEXT NOT NULL,
    org_state TEXT NOT NULL,
    org_country TEXT NOT NULL,
    pi_names TEXT NOT NULL,
    agency_ic TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    first_seen TEXT NOT NULL,
    last_synced TEXT NOT NULL,
    PRIMARY KEY (topic, project_num)
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def upsert_projects(conn: sqlite3.Connection, projects: Iterable[Project], now: str = None) -> int:
    """Insert or update each project. Returns the number of rows written."""
    now = now or datetime.now(timezone.utc).isoformat()
    count = 0
    for project in projects:
        conn.execute(
            """
            INSERT INTO projects (
                topic, project_num, core_project_num, title, fiscal_year, award_amount,
                org_name, org_city, org_state, org_country, pi_names, agency_ic,
                start_date, end_date, first_seen, last_synced
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(topic, project_num) DO UPDATE SET
                core_project_num = excluded.core_project_num,
                title = excluded.title,
                fiscal_year = excluded.fiscal_year,
                award_amount = excluded.award_amount,
                org_name = excluded.org_name,
                org_city = excluded.org_city,
                org_state = excluded.org_state,
                org_country = excluded.org_country,
                pi_names = excluded.pi_names,
                agency_ic = excluded.agency_ic,
                start_date = excluded.start_date,
                end_date = excluded.end_date,
                last_synced = excluded.last_synced
            """,
            (
                project.topic, project.project_num, project.core_project_num, project.title,
                project.fiscal_year, project.award_amount, project.org_name, project.org_city,
                project.org_state, project.org_country, json.dumps(project.pi_names),
                project.agency_ic, project.start_date, project.end_date, now, now,
            ),
        )
        count += 1
    conn.commit()
    return count


def _row_to_project(row: sqlite3.Row) -> Project:
    return Project(
        topic=row["topic"],
        project_num=row["project_num"],
        core_project_num=row["core_project_num"],
        title=row["title"],
        fiscal_year=row["fiscal_year"],
        award_amount=row["award_amount"],
        org_name=row["org_name"],
        org_city=row["org_city"],
        org_state=row["org_state"],
        org_country=row["org_country"],
        pi_names=json.loads(row["pi_names"]),
        agency_ic=row["agency_ic"],
        start_date=row["start_date"],
        end_date=row["end_date"],
    )


def all_projects(conn: sqlite3.Connection, topic: str = None) -> list:
    """Return all stored projects, optionally filtered to one topic."""
    conn.row_factory = sqlite3.Row
    if topic is None:
        cursor = conn.execute("SELECT * FROM projects ORDER BY topic, fiscal_year DESC")
    else:
        cursor = conn.execute(
            "SELECT * FROM projects WHERE topic = ? ORDER BY fiscal_year DESC", (topic,)
        )
    return [_row_to_project(row) for row in cursor.fetchall()]


def project_count(conn: sqlite3.Connection) -> int:
    cursor = conn.execute("SELECT COUNT(*) FROM projects")
    return cursor.fetchone()[0]


def filtered_projects(conn: sqlite3.Connection, topics: Iterable[str], fy_start: int, fy_end: int) -> list:
    """Return stored projects restricted to `topics` and the [fy_start, fy_end] range.

    `report` uses this instead of `all_projects` so that requesting a narrower
    --topics/--fy-start/--fy-end than what was last synced doesn't pull in
    out-of-scope rows left over from a broader prior sync.
    """
    topics = list(topics)
    if not topics:
        return []
    conn.row_factory = sqlite3.Row
    placeholders = ",".join("?" for _ in topics)
    cursor = conn.execute(
        f"""
        SELECT * FROM projects
        WHERE topic IN ({placeholders}) AND fiscal_year BETWEEN ? AND ?
        ORDER BY topic, fiscal_year DESC
        """,
        (*topics, fy_start, fy_end),
    )
    return [_row_to_project(row) for row in cursor.fetchall()]


def reconcile_topic(
    conn: sqlite3.Connection, topic: str, fiscal_years: Iterable[int], seen_project_nums: Iterable[str]
) -> int:
    """Delete stored rows for `topic` whose fiscal_year was just re-synced but whose
    project_num was NOT among the results the latest sync returned.

    Without this, a project that NIH stops returning for a topic/fiscal-year search
    (corrected, withdrawn, or no longer matching) would linger in every future
    `report` forever, since `upsert_projects` only ever adds or updates rows it is
    given -- it never learns that a previously-seen row should be removed. Returns
    the number of rows deleted.
    """
    fiscal_years = list(fiscal_years)
    if not fiscal_years:
        return 0
    seen = list(seen_project_nums)
    fy_placeholders = ",".join("?" for _ in fiscal_years)
    if seen:
        seen_placeholders = ",".join("?" for _ in seen)
        cursor = conn.execute(
            f"""
            DELETE FROM projects
            WHERE topic = ? AND fiscal_year IN ({fy_placeholders})
            AND project_num NOT IN ({seen_placeholders})
            """,
            (topic, *fiscal_years, *seen),
        )
    else:
        # Nothing at all was returned for this topic across the synced fiscal
        # years -- every previously stored row in that range is now stale.
        cursor = conn.execute(
            f"DELETE FROM projects WHERE topic = ? AND fiscal_year IN ({fy_placeholders})",
            (topic, *fiscal_years),
        )
    conn.commit()
    return cursor.rowcount

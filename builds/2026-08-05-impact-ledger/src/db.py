"""SQLite persistence and trend/velocity queries for Impact Ledger."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS authors (
    author_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    works_count INTEGER NOT NULL,
    cited_by_count INTEGER NOT NULL,
    h_index INTEGER,
    i10_index INTEGER,
    last_synced TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS work_snapshots (
    work_id TEXT NOT NULL,
    sync_date TEXT NOT NULL,
    author_id TEXT NOT NULL,
    title TEXT NOT NULL,
    publication_year INTEGER,
    doi TEXT,
    host_venue TEXT,
    cited_by_count INTEGER NOT NULL,
    concepts TEXT,
    abstract TEXT,
    PRIMARY KEY (work_id, sync_date)
);
"""


def connect(db_path: str | Path) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_author(conn: sqlite3.Connection, author: dict[str, Any], sync_date: str) -> None:
    conn.execute(
        """
        INSERT INTO authors (author_id, display_name, works_count, cited_by_count, h_index, i10_index, last_synced)
        VALUES (:author_id, :display_name, :works_count, :cited_by_count, :h_index, :i10_index, :sync_date)
        ON CONFLICT(author_id) DO UPDATE SET
            display_name=excluded.display_name,
            works_count=excluded.works_count,
            cited_by_count=excluded.cited_by_count,
            h_index=excluded.h_index,
            i10_index=excluded.i10_index,
            last_synced=excluded.last_synced
        """,
        {**author, "sync_date": sync_date},
    )
    conn.commit()


def upsert_work_snapshot(conn: sqlite3.Connection, author_id: str, work: dict[str, Any], sync_date: str) -> None:
    conn.execute(
        """
        INSERT INTO work_snapshots
            (work_id, sync_date, author_id, title, publication_year, doi, host_venue, cited_by_count, concepts, abstract)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(work_id, sync_date) DO UPDATE SET
            title=excluded.title,
            publication_year=excluded.publication_year,
            doi=excluded.doi,
            host_venue=excluded.host_venue,
            cited_by_count=excluded.cited_by_count,
            concepts=excluded.concepts,
            abstract=excluded.abstract
        """,
        (
            work["work_id"],
            sync_date,
            author_id,
            work["title"],
            work.get("publication_year"),
            work.get("doi"),
            work.get("host_venue"),
            work.get("cited_by_count", 0),
            json.dumps(work.get("concepts", [])),
            work.get("abstract", ""),
        ),
    )
    conn.commit()


def get_author(conn: sqlite3.Connection, author_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM authors WHERE author_id = ?", (author_id,)).fetchone()
    return dict(row) if row else None


def distinct_sync_dates(conn: sqlite3.Connection, author_id: str) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT sync_date FROM work_snapshots WHERE author_id = ? ORDER BY sync_date ASC",
        (author_id,),
    ).fetchall()
    return [row["sync_date"] for row in rows]


def latest_snapshot(conn: sqlite3.Connection, author_id: str) -> list[dict[str, Any]]:
    dates = distinct_sync_dates(conn, author_id)
    if not dates:
        return []
    latest_date = dates[-1]
    rows = conn.execute(
        """
        SELECT * FROM work_snapshots
        WHERE author_id = ? AND sync_date = ?
        ORDER BY cited_by_count DESC
        """,
        (author_id, latest_date),
    ).fetchall()
    results = []
    for row in rows:
        record = dict(row)
        record["concepts"] = json.loads(record["concepts"] or "[]")
        results.append(record)
    return results


def citation_trend(conn: sqlite3.Connection, author_id: str) -> list[dict[str, Any]]:
    """Total citations across all works, aggregated per distinct sync date."""
    rows = conn.execute(
        """
        SELECT sync_date, SUM(cited_by_count) AS total_citations
        FROM work_snapshots
        WHERE author_id = ?
        GROUP BY sync_date
        ORDER BY sync_date ASC
        """,
        (author_id,),
    ).fetchall()
    return [{"sync_date": row["sync_date"], "total_citations": row["total_citations"]} for row in rows]


def rising_papers(conn: sqlite3.Connection, author_id: str) -> list[dict[str, Any]]:
    """Papers whose citation count increased between the two most recent distinct snapshots.

    Returns an empty list when fewer than 2 distinct sync dates exist yet.
    """
    dates = distinct_sync_dates(conn, author_id)
    if len(dates) < 2:
        return []

    latest_date, previous_date = dates[-1], dates[-2]
    latest_rows = {
        row["work_id"]: dict(row)
        for row in conn.execute(
            "SELECT * FROM work_snapshots WHERE author_id = ? AND sync_date = ?",
            (author_id, latest_date),
        ).fetchall()
    }
    previous_counts = {
        row["work_id"]: row["cited_by_count"]
        for row in conn.execute(
            "SELECT work_id, cited_by_count FROM work_snapshots WHERE author_id = ? AND sync_date = ?",
            (author_id, previous_date),
        ).fetchall()
    }

    rising = []
    for work_id, row in latest_rows.items():
        previous_count = previous_counts.get(work_id)
        if previous_count is None:
            continue
        velocity = row["cited_by_count"] - previous_count
        if velocity > 0:
            rising.append(
                {
                    "work_id": work_id,
                    "title": row["title"],
                    "cited_by_count": row["cited_by_count"],
                    "previous_cited_by_count": previous_count,
                    "velocity": velocity,
                    "abstract": row["abstract"],
                    "previous_date": previous_date,
                    "latest_date": latest_date,
                }
            )
    rising.sort(key=lambda item: item["velocity"], reverse=True)
    return rising

"""SQLite persistence layer for Throughline."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Iterable, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS author (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    author_id TEXT NOT NULL,
    name TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS papers (
    paper_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    abstract TEXT,
    year INTEGER,
    venue TEXT,
    citation_count INTEGER NOT NULL DEFAULT 0,
    external_url TEXT,
    first_seen_at TEXT NOT NULL,
    last_synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS citation_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id TEXT NOT NULL REFERENCES papers(paper_id),
    citation_count INTEGER NOT NULL,
    snapshot_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clusters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    keywords TEXT NOT NULL,
    computed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cluster_papers (
    cluster_id INTEGER NOT NULL REFERENCES clusters(id),
    paper_id TEXT NOT NULL REFERENCES papers(paper_id),
    PRIMARY KEY (cluster_id, paper_id)
);

CREATE TABLE IF NOT EXISTS narratives (
    cluster_id INTEGER PRIMARY KEY REFERENCES clusters(id),
    text TEXT NOT NULL,
    source TEXT NOT NULL,
    generated_at TEXT NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def set_author(conn: sqlite3.Connection, author_id: str, name: str) -> None:
    conn.execute(
        "INSERT INTO author (id, author_id, name, synced_at) VALUES (1, ?, ?, ?) "
        "ON CONFLICT(id) DO UPDATE SET author_id=excluded.author_id, "
        "name=excluded.name, synced_at=excluded.synced_at",
        (author_id, name, now_iso()),
    )
    conn.commit()


def get_author(conn: sqlite3.Connection) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM author WHERE id = 1").fetchone()


def upsert_papers(conn: sqlite3.Connection, papers: Iterable) -> int:
    """Upsert papers by paper_id and append a citation snapshot for each.

    Returns the number of papers written (inserted or updated).
    """
    timestamp = now_iso()
    count = 0
    for paper in papers:
        existing = conn.execute(
            "SELECT paper_id FROM papers WHERE paper_id = ?", (paper.paper_id,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE papers SET title=?, abstract=?, year=?, venue=?, "
                "citation_count=?, external_url=?, last_synced_at=? WHERE paper_id=?",
                (
                    paper.title,
                    paper.abstract,
                    paper.year,
                    paper.venue,
                    paper.citation_count,
                    paper.external_url,
                    timestamp,
                    paper.paper_id,
                ),
            )
        else:
            conn.execute(
                "INSERT INTO papers (paper_id, title, abstract, year, venue, "
                "citation_count, external_url, first_seen_at, last_synced_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    paper.paper_id,
                    paper.title,
                    paper.abstract,
                    paper.year,
                    paper.venue,
                    paper.citation_count,
                    paper.external_url,
                    timestamp,
                    timestamp,
                ),
            )
        conn.execute(
            "INSERT INTO citation_snapshots (paper_id, citation_count, snapshot_at) "
            "VALUES (?, ?, ?)",
            (paper.paper_id, paper.citation_count, timestamp),
        )
        count += 1
    conn.commit()
    return count


def list_papers(conn: sqlite3.Connection) -> list:
    return conn.execute("SELECT * FROM papers ORDER BY year DESC, title ASC").fetchall()


def citation_growth(conn: sqlite3.Connection) -> list:
    """Per-paper citation delta between the earliest and latest snapshot."""
    rows = conn.execute(
        "SELECT paper_id, citation_count, snapshot_at FROM citation_snapshots "
        "ORDER BY paper_id, snapshot_at ASC"
    ).fetchall()

    by_paper: dict = {}
    for row in rows:
        by_paper.setdefault(row["paper_id"], []).append(row)

    results = []
    for paper_id, snapshots in by_paper.items():
        first = snapshots[0]
        last = snapshots[-1]
        title_row = conn.execute(
            "SELECT title FROM papers WHERE paper_id = ?", (paper_id,)
        ).fetchone()
        results.append(
            {
                "paper_id": paper_id,
                "title": title_row["title"] if title_row else "(unknown)",
                "first_count": first["citation_count"],
                "latest_count": last["citation_count"],
                "delta": last["citation_count"] - first["citation_count"],
                "snapshots": len(snapshots),
            }
        )
    results.sort(key=lambda r: r["delta"], reverse=True)
    return results


def replace_clusters(conn: sqlite3.Connection, clusters: list) -> None:
    """Replace all stored clusters with a freshly computed set.

    `clusters` is a list of dicts: {"label": str, "keywords": [str], "paper_ids": [str]}.
    Narratives for clusters that no longer exist are dropped along with them.
    """
    timestamp = now_iso()
    conn.execute("DELETE FROM cluster_papers")
    conn.execute("DELETE FROM narratives")
    conn.execute("DELETE FROM clusters")
    for cluster in clusters:
        cursor = conn.execute(
            "INSERT INTO clusters (label, keywords, computed_at) VALUES (?, ?, ?)",
            (cluster["label"], json.dumps(cluster["keywords"]), timestamp),
        )
        cluster_id = cursor.lastrowid
        for paper_id in cluster["paper_ids"]:
            conn.execute(
                "INSERT INTO cluster_papers (cluster_id, paper_id) VALUES (?, ?)",
                (cluster_id, paper_id),
            )
    conn.commit()


def list_clusters(conn: sqlite3.Connection) -> list:
    clusters = conn.execute("SELECT * FROM clusters ORDER BY id ASC").fetchall()
    result = []
    for cluster in clusters:
        papers = conn.execute(
            "SELECT p.* FROM papers p "
            "JOIN cluster_papers cp ON cp.paper_id = p.paper_id "
            "WHERE cp.cluster_id = ? ORDER BY p.year DESC",
            (cluster["id"],),
        ).fetchall()
        narrative = conn.execute(
            "SELECT * FROM narratives WHERE cluster_id = ?", (cluster["id"],)
        ).fetchone()
        result.append(
            {
                "id": cluster["id"],
                "label": cluster["label"],
                "keywords": json.loads(cluster["keywords"]),
                "papers": papers,
                "narrative": narrative["text"] if narrative else None,
                "narrative_source": narrative["source"] if narrative else None,
            }
        )
    return result


def set_narrative(conn: sqlite3.Connection, cluster_id: int, text: str, source: str) -> None:
    conn.execute(
        "INSERT INTO narratives (cluster_id, text, source, generated_at) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(cluster_id) DO UPDATE SET text=excluded.text, "
        "source=excluded.source, generated_at=excluded.generated_at",
        (cluster_id, text, source, now_iso()),
    )
    conn.commit()

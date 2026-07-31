"""SQLite persistence layer: schema, topic CRUD, article dedup/upsert, search, stats."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    query TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS articles (
    pmid TEXT PRIMARY KEY,
    topic_id INTEGER NOT NULL REFERENCES topics(id),
    title TEXT NOT NULL,
    authors TEXT NOT NULL,
    journal TEXT,
    pub_date TEXT,
    abstract TEXT,
    url TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    relevance_score REAL,
    ai_summary TEXT,
    methodology_tag TEXT,
    scoring_method TEXT,
    starred INTEGER DEFAULT 0,
    read_state INTEGER DEFAULT 0
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_topic(conn: sqlite3.Connection, name: str, query: str) -> int:
    cursor = conn.execute(
        "INSERT INTO topics (name, query, created_at) VALUES (?, ?, ?)",
        (name, query, _now()),
    )
    conn.commit()
    return cursor.lastrowid


def list_topics(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM topics ORDER BY name").fetchall()


def get_topic_by_name(conn: sqlite3.Connection, name: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM topics WHERE name = ?", (name,)).fetchone()


def remove_topic(conn: sqlite3.Connection, name: str) -> bool:
    topic = get_topic_by_name(conn, name)
    if topic is None:
        return False
    conn.execute("DELETE FROM articles WHERE topic_id = ?", (topic["id"],))
    conn.execute("DELETE FROM topics WHERE id = ?", (topic["id"],))
    conn.commit()
    return True


def upsert_article(conn: sqlite3.Connection, topic_id: int, article: dict[str, Any]) -> bool:
    """Insert an article if its PMID is new. Returns True if a new row was inserted."""
    existing = conn.execute(
        "SELECT 1 FROM articles WHERE pmid = ?", (article["pmid"],)
    ).fetchone()
    if existing is not None:
        return False
    conn.execute(
        """
        INSERT INTO articles
            (pmid, topic_id, title, authors, journal, pub_date, abstract, url, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            article["pmid"],
            topic_id,
            article["title"],
            article["authors"],
            article.get("journal"),
            article.get("pub_date"),
            article.get("abstract"),
            article["url"],
            _now(),
        ),
    )
    conn.commit()
    return True


def set_scoring(
    conn: sqlite3.Connection,
    pmid: str,
    relevance_score: float,
    ai_summary: str | None,
    methodology_tag: str | None,
    scoring_method: str,
) -> None:
    conn.execute(
        """
        UPDATE articles
        SET relevance_score = ?, ai_summary = ?, methodology_tag = ?, scoring_method = ?
        WHERE pmid = ?
        """,
        (relevance_score, ai_summary, methodology_tag, scoring_method, pmid),
    )
    conn.commit()


def get_unscored_articles(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM articles WHERE relevance_score IS NULL"
    ).fetchall()


def get_articles_by_topic(conn: sqlite3.Connection, topic_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT * FROM articles
        WHERE topic_id = ?
        ORDER BY relevance_score DESC NULLS LAST, fetched_at DESC
        """,
        (topic_id,),
    ).fetchall()


def search_articles(conn: sqlite3.Connection, query: str) -> list[sqlite3.Row]:
    like = f"%{query}%"
    return conn.execute(
        """
        SELECT * FROM articles
        WHERE title LIKE ? COLLATE NOCASE
           OR abstract LIKE ? COLLATE NOCASE
           OR ai_summary LIKE ? COLLATE NOCASE
        ORDER BY relevance_score DESC NULLS LAST
        """,
        (like, like, like),
    ).fetchall()


def get_stats(conn: sqlite3.Connection) -> dict[str, Any]:
    total = conn.execute("SELECT COUNT(*) AS n FROM articles").fetchone()["n"]
    unscored = conn.execute(
        "SELECT COUNT(*) AS n FROM articles WHERE relevance_score IS NULL"
    ).fetchone()["n"]
    per_topic = conn.execute(
        """
        SELECT topics.name AS topic_name, COUNT(articles.pmid) AS count
        FROM topics
        LEFT JOIN articles ON articles.topic_id = topics.id
        GROUP BY topics.id
        ORDER BY topics.name
        """
    ).fetchall()
    return {
        "total": total,
        "unscored": unscored,
        "per_topic": [{"topic": row["topic_name"], "count": row["count"]} for row in per_topic],
    }

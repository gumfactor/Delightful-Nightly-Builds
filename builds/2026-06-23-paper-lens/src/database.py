"""SQLite persistence for Paper Lens."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_DB = Path(__file__).parent.parent / "data" / "papers.db"


def _get_db_path(db_path: Path = None) -> Path:
    return db_path or _DEFAULT_DB


def init_db(db_path: Path = None) -> None:
    path = _get_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                arxiv_id        TEXT UNIQUE NOT NULL,
                title           TEXT NOT NULL,
                authors         TEXT NOT NULL,
                abstract        TEXT NOT NULL,
                published_date  TEXT NOT NULL,
                fetched_date    TEXT NOT NULL,
                relevance_score INTEGER DEFAULT NULL,
                summary         TEXT DEFAULT NULL,
                methodology     TEXT DEFAULT NULL,
                topic_label     TEXT DEFAULT NULL,
                is_read         INTEGER DEFAULT 0
            )
        """)


def insert_paper(paper: dict, db_path: Path = None) -> bool:
    """Insert a paper. Returns True on success, False if arxiv_id already exists."""
    path = _get_db_path(db_path)
    try:
        with sqlite3.connect(str(path)) as conn:
            conn.execute(
                """
                INSERT INTO papers
                    (arxiv_id, title, authors, abstract, published_date, fetched_date,
                     relevance_score, summary, methodology, topic_label)
                VALUES
                    (:arxiv_id, :title, :authors, :abstract, :published_date, :fetched_date,
                     :relevance_score, :summary, :methodology, :topic_label)
                """,
                paper,
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_papers(db_path: Path = None) -> list:
    """Return all papers ordered by relevance desc, then fetched_date desc."""
    path = _get_db_path(db_path)
    with sqlite3.connect(str(path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT * FROM papers
            ORDER BY COALESCE(relevance_score, 0) DESC, fetched_date DESC
        """).fetchall()
    return [dict(row) for row in rows]


def mark_as_read(arxiv_id: str, db_path: Path = None) -> bool:
    """Mark a paper as read. Returns True if the row was found and updated."""
    path = _get_db_path(db_path)
    with sqlite3.connect(str(path)) as conn:
        cursor = conn.execute(
            "UPDATE papers SET is_read = 1 WHERE arxiv_id = ?", (arxiv_id,)
        )
    return cursor.rowcount > 0


def search_papers(query: str, db_path: Path = None) -> list:
    """Full-text search across title, summary, and topic_label."""
    path = _get_db_path(db_path)
    pattern = f"%{query}%"
    with sqlite3.connect(str(path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT * FROM papers
            WHERE title LIKE ? OR summary LIKE ? OR topic_label LIKE ? OR authors LIKE ?
            ORDER BY COALESCE(relevance_score, 0) DESC
            """,
            (pattern, pattern, pattern, pattern),
        ).fetchall()
    return [dict(row) for row in rows]


def get_today_count(db_path: Path = None) -> int:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = _get_db_path(db_path)
    with sqlite3.connect(str(path)) as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM papers WHERE fetched_date LIKE ?",
            (f"{today}%",),
        ).fetchone()
    return row[0] if row else 0

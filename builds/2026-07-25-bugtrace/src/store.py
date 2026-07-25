"""SQLite persistence. A commit is never re-classified once stored — a
second `sync` run is always safe to re-run and only adds genuinely new
fix commits."""

import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS fixes (
    repo         TEXT NOT NULL,
    sha          TEXT NOT NULL,
    message      TEXT NOT NULL,
    author_date  TEXT NOT NULL,
    category     TEXT NOT NULL,
    source       TEXT NOT NULL,
    explanation  TEXT NOT NULL,
    diff_excerpt TEXT NOT NULL,
    PRIMARY KEY (repo, sha)
)
"""

_COLUMNS = ["repo", "sha", "message", "author_date", "category", "source", "explanation", "diff_excerpt"]


def init_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def is_known(conn, repo, sha):
    row = conn.execute("SELECT 1 FROM fixes WHERE repo = ? AND sha = ?", (repo, sha)).fetchone()
    return row is not None


def upsert_fix(conn, repo, sha, message, author_date, category, source, explanation, diff_excerpt):
    conn.execute(
        "INSERT OR IGNORE INTO fixes (repo, sha, message, author_date, category, source, explanation, diff_excerpt) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (repo, sha, message, author_date, category, source, explanation, diff_excerpt),
    )
    conn.commit()


def get_all_fixes(conn):
    cur = conn.execute(f"SELECT {', '.join(_COLUMNS)} FROM fixes ORDER BY author_date DESC")
    return [dict(zip(_COLUMNS, row)) for row in cur.fetchall()]


def category_counts(conn):
    cur = conn.execute("SELECT category, COUNT(*) FROM fixes GROUP BY category ORDER BY COUNT(*) DESC, category ASC")
    return [{"category": row[0], "count": row[1]} for row in cur.fetchall()]


def monthly_counts(conn):
    cur = conn.execute(
        "SELECT substr(author_date, 1, 7) AS month, COUNT(*) FROM fixes GROUP BY month ORDER BY month ASC"
    )
    return [{"month": row[0], "count": row[1]} for row in cur.fetchall()]


def repo_counts(conn):
    cur = conn.execute("SELECT repo, COUNT(*) FROM fixes GROUP BY repo ORDER BY COUNT(*) DESC")
    return [{"repo": row[0], "count": row[1]} for row in cur.fetchall()]

"""SQLite persistence for CaseForge's local teaching-case library.

One row per PMID — an article is never re-fetched or duplicated by a
later `generate` run over an overlapping query unless the caller passes
--force, which explicitly deletes and re-inserts that row.
"""
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    pmid TEXT PRIMARY KEY,
    course TEXT NOT NULL,
    topic_query TEXT NOT NULL,
    title TEXT NOT NULL,
    journal TEXT,
    pub_year INTEGER,
    citation TEXT NOT NULL,
    abstract_text TEXT NOT NULL,
    sample_size INTEGER,
    population TEXT,
    methodology TEXT,
    effect_size_text TEXT,
    p_value_text TEXT,
    vignette_text TEXT NOT NULL,
    vignette_source TEXT NOT NULL,
    discussion_questions TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


@dataclass
class Case:
    pmid: str
    course: str
    topic_query: str
    title: str
    journal: Optional[str]
    pub_year: Optional[int]
    citation: str
    abstract_text: str
    sample_size: Optional[int]
    population: Optional[str]
    methodology: Optional[str]
    effect_size_text: Optional[str]
    p_value_text: Optional[str]
    vignette_text: str
    vignette_source: str
    discussion_questions: List[str]
    created_at: str


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def pmid_exists(conn: sqlite3.Connection, pmid: str) -> bool:
    row = conn.execute("SELECT 1 FROM cases WHERE pmid = ?", (pmid,)).fetchone()
    return row is not None


def insert_case(conn: sqlite3.Connection, case: Case, overwrite: bool = False) -> None:
    if overwrite:
        conn.execute("DELETE FROM cases WHERE pmid = ?", (case.pmid,))
    conn.execute(
        """INSERT INTO cases (
            pmid, course, topic_query, title, journal, pub_year, citation,
            abstract_text, sample_size, population, methodology,
            effect_size_text, p_value_text, vignette_text, vignette_source,
            discussion_questions, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            case.pmid,
            case.course,
            case.topic_query,
            case.title,
            case.journal,
            case.pub_year,
            case.citation,
            case.abstract_text,
            case.sample_size,
            case.population,
            case.methodology,
            case.effect_size_text,
            case.p_value_text,
            case.vignette_text,
            case.vignette_source,
            json.dumps(case.discussion_questions),
            case.created_at,
        ),
    )
    conn.commit()


def _row_to_case(row: sqlite3.Row) -> Case:
    return Case(
        pmid=row["pmid"],
        course=row["course"],
        topic_query=row["topic_query"],
        title=row["title"],
        journal=row["journal"],
        pub_year=row["pub_year"],
        citation=row["citation"],
        abstract_text=row["abstract_text"],
        sample_size=row["sample_size"],
        population=row["population"],
        methodology=row["methodology"],
        effect_size_text=row["effect_size_text"],
        p_value_text=row["p_value_text"],
        vignette_text=row["vignette_text"],
        vignette_source=row["vignette_source"],
        discussion_questions=json.loads(row["discussion_questions"]),
        created_at=row["created_at"],
    )


def list_cases(conn: sqlite3.Connection, course: Optional[str] = None) -> List[Case]:
    if course:
        rows = conn.execute(
            "SELECT * FROM cases WHERE course = ? ORDER BY created_at DESC",
            (course,),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM cases ORDER BY created_at DESC").fetchall()
    return [_row_to_case(row) for row in rows]


def get_case(conn: sqlite3.Connection, pmid: str) -> Optional[Case]:
    row = conn.execute("SELECT * FROM cases WHERE pmid = ?", (pmid,)).fetchone()
    return _row_to_case(row) if row else None


def search_cases(conn: sqlite3.Connection, keyword: str) -> List[Case]:
    like = f"%{keyword}%"
    rows = conn.execute(
        """SELECT * FROM cases
           WHERE title LIKE ? OR abstract_text LIKE ? OR course LIKE ?
           ORDER BY created_at DESC""",
        (like, like, like),
    ).fetchall()
    return [_row_to_case(row) for row in rows]


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

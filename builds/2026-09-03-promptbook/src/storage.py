"""SQLite persistence for the Promptbook library."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "promptbook.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS prompts (
    prompt_uuid TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    project TEXT NOT NULL,
    git_branch TEXT,
    entrypoint TEXT,
    timestamp TEXT NOT NULL,
    prompt_text TEXT NOT NULL,
    task_type TEXT NOT NULL,
    score INTEGER NOT NULL,
    tools_used TEXT NOT NULL,
    files_edited INTEGER NOT NULL,
    test_run INTEGER NOT NULL,
    test_passed INTEGER,
    git_commit INTEGER NOT NULL,
    had_error INTEGER NOT NULL,
    ai_note TEXT
);

CREATE TABLE IF NOT EXISTS ingested_files (
    file_path TEXT PRIMARY KEY,
    last_line_count INTEGER NOT NULL,
    last_ingested_at TEXT NOT NULL
);
"""


@dataclass
class StoredPrompt:
    prompt_uuid: str
    session_id: str
    project: str
    git_branch: str | None
    entrypoint: str | None
    timestamp: str
    prompt_text: str
    task_type: str
    score: int
    tools_used: list[str]
    files_edited: int
    test_run: bool
    test_passed: bool | None
    git_commit: bool
    had_error: bool
    ai_note: str | None = None


def connect(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def get_last_line_count(conn: sqlite3.Connection, file_path: str) -> int:
    row = conn.execute(
        "SELECT last_line_count FROM ingested_files WHERE file_path = ?", (file_path,)
    ).fetchone()
    return int(row["last_line_count"]) if row else 0


def set_last_line_count(conn: sqlite3.Connection, file_path: str, line_count: int, ingested_at: str) -> None:
    conn.execute(
        """
        INSERT INTO ingested_files (file_path, last_line_count, last_ingested_at)
        VALUES (?, ?, ?)
        ON CONFLICT(file_path) DO UPDATE SET
            last_line_count = excluded.last_line_count,
            last_ingested_at = excluded.last_ingested_at
        """,
        (file_path, line_count, ingested_at),
    )


def upsert_prompt(conn: sqlite3.Connection, prompt: StoredPrompt) -> bool:
    """Insert a prompt if it doesn't already exist. Returns True if a new row was inserted."""
    cursor = conn.execute(
        """
        INSERT OR IGNORE INTO prompts (
            prompt_uuid, session_id, project, git_branch, entrypoint, timestamp,
            prompt_text, task_type, score, tools_used, files_edited, test_run,
            test_passed, git_commit, had_error, ai_note
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            prompt.prompt_uuid,
            prompt.session_id,
            prompt.project,
            prompt.git_branch,
            prompt.entrypoint,
            prompt.timestamp,
            prompt.prompt_text,
            prompt.task_type,
            prompt.score,
            json.dumps(prompt.tools_used),
            prompt.files_edited,
            int(prompt.test_run),
            None if prompt.test_passed is None else int(prompt.test_passed),
            int(prompt.git_commit),
            int(prompt.had_error),
            prompt.ai_note,
        ),
    )
    return cursor.rowcount > 0


def set_ai_note(conn: sqlite3.Connection, prompt_uuid: str, note: str) -> None:
    conn.execute("UPDATE prompts SET ai_note = ? WHERE prompt_uuid = ?", (note, prompt_uuid))


def search_prompts(
    conn: sqlite3.Connection,
    project: str | None = None,
    task_type: str | None = None,
    min_score: int | None = None,
    query: str | None = None,
    limit: int = 50,
) -> list[sqlite3.Row]:
    clauses = []
    params: list[object] = []
    if project:
        clauses.append("project = ?")
        params.append(project)
    if task_type:
        clauses.append("task_type = ?")
        params.append(task_type)
    if min_score is not None:
        clauses.append("score >= ?")
        params.append(min_score)
    if query:
        clauses.append("prompt_text LIKE ?")
        params.append(f"%{query}%")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT * FROM prompts {where} ORDER BY score DESC, timestamp DESC LIMIT ?"
    params.append(limit)
    return list(conn.execute(sql, params).fetchall())


def get_stats(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) AS c FROM prompts").fetchone()["c"]
    by_task_type = {
        row["task_type"]: row["c"]
        for row in conn.execute(
            "SELECT task_type, COUNT(*) AS c FROM prompts GROUP BY task_type ORDER BY c DESC"
        ).fetchall()
    }
    by_project = {
        row["project"]: row["c"]
        for row in conn.execute(
            "SELECT project, COUNT(*) AS c FROM prompts GROUP BY project ORDER BY c DESC"
        ).fetchall()
    }
    avg_score_row = conn.execute("SELECT AVG(score) AS avg_score FROM prompts").fetchone()
    avg_score = round(avg_score_row["avg_score"], 2) if avg_score_row["avg_score"] is not None else 0.0
    return {
        "total": total,
        "by_task_type": by_task_type,
        "by_project": by_project,
        "avg_score": avg_score,
    }


def get_all_prompts(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(conn.execute("SELECT * FROM prompts ORDER BY score DESC, timestamp DESC").fetchall())

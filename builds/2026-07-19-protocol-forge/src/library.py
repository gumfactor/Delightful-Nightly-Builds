"""Local SQLite protocol library: persistence, approval, and deterministic
tag-based similarity matching for boilerplate section reuse.

Reuse is intentionally tag-based rather than fuzzy/embedding-based text
similarity: it requires no model or network call, is fully deterministic and
testable, and only ever surfaces text a human previously approved.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.models import Study

STATUS_DRAFT = "draft"
STATUS_APPROVED = "approved"

REUSE_THRESHOLD = 0.5

_SCHEMA = """
CREATE TABLE IF NOT EXISTS protocols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    completeness_score INTEGER NOT NULL,
    study_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    protocol_id INTEGER NOT NULL,
    section_key TEXT NOT NULL,
    text TEXT NOT NULL,
    source TEXT NOT NULL,
    tags TEXT NOT NULL,
    FOREIGN KEY (protocol_id) REFERENCES protocols (id)
);
"""


@dataclass
class ProtocolRecord:
    id: int
    title: str
    status: str
    completeness_score: int
    created_at: str
    study: Study
    sections: dict[str, dict[str, str]]  # section_key -> {"text":..., "source":...}


@dataclass
class ReuseMatch:
    text: str
    source_protocol_id: int
    score: float


class ProtocolLibrary:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "ProtocolLibrary":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    def save_protocol(
        self,
        study: Study,
        sections: dict[str, tuple[str, str]],
        completeness_score: int,
    ) -> int:
        """sections maps section_key -> (text, source). Returns the new protocol id."""
        tags = sorted(study.tag_set())
        created_at = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            "INSERT INTO protocols (title, status, completeness_score, study_json, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (study.title, STATUS_DRAFT, completeness_score, json.dumps(study.to_json_dict()), created_at),
        )
        protocol_id = cur.lastrowid
        for section_key, (text, source) in sections.items():
            self._conn.execute(
                "INSERT INTO sections (protocol_id, section_key, text, source, tags) "
                "VALUES (?, ?, ?, ?, ?)",
                (protocol_id, section_key, text, source, json.dumps(tags)),
            )
        self._conn.commit()
        return protocol_id

    def approve(self, protocol_id: int) -> None:
        cur = self._conn.execute(
            "UPDATE protocols SET status = ? WHERE id = ?", (STATUS_APPROVED, protocol_id)
        )
        self._conn.commit()
        if cur.rowcount == 0:
            raise ValueError(f"No protocol with id {protocol_id}")

    def list_protocols(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, title, status, completeness_score, created_at FROM protocols ORDER BY id"
        ).fetchall()
        return [dict(row) for row in rows]

    def get_protocol(self, protocol_id: int) -> Optional[ProtocolRecord]:
        row = self._conn.execute(
            "SELECT * FROM protocols WHERE id = ?", (protocol_id,)
        ).fetchone()
        if row is None:
            return None
        section_rows = self._conn.execute(
            "SELECT section_key, text, source FROM sections WHERE protocol_id = ?",
            (protocol_id,),
        ).fetchall()
        sections = {
            r["section_key"]: {"text": r["text"], "source": r["source"]} for r in section_rows
        }
        study = Study.from_dict(json.loads(row["study_json"]))
        return ProtocolRecord(
            id=row["id"],
            title=row["title"],
            status=row["status"],
            completeness_score=row["completeness_score"],
            created_at=row["created_at"],
            study=study,
            sections=sections,
        )

    def find_reusable_section(self, study: Study, section_key: str) -> Optional[ReuseMatch]:
        """Best-matching APPROVED protocol's text for section_key, by tag Jaccard overlap."""
        query_tags = study.tag_set()
        rows = self._conn.execute(
            """
            SELECT s.protocol_id, s.text, s.tags
            FROM sections s
            JOIN protocols p ON p.id = s.protocol_id
            WHERE s.section_key = ? AND p.status = ?
            """,
            (section_key, STATUS_APPROVED),
        ).fetchall()

        best: Optional[ReuseMatch] = None
        for row in rows:
            candidate_tags = set(json.loads(row["tags"]))
            union = query_tags | candidate_tags
            if not union:
                continue
            score = len(query_tags & candidate_tags) / len(union)
            if score >= REUSE_THRESHOLD and (best is None or score > best.score):
                best = ReuseMatch(text=row["text"], source_protocol_id=row["protocol_id"], score=score)
        return best

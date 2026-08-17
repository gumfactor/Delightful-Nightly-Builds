"""SQLite persistence for generated pieces. Append-only: pieces are never overwritten."""

from __future__ import annotations

import json
import sqlite3

_COLUMNS = [
    "id",
    "created_at",
    "piece_type",
    "tone",
    "occasion",
    "headline",
    "body_markdown",
    "businesses_json",
    "novelty_score",
    "ai_polished",
]


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pieces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            piece_type TEXT NOT NULL,
            tone TEXT NOT NULL,
            occasion TEXT NOT NULL,
            headline TEXT NOT NULL,
            body_markdown TEXT NOT NULL,
            businesses_json TEXT NOT NULL,
            novelty_score REAL NOT NULL,
            ai_polished INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()
    return conn


def insert_piece(
    conn: sqlite3.Connection,
    piece_type: str,
    tone: str,
    occasion: str,
    headline: str,
    body_markdown: str,
    businesses: list[dict],
    novelty_score: float,
    ai_polished: bool = False,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO pieces
            (piece_type, tone, occasion, headline, body_markdown,
             businesses_json, novelty_score, ai_polished)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            piece_type,
            tone,
            occasion,
            headline,
            body_markdown,
            json.dumps(businesses),
            novelty_score,
            int(ai_polished),
        ),
    )
    conn.commit()
    return cur.lastrowid


def get_piece(conn: sqlite3.Connection, piece_id: int) -> dict:
    row = conn.execute(
        f"SELECT {', '.join(_COLUMNS)} FROM pieces WHERE id = ?", (piece_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"No piece found with id {piece_id}.")
    return _row_to_dict(row)


def list_pieces(
    conn: sqlite3.Connection, piece_type: str | None = None, tone: str | None = None
) -> list[dict]:
    query = f"SELECT {', '.join(_COLUMNS)} FROM pieces"
    conditions = []
    params: list[str] = []
    if piece_type:
        conditions.append("piece_type = ?")
        params.append(piece_type)
    if tone:
        conditions.append("tone = ?")
        params.append(tone)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id ASC"
    rows = conn.execute(query, params).fetchall()
    return [_row_to_dict(row) for row in rows]


def history_full_texts(conn: sqlite3.Connection, piece_type: str) -> list[str]:
    rows = conn.execute(
        "SELECT headline, body_markdown FROM pieces WHERE piece_type = ?", (piece_type,)
    ).fetchall()
    return [f"{headline}\n\n{body}" for headline, body in rows]


def _row_to_dict(row: tuple) -> dict:
    data = dict(zip(_COLUMNS, row))
    data["businesses"] = json.loads(data.pop("businesses_json"))
    data["ai_polished"] = bool(data["ai_polished"])
    return data

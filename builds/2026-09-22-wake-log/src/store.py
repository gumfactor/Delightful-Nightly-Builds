"""Local SQLite persistence for Wake Log entries.

Append-only by design: there is no update or delete function. Every
`generate` run produces a new permanent row, so the journal is a real,
growing record of outings rather than a single mutable snapshot.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL,
  location_name TEXT NOT NULL,
  latitude REAL NOT NULL,
  longitude REAL NOT NULL,
  target_date TEXT NOT NULL,
  window_label TEXT NOT NULL,
  score REAL NOT NULL,
  beaufort INTEGER NOT NULL,
  beaufort_name TEXT NOT NULL,
  wind_knots REAL NOT NULL,
  gust_knots REAL NOT NULL,
  temp_c REAL NOT NULL,
  precip_probability REAL NOT NULL,
  cloud_cover REAL NOT NULL,
  narrative TEXT NOT NULL,
  ai_polished INTEGER NOT NULL DEFAULT 0
);
"""


@dataclass
class Entry:
    id: int
    created_at: str
    location_name: str
    latitude: float
    longitude: float
    target_date: str
    window_label: str
    score: float
    beaufort: int
    beaufort_name: str
    wind_knots: float
    gust_knots: float
    temp_c: float
    precip_probability: float
    cloud_cover: float
    narrative: str
    ai_polished: bool

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Entry":
        return cls(
            id=row["id"],
            created_at=row["created_at"],
            location_name=row["location_name"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            target_date=row["target_date"],
            window_label=row["window_label"],
            score=row["score"],
            beaufort=row["beaufort"],
            beaufort_name=row["beaufort_name"],
            wind_knots=row["wind_knots"],
            gust_knots=row["gust_knots"],
            temp_c=row["temp_c"],
            precip_probability=row["precip_probability"],
            cloud_cover=row["cloud_cover"],
            narrative=row["narrative"],
            ai_polished=bool(row["ai_polished"]),
        )


class Store:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def save(
        self,
        created_at: str,
        location_name: str,
        latitude: float,
        longitude: float,
        target_date: str,
        window_label: str,
        score: float,
        beaufort: int,
        beaufort_name: str,
        wind_knots: float,
        gust_knots: float,
        temp_c: float,
        precip_probability: float,
        cloud_cover: float,
        narrative: str,
        ai_polished: bool,
    ) -> int:
        cursor = self._conn.execute(
            """
            INSERT INTO entries (
                created_at, location_name, latitude, longitude, target_date,
                window_label, score, beaufort, beaufort_name, wind_knots,
                gust_knots, temp_c, precip_probability, cloud_cover, narrative,
                ai_polished
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at, location_name, latitude, longitude, target_date,
                window_label, score, beaufort, beaufort_name, wind_knots,
                gust_knots, temp_c, precip_probability, cloud_cover, narrative,
                int(ai_polished),
            ),
        )
        self._conn.commit()
        return cursor.lastrowid

    def list_entries(self, limit: Optional[int] = None) -> List[Entry]:
        query = "SELECT * FROM entries ORDER BY created_at DESC"
        params: tuple = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)
        rows = self._conn.execute(query, params).fetchall()
        return [Entry.from_row(r) for r in rows]

    def get(self, entry_id: int) -> Optional[Entry]:
        row = self._conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        return Entry.from_row(row) if row else None

    def search(self, query: str) -> List[Entry]:
        like = f"%{query}%"
        rows = self._conn.execute(
            "SELECT * FROM entries WHERE narrative LIKE ? OR location_name LIKE ? ORDER BY created_at DESC",
            (like, like),
        ).fetchall()
        return [Entry.from_row(r) for r in rows]

    def history_for_location(self, location_name: str) -> List[str]:
        """Narrative texts previously generated for this location -- the
        novelty-scoring corpus."""
        rows = self._conn.execute(
            "SELECT narrative FROM entries WHERE location_name = ? ORDER BY created_at DESC",
            (location_name,),
        ).fetchall()
        return [r["narrative"] for r in rows]

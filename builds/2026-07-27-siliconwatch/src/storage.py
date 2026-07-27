"""SQLite persistence for SiliconWatch snapshots and price history."""
import sqlite3
from typing import Dict, List, Optional, Tuple

SNAPSHOT_COLUMNS = (
    "ticker",
    "name",
    "subsector",
    "snapshot_date",
    "price",
    "market_cap",
    "pe_trailing",
    "pe_forward",
    "peg_ratio",
    "profit_margin",
    "revenue_growth",
    "target_mean_price",
    "week52_low",
    "week52_high",
    "fetched_at",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    ticker TEXT NOT NULL,
    name TEXT NOT NULL,
    subsector TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    price REAL,
    market_cap REAL,
    pe_trailing REAL,
    pe_forward REAL,
    peg_ratio REAL,
    profit_margin REAL,
    revenue_growth REAL,
    target_mean_price REAL,
    week52_low REAL,
    week52_high REAL,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (ticker, snapshot_date)
);

CREATE TABLE IF NOT EXISTS price_history (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    close REAL NOT NULL,
    PRIMARY KEY (ticker, date)
);
"""


class SiliconWatchDB:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def upsert_snapshot(self, row: Dict) -> None:
        placeholders = ", ".join("?" for _ in SNAPSHOT_COLUMNS)
        columns = ", ".join(SNAPSHOT_COLUMNS)
        values = [row.get(col) for col in SNAPSHOT_COLUMNS]
        self.conn.execute(
            f"INSERT OR REPLACE INTO snapshots ({columns}) VALUES ({placeholders})",
            values,
        )
        self.conn.commit()

    def insert_price_history(self, ticker: str, rows: List[Tuple[str, float]]) -> None:
        self.conn.executemany(
            "INSERT OR REPLACE INTO price_history (ticker, date, close) VALUES (?, ?, ?)",
            [(ticker, date, close) for date, close in rows],
        )
        self.conn.commit()

    def get_latest_snapshots(self) -> List[Dict]:
        cursor = self.conn.execute(
            """
            SELECT s.* FROM snapshots s
            INNER JOIN (
                SELECT ticker, MAX(snapshot_date) AS max_date
                FROM snapshots
                GROUP BY ticker
            ) latest
            ON s.ticker = latest.ticker AND s.snapshot_date = latest.max_date
            ORDER BY s.market_cap DESC NULLS LAST
            """
        )
        return [dict(r) for r in cursor.fetchall()]

    def get_snapshot_history(self, ticker: str) -> List[Dict]:
        cursor = self.conn.execute(
            "SELECT * FROM snapshots WHERE ticker = ? ORDER BY snapshot_date ASC",
            (ticker,),
        )
        return [dict(r) for r in cursor.fetchall()]

    def list_snapshot_dates(self) -> List[str]:
        cursor = self.conn.execute(
            "SELECT DISTINCT snapshot_date FROM snapshots ORDER BY snapshot_date ASC"
        )
        return [r["snapshot_date"] for r in cursor.fetchall()]

    def sector_pe_by_date(self) -> List[Tuple[str, Optional[float]]]:
        cursor = self.conn.execute(
            """
            SELECT snapshot_date, AVG(pe_trailing) AS avg_pe
            FROM snapshots
            WHERE pe_trailing IS NOT NULL
            GROUP BY snapshot_date
            ORDER BY snapshot_date ASC
            """
        )
        return [(r["snapshot_date"], r["avg_pe"]) for r in cursor.fetchall()]

    def get_price_history(self, ticker: str) -> List[Tuple[str, float]]:
        cursor = self.conn.execute(
            "SELECT date, close FROM price_history WHERE ticker = ? ORDER BY date ASC",
            (ticker,),
        )
        return [(r["date"], r["close"]) for r in cursor.fetchall()]

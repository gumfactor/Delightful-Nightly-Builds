"""SQLite persistence: ticker->CIK cache and per-fiscal-year financials.

All writes are upserts keyed by primary key, so re-running sync on the
same ticker/fiscal-year never duplicates rows -- it reflects the latest
extraction (e.g. after a 10-K/A restatement supersedes an original filing).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickers (
    ticker TEXT PRIMARY KEY,
    cik TEXT NOT NULL,
    company_name TEXT NOT NULL,
    resolved_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS financials (
    cik TEXT NOT NULL,
    ticker TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    company_name TEXT NOT NULL,
    revenue REAL,
    net_income REAL,
    operating_income REAL,
    assets REAL,
    liabilities REAL,
    equity REAL,
    cash REAL,
    filed_date TEXT,
    accn TEXT,
    synced_at TEXT NOT NULL,
    PRIMARY KEY (cik, fiscal_year)
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def upsert_ticker(conn: sqlite3.Connection, ticker: str, cik: str, company_name: str) -> None:
    conn.execute(
        """
        INSERT INTO tickers (ticker, cik, company_name, resolved_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(ticker) DO UPDATE SET
            cik = excluded.cik,
            company_name = excluded.company_name,
            resolved_at = excluded.resolved_at
        """,
        (ticker.upper(), cik, company_name, _now()),
    )
    conn.commit()


def get_ticker(conn: sqlite3.Connection, ticker: str) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM tickers WHERE ticker = ?", (ticker.upper(),))
    return cur.fetchone()


def list_tickers(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    cur = conn.execute("SELECT * FROM tickers ORDER BY ticker")
    return cur.fetchall()


def upsert_financials(
    conn: sqlite3.Connection,
    cik: str,
    ticker: str,
    company_name: str,
    rows: list[dict[str, Any]],
) -> int:
    """Upsert one row per fiscal year. Returns the number of rows written."""
    synced_at = _now()
    count = 0
    for row in rows:
        conn.execute(
            """
            INSERT INTO financials (
                cik, ticker, fiscal_year, company_name,
                revenue, net_income, operating_income,
                assets, liabilities, equity, cash,
                filed_date, accn, synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(cik, fiscal_year) DO UPDATE SET
                ticker = excluded.ticker,
                company_name = excluded.company_name,
                revenue = excluded.revenue,
                net_income = excluded.net_income,
                operating_income = excluded.operating_income,
                assets = excluded.assets,
                liabilities = excluded.liabilities,
                equity = excluded.equity,
                cash = excluded.cash,
                filed_date = excluded.filed_date,
                accn = excluded.accn,
                synced_at = excluded.synced_at
            """,
            (
                cik,
                ticker.upper(),
                row["fiscal_year"],
                company_name,
                row.get("revenue"),
                row.get("net_income"),
                row.get("operating_income"),
                row.get("assets"),
                row.get("liabilities"),
                row.get("equity"),
                row.get("cash"),
                row.get("filed_date"),
                row.get("accn"),
                synced_at,
            ),
        )
        count += 1
    conn.commit()
    return count


def get_financials(conn: sqlite3.Connection, ticker: str) -> list[dict[str, Any]]:
    cur = conn.execute(
        "SELECT * FROM financials WHERE ticker = ? ORDER BY fiscal_year ASC",
        (ticker.upper(),),
    )
    return [dict(row) for row in cur.fetchall()]


def get_all_financials(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    cur = conn.execute(
        "SELECT * FROM financials ORDER BY ticker ASC, fiscal_year ASC"
    )
    return [dict(row) for row in cur.fetchall()]


def get_tracked_tickers(conn: sqlite3.Connection) -> list[str]:
    cur = conn.execute("SELECT DISTINCT ticker FROM financials ORDER BY ticker")
    return [row["ticker"] for row in cur.fetchall()]

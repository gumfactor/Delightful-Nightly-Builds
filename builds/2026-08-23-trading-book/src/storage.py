"""Local SQLite persistence for daily IBKR account snapshots.

One row per UTC calendar day: re-syncing on the same day updates that
snapshot in place and replaces its positions, rather than duplicating it,
so `history`/`render` show a clean multi-day trend.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_date TEXT NOT NULL UNIQUE,
    synced_at TEXT NOT NULL,
    account_id TEXT NOT NULL,
    net_liquidation REAL NOT NULL,
    total_cash REAL NOT NULL,
    gross_position_value REAL NOT NULL,
    unrealized_pnl REAL NOT NULL,
    realized_pnl REAL NOT NULL,
    buying_power REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id INTEGER NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
    symbol TEXT NOT NULL,
    sec_type TEXT NOT NULL,
    currency TEXT NOT NULL,
    exchange TEXT,
    quantity REAL NOT NULL,
    avg_cost REAL NOT NULL,
    market_price REAL NOT NULL,
    market_value REAL NOT NULL,
    unrealized_pnl REAL NOT NULL
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def sync_snapshot(
    conn: sqlite3.Connection,
    snapshot: dict[str, Any],
    snapshot_date: str | None = None,
    synced_at: str | None = None,
) -> int:
    """Insert or update the snapshot row for `snapshot_date` (default: today,
    UTC) and fully replace its positions. Returns the snapshot id."""
    snapshot_date = snapshot_date or today_utc()
    synced_at = synced_at or now_utc_iso()

    existing = conn.execute(
        "SELECT id FROM snapshots WHERE snapshot_date = ?", (snapshot_date,)
    ).fetchone()

    fields = (
        synced_at,
        snapshot["account_id"],
        snapshot["net_liquidation"],
        snapshot["total_cash"],
        snapshot["gross_position_value"],
        snapshot["unrealized_pnl"],
        snapshot["realized_pnl"],
        snapshot["buying_power"],
    )

    if existing is None:
        cur = conn.execute(
            """INSERT INTO snapshots
               (snapshot_date, synced_at, account_id, net_liquidation, total_cash,
                gross_position_value, unrealized_pnl, realized_pnl, buying_power)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (snapshot_date, *fields),
        )
        snapshot_id = cur.lastrowid
    else:
        snapshot_id = existing["id"]
        conn.execute(
            """UPDATE snapshots SET synced_at = ?, account_id = ?, net_liquidation = ?,
               total_cash = ?, gross_position_value = ?, unrealized_pnl = ?,
               realized_pnl = ?, buying_power = ? WHERE id = ?""",
            (*fields, snapshot_id),
        )
        conn.execute("DELETE FROM positions WHERE snapshot_id = ?", (snapshot_id,))

    for position in snapshot["positions"]:
        conn.execute(
            """INSERT INTO positions
               (snapshot_id, symbol, sec_type, currency, exchange, quantity,
                avg_cost, market_price, market_value, unrealized_pnl)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                snapshot_id,
                position["symbol"],
                position["sec_type"],
                position["currency"],
                position["exchange"],
                position["quantity"],
                position["avg_cost"],
                position["market_price"],
                position["market_value"],
                position["unrealized_pnl"],
            ),
        )

    conn.commit()
    return snapshot_id


def get_latest_snapshot(conn: sqlite3.Connection) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM snapshots ORDER BY snapshot_date DESC LIMIT 1").fetchone()
    if row is None:
        return None
    return _attach_positions(conn, dict(row))


def get_history(conn: sqlite3.Connection, days: int | None = None) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM snapshots ORDER BY snapshot_date ASC").fetchall()
    results = [dict(r) for r in rows]
    if days is not None and days > 0:
        results = results[-days:]
    return results


def get_all_snapshots_with_positions(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """All snapshots (ascending date) with their positions attached — used by report.py."""
    return [_attach_positions(conn, s) for s in get_history(conn)]


def _attach_positions(conn: sqlite3.Connection, snapshot: dict[str, Any]) -> dict[str, Any]:
    rows = conn.execute(
        "SELECT * FROM positions WHERE snapshot_id = ? ORDER BY market_value DESC",
        (snapshot["id"],),
    ).fetchall()
    snapshot["positions"] = [dict(r) for r in rows]
    return snapshot


def today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

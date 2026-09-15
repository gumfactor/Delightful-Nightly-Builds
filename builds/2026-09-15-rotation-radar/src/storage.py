"""Local SQLite persistence of per-run sector snapshots, so rotation can be
tracked across multiple invocations over time.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshots (
    run_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    rs_ratio REAL NOT NULL,
    rs_momentum REAL NOT NULL,
    quadrant TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
"""


@dataclass(frozen=True)
class QuadrantTransition:
    ticker: str
    previous_quadrant: str | None
    current_quadrant: str
    changed: bool


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def save_run(conn: sqlite3.Connection, run_timestamp: str, snapshots: dict) -> int:
    """Persist one run's per-sector snapshot. `snapshots` maps ticker -> SectorResult.

    Returns the new run's id.
    """
    cur = conn.execute("INSERT INTO runs (run_timestamp) VALUES (?)", (run_timestamp,))
    run_id = cur.lastrowid
    conn.executemany(
        "INSERT INTO snapshots (run_id, ticker, rs_ratio, rs_momentum, quadrant) "
        "VALUES (?, ?, ?, ?, ?)",
        [
            (run_id, ticker, result.latest.rs_ratio, result.latest.rs_momentum, result.latest.quadrant)
            for ticker, result in snapshots.items()
        ],
    )
    conn.commit()
    return run_id


def get_previous_run_snapshot(conn: sqlite3.Connection, before_run_id: int | None = None) -> dict:
    """Return dict[ticker -> quadrant] for the most recent run before `before_run_id`
    (or the most recent run overall if `before_run_id` is None). Empty dict if none exists.
    """
    if before_run_id is None:
        row = conn.execute("SELECT id FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    else:
        row = conn.execute(
            "SELECT id FROM runs WHERE id < ? ORDER BY id DESC LIMIT 1", (before_run_id,)
        ).fetchone()
    if row is None:
        return {}
    run_id = row[0]
    rows = conn.execute(
        "SELECT ticker, quadrant FROM snapshots WHERE run_id = ?", (run_id,)
    ).fetchall()
    return {ticker: quadrant for ticker, quadrant in rows}


def compute_transitions(previous: dict, current: dict) -> list:
    """Compare a previous run's ticker->quadrant map against the current snapshot.

    `current` maps ticker -> SectorResult. Returns a list[QuadrantTransition],
    one per ticker in `current`, sorted by ticker. A ticker absent from
    `previous` (including the very first run) reports previous_quadrant=None
    and changed=False.
    """
    transitions = []
    for ticker in sorted(current.keys()):
        prev_quadrant = previous.get(ticker)
        curr_quadrant = current[ticker].latest.quadrant
        transitions.append(
            QuadrantTransition(
                ticker=ticker,
                previous_quadrant=prev_quadrant,
                current_quadrant=curr_quadrant,
                changed=prev_quadrant is not None and prev_quadrant != curr_quadrant,
            )
        )
    return transitions


def get_history(conn: sqlite3.Connection, ticker: str) -> list:
    """Return [(run_timestamp, rs_ratio, rs_momentum, quadrant), ...] for one ticker,
    oldest run first.
    """
    return conn.execute(
        "SELECT r.run_timestamp, s.rs_ratio, s.rs_momentum, s.quadrant "
        "FROM snapshots s JOIN runs r ON s.run_id = r.id "
        "WHERE s.ticker = ? ORDER BY r.id ASC",
        (ticker,),
    ).fetchall()

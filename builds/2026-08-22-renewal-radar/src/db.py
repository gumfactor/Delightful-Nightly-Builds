"""SQLite persistence for Renewal Radar."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS domains (
    id INTEGER PRIMARY KEY,
    domain TEXT NOT NULL UNIQUE,
    project_label TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS domain_snapshots (
    id INTEGER PRIMARY KEY,
    domain_id INTEGER NOT NULL REFERENCES domains(id),
    snapshot_date TEXT NOT NULL,
    rdap_status TEXT NOT NULL,
    rdap_expiration TEXT,
    rdap_registrar TEXT,
    ssl_status TEXT NOT NULL,
    ssl_expiration TEXT,
    ssl_days_remaining INTEGER,
    UNIQUE(domain_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS manual_renewals (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    project_label TEXT,
    due_date TEXT NOT NULL,
    recurrence TEXT NOT NULL,
    recurrence_n INTEGER,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    completed_at TEXT
);
"""

VALID_CATEGORIES = {"license", "insurance", "subscription", "membership", "certification", "other"}
VALID_RECURRENCES = {"one-time", "annual", "monthly", "every-N-months"}


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def add_domain(conn: sqlite3.Connection, domain: str, project_label: Optional[str], created_at: str) -> int:
    domain = domain.strip().lower()
    if not domain:
        raise ValueError("Domain name cannot be empty")
    try:
        cur = conn.execute(
            "INSERT INTO domains (domain, project_label, created_at) VALUES (?, ?, ?)",
            (domain, project_label, created_at),
        )
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"Domain '{domain}' is already being monitored") from exc
    conn.commit()
    return cur.lastrowid


def list_domains(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM domains ORDER BY domain").fetchall()


def upsert_domain_snapshot(conn: sqlite3.Connection, domain_id: int, snapshot_date: str, **fields: Any) -> None:
    columns = [
        "domain_id",
        "snapshot_date",
        "rdap_status",
        "rdap_expiration",
        "rdap_registrar",
        "ssl_status",
        "ssl_expiration",
        "ssl_days_remaining",
    ]
    values = {
        "domain_id": domain_id,
        "snapshot_date": snapshot_date,
        "rdap_status": fields.get("rdap_status", "unknown"),
        "rdap_expiration": fields.get("rdap_expiration"),
        "rdap_registrar": fields.get("rdap_registrar"),
        "ssl_status": fields.get("ssl_status", "unknown"),
        "ssl_expiration": fields.get("ssl_expiration"),
        "ssl_days_remaining": fields.get("ssl_days_remaining"),
    }
    placeholders = ", ".join("?" for _ in columns)
    update_clause = ", ".join(f"{c}=excluded.{c}" for c in columns if c not in ("domain_id", "snapshot_date"))
    conn.execute(
        f"""
        INSERT INTO domain_snapshots ({', '.join(columns)}) VALUES ({placeholders})
        ON CONFLICT(domain_id, snapshot_date) DO UPDATE SET {update_clause}
        """,
        tuple(values[c] for c in columns),
    )
    conn.commit()


def latest_snapshot(conn: sqlite3.Connection, domain_id: int) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM domain_snapshots WHERE domain_id = ? ORDER BY snapshot_date DESC LIMIT 1",
        (domain_id,),
    ).fetchone()


def snapshot_history(conn: sqlite3.Connection, domain_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM domain_snapshots WHERE domain_id = ? ORDER BY snapshot_date ASC",
        (domain_id,),
    ).fetchall()


def add_manual_renewal(
    conn: sqlite3.Connection,
    title: str,
    category: str,
    due_date: str,
    recurrence: str,
    created_at: str,
    project_label: Optional[str] = None,
    recurrence_n: Optional[int] = None,
) -> int:
    title = title.strip()
    if not title:
        raise ValueError("Renewal title cannot be empty")
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Must be one of: {', '.join(sorted(VALID_CATEGORIES))}")
    if recurrence not in VALID_RECURRENCES:
        raise ValueError(f"Invalid recurrence '{recurrence}'. Must be one of: {', '.join(sorted(VALID_RECURRENCES))}")
    if recurrence == "every-N-months":
        if not recurrence_n or recurrence_n < 1:
            raise ValueError("recurrence_n must be a positive integer when recurrence is 'every-N-months'")
    else:
        recurrence_n = None
    cur = conn.execute(
        """
        INSERT INTO manual_renewals
            (title, category, project_label, due_date, recurrence, recurrence_n, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
        """,
        (title, category, project_label, due_date, recurrence, recurrence_n, created_at),
    )
    conn.commit()
    return cur.lastrowid


def list_manual_renewals(conn: sqlite3.Connection, status: Optional[str] = None) -> list[sqlite3.Row]:
    if status:
        return conn.execute(
            "SELECT * FROM manual_renewals WHERE status = ? ORDER BY due_date ASC", (status,)
        ).fetchall()
    return conn.execute("SELECT * FROM manual_renewals ORDER BY due_date ASC").fetchall()


def get_manual_renewal(conn: sqlite3.Connection, renewal_id: int) -> Optional[sqlite3.Row]:
    return conn.execute("SELECT * FROM manual_renewals WHERE id = ?", (renewal_id,)).fetchone()


def complete_manual_renewal(conn: sqlite3.Connection, renewal_id: int, completed_at: str) -> None:
    conn.execute(
        "UPDATE manual_renewals SET status = 'done', completed_at = ? WHERE id = ?",
        (completed_at, renewal_id),
    )
    conn.commit()

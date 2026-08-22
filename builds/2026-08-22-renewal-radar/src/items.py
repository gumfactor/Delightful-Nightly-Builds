"""Builds the unified list of tracked items (domains, certs, manual renewals)
used by both the `list` and `render` commands, so they can never disagree."""

from __future__ import annotations

import sqlite3
from datetime import date
from typing import Any

from . import db, recurrence, urgency


def build_items(conn: sqlite3.Connection, today: date) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    for domain_row in db.list_domains(conn):
        snapshot = db.latest_snapshot(conn, domain_row["id"])

        rdap_days = None
        rdap_expiration = None
        registrar = None
        if snapshot and snapshot["rdap_status"] == "ok" and snapshot["rdap_expiration"]:
            rdap_expiration = snapshot["rdap_expiration"]
            rdap_days = recurrence.days_until(date.fromisoformat(rdap_expiration), today)
            registrar = snapshot["rdap_registrar"]
        items.append(
            {
                "id": f"domain-rdap-{domain_row['id']}",
                "source": "Domain",
                "title": domain_row["domain"],
                "project_label": domain_row["project_label"],
                "category": "registration",
                "expiration": rdap_expiration,
                "days_remaining": rdap_days,
                "urgency": urgency.classify(rdap_days),
                "detail": registrar or ("not yet synced" if not snapshot else "lookup unavailable"),
            }
        )

        ssl_days = None
        ssl_expiration = None
        if snapshot and snapshot["ssl_status"] == "ok" and snapshot["ssl_expiration"]:
            ssl_expiration = snapshot["ssl_expiration"]
            ssl_days = snapshot["ssl_days_remaining"]
        items.append(
            {
                "id": f"domain-ssl-{domain_row['id']}",
                "source": "SSL",
                "title": domain_row["domain"],
                "project_label": domain_row["project_label"],
                "category": "certificate",
                "expiration": ssl_expiration,
                "days_remaining": ssl_days,
                "urgency": urgency.classify(ssl_days),
                "detail": "not yet synced" if not snapshot else ("live TLS check" if ssl_expiration else "lookup unavailable"),
            }
        )

    for renewal_row in db.list_manual_renewals(conn, status="pending"):
        due = date.fromisoformat(renewal_row["due_date"])
        days = recurrence.days_until(due, today)
        items.append(
            {
                "id": f"manual-{renewal_row['id']}",
                "source": "Manual",
                "title": renewal_row["title"],
                "project_label": renewal_row["project_label"],
                "category": renewal_row["category"],
                "expiration": renewal_row["due_date"],
                "days_remaining": days,
                "urgency": urgency.classify(days),
                "detail": renewal_row["recurrence"],
            }
        )

    return items


def build_domain_histories(conn: sqlite3.Connection) -> dict[str, list[dict[str, Any]]]:
    histories: dict[str, list[dict[str, Any]]] = {}
    for domain_row in db.list_domains(conn):
        history = db.snapshot_history(conn, domain_row["id"])
        histories[domain_row["domain"]] = [
            {"date": row["snapshot_date"], "ssl_days_remaining": row["ssl_days_remaining"]} for row in history
        ]
    return histories

#!/usr/bin/env python3
"""Renewal Radar — domain, SSL certificate, and manual admin renewal tracker.

Usage:
    python3 renewal_radar.py add-domain --domain example.com [--project "Label"]
    python3 renewal_radar.py sync
    python3 renewal_radar.py add-renewal --title "..." --category license \
        --due-date 2027-01-01 --recurrence annual [--recurrence-n N] [--project "Label"]
    python3 renewal_radar.py complete --id 3
    python3 renewal_radar.py list
    python3 renewal_radar.py render [--output data/dashboard.html]
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src import ai_briefing, db, items, rdap, recurrence, render, tls, urgency

BUILD_DIR = Path(__file__).parent
DEFAULT_DB_PATH = BUILD_DIR / "data" / "renewal_radar.db"
DEFAULT_DASHBOARD_PATH = BUILD_DIR / "data" / "dashboard.html"


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def cmd_add_domain(args: argparse.Namespace, conn) -> int:
    try:
        domain_id = db.add_domain(conn, args.domain, args.project, _now_iso())
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Added domain '{args.domain}' (id={domain_id}) for monitoring.")
    return 0


def cmd_sync(args: argparse.Namespace, conn) -> int:
    domains = db.list_domains(conn)
    if not domains:
        print("No domains registered yet. Use 'add-domain' first.")
        return 0

    today = _today()
    snapshot_date = today.isoformat()
    for domain_row in domains:
        domain = domain_row["domain"]
        print(f"Syncing {domain} ...")
        rdap_result = rdap.lookup_domain(domain)
        ssl_result = tls.check_certificate(domain, today=today)

        db.upsert_domain_snapshot(
            conn,
            domain_row["id"],
            snapshot_date,
            rdap_status=rdap_result["status"],
            rdap_expiration=rdap_result["expiration"],
            rdap_registrar=rdap_result["registrar"],
            ssl_status=ssl_result["status"],
            ssl_expiration=ssl_result["expiration"],
            ssl_days_remaining=ssl_result["days_remaining"],
        )

        if rdap_result["status"] == "unknown":
            print(f"  RDAP: unknown ({rdap_result['error']})")
        else:
            print(f"  RDAP: expires {rdap_result['expiration']}")
        if ssl_result["status"] == "unknown":
            print(f"  SSL:  unknown ({ssl_result['error']})")
        else:
            print(f"  SSL:  expires {ssl_result['expiration']} ({ssl_result['days_remaining']} days)")

    print(f"Sync complete for {len(domains)} domain(s).")
    return 0


def cmd_add_renewal(args: argparse.Namespace, conn) -> int:
    try:
        renewal_id = db.add_manual_renewal(
            conn,
            title=args.title,
            category=args.category,
            due_date=args.due_date,
            recurrence=args.recurrence,
            created_at=_now_iso(),
            project_label=args.project,
            recurrence_n=args.recurrence_n,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Added renewal '{args.title}' (id={renewal_id}), due {args.due_date}.")
    return 0


def cmd_complete(args: argparse.Namespace, conn) -> int:
    renewal_row = db.get_manual_renewal(conn, args.id)
    if renewal_row is None:
        print(f"Error: no renewal with id={args.id}", file=sys.stderr)
        return 1
    if renewal_row["status"] == "done":
        print(f"Renewal '{renewal_row['title']}' (id={args.id}) is already marked done.")
        return 0

    now = _now_iso()
    db.complete_manual_renewal(conn, args.id, now)

    due = date.fromisoformat(renewal_row["due_date"])
    next_due = recurrence.next_occurrence(due, renewal_row["recurrence"], renewal_row["recurrence_n"])
    if next_due is None:
        print(f"Completed '{renewal_row['title']}' (one-time; no further occurrence).")
        return 0

    new_id = db.add_manual_renewal(
        conn,
        title=renewal_row["title"],
        category=renewal_row["category"],
        due_date=next_due.isoformat(),
        recurrence=renewal_row["recurrence"],
        created_at=now,
        project_label=renewal_row["project_label"],
        recurrence_n=renewal_row["recurrence_n"],
    )
    print(f"Completed '{renewal_row['title']}'. Next occurrence scheduled {next_due.isoformat()} (id={new_id}).")
    return 0


def cmd_list(args: argparse.Namespace, conn) -> int:
    today = _today()
    tracked_items = items.build_items(conn, today)
    if not tracked_items:
        print("Nothing tracked yet. Use 'add-domain' or 'add-renewal' to get started.")
        return 0

    buckets: dict[str, list] = {bucket: [] for bucket in urgency.BUCKETS}
    for item in tracked_items:
        buckets[item["urgency"]].append(item)

    for bucket in urgency.BUCKETS:
        bucket_items = buckets[bucket]
        if not bucket_items:
            continue
        print(f"\n=== {bucket} ({len(bucket_items)}) ===")
        for item in bucket_items:
            days_str = "?" if item["days_remaining"] is None else f"{item['days_remaining']}d"
            project = f" [{item['project_label']}]" if item["project_label"] else ""
            print(f"  [{item['source']}] {item['title']}{project} — {item['category']} — {days_str}")
    return 0


def cmd_render(args: argparse.Namespace, conn) -> int:
    today = _today()
    tracked_items = items.build_items(conn, today)
    domain_histories = items.build_domain_histories(conn)

    briefing_input = [
        {"title": item["title"], "category": item["category"], "urgency": item["urgency"]} for item in tracked_items
    ]
    briefing_text, used_ai = ai_briefing.generate_briefing(briefing_input)

    html = render.render_dashboard(
        items=tracked_items,
        briefing_text=briefing_text,
        used_ai=used_ai,
        domain_histories=domain_histories,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    output_path = Path(args.output) if args.output else DEFAULT_DASHBOARD_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Dashboard written to {output_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Renewal Radar — domain, SSL, and admin renewal tracker")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to the SQLite database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_domain = subparsers.add_parser("add-domain", help="Register a domain to monitor")
    add_domain.add_argument("--domain", required=True)
    add_domain.add_argument("--project", default=None)
    add_domain.set_defaults(func=cmd_add_domain)

    sync_parser = subparsers.add_parser("sync", help="Check all monitored domains via RDAP + live TLS")
    sync_parser.set_defaults(func=cmd_sync)

    add_renewal = subparsers.add_parser("add-renewal", help="Add a manually-tracked admin renewal")
    add_renewal.add_argument("--title", required=True)
    add_renewal.add_argument("--category", required=True, choices=sorted(db.VALID_CATEGORIES))
    add_renewal.add_argument("--due-date", required=True, dest="due_date", help="ISO date, YYYY-MM-DD")
    add_renewal.add_argument("--recurrence", required=True, choices=sorted(db.VALID_RECURRENCES))
    add_renewal.add_argument("--recurrence-n", type=int, default=None, dest="recurrence_n")
    add_renewal.add_argument("--project", default=None)
    add_renewal.set_defaults(func=cmd_add_renewal)

    complete_parser = subparsers.add_parser("complete", help="Mark a manual renewal done and schedule its next occurrence")
    complete_parser.add_argument("--id", type=int, required=True)
    complete_parser.set_defaults(func=cmd_complete)

    list_parser = subparsers.add_parser("list", help="List all tracked items grouped by urgency")
    list_parser.set_defaults(func=cmd_list)

    render_parser = subparsers.add_parser("render", help="Generate the HTML dashboard")
    render_parser.add_argument("--output", default=None)
    render_parser.set_defaults(func=cmd_render)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    conn = db.connect(Path(args.db))
    try:
        return args.func(args, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())

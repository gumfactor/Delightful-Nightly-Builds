"""Manuscript Pipeline CLI.

Usage:
    python src/main.py add --title "..." --authors "..." --journal "..." \\
        --type original-research --submitted 2026-08-01
    python src/main.py list
    python src/main.py update <id> --status revise_resubmit --deadline 2026-09-01
    python src/main.py capture <id> --text "..."   (or pipe via stdin)
    python src/main.py sync
    python src/main.py report [--out report.html]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import crossref, db, parsing, render

DEFAULT_DB_PATH = str(Path(__file__).resolve().parent.parent / "manuscripts.db")


def cmd_add(args: argparse.Namespace, conn) -> None:
    manuscript_id = db.add_manuscript(
        conn,
        title=args.title,
        authors=args.authors,
        journal=args.journal,
        manuscript_type=args.type,
        submitted_date=args.submitted,
        expected_review_days=args.expected_days,
    )
    print(f"Added manuscript #{manuscript_id}: {args.title}")


def cmd_list(args: argparse.Namespace, conn) -> None:
    manuscripts = db.list_manuscripts(conn)
    print(render.render_terminal(manuscripts))


def cmd_update(args: argparse.Namespace, conn) -> None:
    try:
        db.update_status(
            conn,
            manuscript_id=args.id,
            status=args.status,
            note=args.note,
            source="manual",
            revision_deadline=args.deadline,
        )
        print(f"Manuscript #{args.id} -> {args.status}")
    except (db.ManuscriptNotFoundError, db.InvalidStatusError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_capture(args: argparse.Namespace, conn) -> None:
    try:
        db.get_manuscript(conn, args.id)
    except db.ManuscriptNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    text = args.text if args.text is not None else sys.stdin.read()
    result = parsing.extract(text)

    if not result.get("decision"):
        print("Could not confidently determine a decision from the supplied text.")
        return

    db.update_status(
        conn,
        manuscript_id=args.id,
        status=result["decision"],
        note=f"Captured from pasted text (source: {result['source']}).",
        source=result["source"],
        revision_deadline=result.get("revision_deadline"),
    )
    print(f"Manuscript #{args.id} -> {result['decision']} (via {result['source']})")


def cmd_sync(args: argparse.Namespace, conn) -> None:
    manuscripts = db.list_manuscripts(conn)
    updated = 0
    for m in manuscripts:
        if m["status"] in db.TERMINAL_STATUSES:
            continue
        match = crossref.find_publication_match(m["title"], m["authors"])
        if match:
            db.update_status(
                conn,
                manuscript_id=m["id"],
                status="published",
                note=f"Auto-detected via Crossref (similarity={match['similarity']:.2f}).",
                source="sync",
                doi=match["doi"],
                published_date=match["published_date"],
            )
            print(f"Manuscript #{m['id']} '{m['title']}' -> published (DOI: {match['doi']})")
            updated += 1
    if updated == 0:
        print("No new publications detected.")


def cmd_report(args: argparse.Namespace, conn) -> None:
    manuscripts = db.list_manuscripts(conn)
    print(render.render_terminal(manuscripts))
    html_output = render.render_html(manuscripts)
    out_path = Path(args.out)
    out_path.write_text(html_output, encoding="utf-8")
    print(f"\nHTML report written to {out_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manuscript Pipeline tracker")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to the SQLite database file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_add = subparsers.add_parser("add", help="Register a new manuscript")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--authors", required=True, help="Comma-separated, first = corresponding author")
    p_add.add_argument("--journal", required=True)
    p_add.add_argument("--type", dest="type", default="original-research", choices=db.VALID_TYPES)
    p_add.add_argument("--submitted", required=True, help="ISO date YYYY-MM-DD")
    p_add.add_argument("--expected-days", dest="expected_days", type=int, default=90)
    p_add.set_defaults(func=cmd_add)

    p_list = subparsers.add_parser("list", help="List all manuscripts")
    p_list.set_defaults(func=cmd_list)

    p_update = subparsers.add_parser("update", help="Manually update a manuscript's status")
    p_update.add_argument("id", type=int)
    p_update.add_argument("--status", required=True, choices=db.VALID_STATUSES)
    p_update.add_argument("--note", default=None)
    p_update.add_argument("--deadline", default=None, help="ISO date, for revise_resubmit")
    p_update.set_defaults(func=cmd_update)

    p_capture = subparsers.add_parser("capture", help="Extract a decision from a pasted email")
    p_capture.add_argument("id", type=int)
    p_capture.add_argument("--text", default=None, help="Email text (or pipe via stdin)")
    p_capture.set_defaults(func=cmd_capture)

    p_sync = subparsers.add_parser("sync", help="Check Crossref for newly published manuscripts")
    p_sync.set_defaults(func=cmd_sync)

    p_report = subparsers.add_parser("report", help="Render terminal + HTML report")
    p_report.add_argument("--out", default="report.html")
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    conn = db.connect(args.db)
    try:
        args.func(args, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

"""Command-line interface for Deadline Guardian."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime

from . import db, extraction, render
from .db import VALID_CATEGORIES
from .recurrence import VALID_RECURRENCES

DEFAULT_DB_PATH = os.path.join("data", "deadlines.db")
DEFAULT_OUTPUT_PATH = "dashboard.html"


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"'{value}' is not a valid date — expected YYYY-MM-DD"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deadline_guardian",
        description="Track recurring academic/research administrative deadlines.",
    )
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to the SQLite database file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Manually add a deadline")
    add_parser.add_argument("--title", required=True)
    add_parser.add_argument("--category", required=True, choices=VALID_CATEGORIES)
    add_parser.add_argument("--due-date", required=True, type=_parse_date)
    add_parser.add_argument("--recurrence", default="none", choices=VALID_RECURRENCES)
    add_parser.add_argument("--recurrence-months", type=int, default=None)
    add_parser.add_argument("--notes", default=None)

    capture_parser = subparsers.add_parser(
        "capture", help="Extract a deadline from pasted/piped/file text via AI or fallback parsing"
    )
    capture_group = capture_parser.add_mutually_exclusive_group()
    capture_group.add_argument("--text", default=None, help="Raw text to parse")
    capture_group.add_argument("--file", default=None, help="Path to a text file to parse")
    capture_parser.add_argument("--json", action="store_true", dest="as_json")

    complete_parser = subparsers.add_parser("complete", help="Mark a deadline complete")
    complete_parser.add_argument("--id", required=True, type=int, dest="deadline_id")
    complete_parser.add_argument("--on", default=None, type=_parse_date, help="Completion date override")
    complete_parser.add_argument("--json", action="store_true", dest="as_json")

    list_parser = subparsers.add_parser("list", help="List deadlines")
    list_parser.add_argument("--json", action="store_true", dest="as_json")
    list_parser.add_argument("--include-completed", action="store_true")

    render_parser = subparsers.add_parser("render", help="Render the HTML dashboard")
    render_parser.add_argument("--output", default=DEFAULT_OUTPUT_PATH)

    return parser


def _read_capture_text(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.file is not None:
        with open(args.file, "r", encoding="utf-8") as handle:
            return handle.read()
    return sys.stdin.read()


def _print(payload: dict, as_json: bool, human_message: str) -> None:
    if as_json:
        print(json.dumps(payload, default=str, indent=2))
    else:
        print(human_message)


def cmd_add(args: argparse.Namespace) -> int:
    conn = db.get_connection(args.db)
    deadline_id = db.add_deadline(
        conn,
        title=args.title,
        category=args.category,
        due_date=args.due_date,
        recurrence_rule=args.recurrence,
        recurrence_months=args.recurrence_months,
        notes=args.notes,
        extraction_method="manual",
    )
    print(f"Added deadline #{deadline_id}: {args.title} ({args.category}, due {args.due_date.isoformat()})")
    return 0


def cmd_capture(args: argparse.Namespace) -> int:
    text = _read_capture_text(args)
    if not text.strip():
        print("error: no text supplied (use --text, --file, or pipe text via stdin)", file=sys.stderr)
        return 1

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    try:
        fields, method = extraction.extract_deadline(text, api_key)
    except extraction.NoDateFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    conn = db.get_connection(args.db)
    deadline_id = db.add_deadline(
        conn,
        title=fields["title"],
        category=fields["category"],
        due_date=fields["due_date"],
        recurrence_rule=fields["recurrence"],
        recurrence_months=fields["recurrence_months"],
        notes=fields["notes"],
        source_text=text,
        extraction_method=method,
    )
    result = db.get_deadline(conn, deadline_id)
    _print(
        result,
        args.as_json,
        f"Captured deadline #{deadline_id} via {method} extraction: "
        f"{result['title']} ({result['category']}, due {result['due_date']})",
    )
    return 0


def cmd_complete(args: argparse.Namespace) -> int:
    conn = db.get_connection(args.db)
    try:
        completed, next_deadline = db.complete_deadline(conn, args.deadline_id, args.on)
    except db.DeadlineNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except db.AlreadyCompletedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    message = f"Completed #{completed['id']}: {completed['title']}"
    if next_deadline:
        message += f" — next occurrence #{next_deadline['id']} due {next_deadline['due_date']}"
    _print({"completed": completed, "next": next_deadline}, args.as_json, message)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    conn = db.get_connection(args.db)
    deadlines = db.list_deadlines(conn, include_completed=args.include_completed)
    if args.as_json:
        print(json.dumps(deadlines, default=str, indent=2))
        return 0
    if not deadlines:
        print("No deadlines found.")
        return 0
    for d in deadlines:
        flag = "[done] " if d["completed"] else ""
        print(f"#{d['id']} {flag}{d['title']} — {d['category']} — due {d['due_date']}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    conn = db.get_connection(args.db)
    deadlines = db.list_deadlines(conn, include_completed=True)
    html = render.render_dashboard(deadlines)
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(html)
    print(f"Dashboard written to {args.output}")
    return 0


COMMANDS = {
    "add": cmd_add,
    "capture": cmd_capture,
    "complete": cmd_complete,
    "list": cmd_list,
    "render": cmd_render,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return COMMANDS[args.command](args)


if __name__ == "__main__":
    sys.exit(main())

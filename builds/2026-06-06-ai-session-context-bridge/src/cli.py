"""CLI command implementations and argument parser for ctxlog."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .journal import Journal
from .storage import Storage
from .search import search_sessions
from .handoff import generate_handoff


def _get_journal(data_dir: Path) -> Journal:
    return Journal(Storage(data_dir / "sessions.json"))


def cmd_add(args: argparse.Namespace, data_dir: Path) -> None:
    """Capture a new AI session context entry, interactively or via flags."""
    tty = sys.stdin.isatty()

    project: str = args.project or (input("Project name: ").strip() if tty else "")
    summary: str = args.summary or (input("What were you working on? ").strip() if tty else "")

    if not project or not summary:
        print(
            "Error: --project and --summary are required in non-interactive mode.",
            file=sys.stderr,
        )
        sys.exit(1)

    context: str = args.context
    if not context and tty:
        context = input("Key state / context at end of session (Enter to skip): ").strip()

    next_steps = list(args.next_steps or [])
    if not next_steps and tty:
        print("Next steps (one per line, blank line to finish):")
        while True:
            step = input("  > ").strip()
            if not step:
                break
            next_steps.append(step)

    files = list(args.files or [])
    if not files and tty:
        print("Files being worked on (one per line, blank line to finish):")
        while True:
            f = input("  > ").strip()
            if not f:
                break
            files.append(f)

    tags = list(args.tags or [])

    journal = _get_journal(data_dir)
    session = journal.add_session(
        project=project,
        summary=summary,
        context=context,
        next_steps=next_steps,
        files=files,
        tags=tags,
    )
    print(f"Saved [{session.id}]  {session.project} — {session.summary}")


def cmd_list(args: argparse.Namespace, data_dir: Path) -> None:
    """List recent sessions, optionally filtered by project or date."""
    journal = _get_journal(data_dir)
    sessions = journal.list_sessions(
        project=args.project,
        limit=args.limit,
        today_only=args.today,
    )

    if not sessions:
        print("No sessions found.")
        return

    for s in sessions:
        tag_str = f"  [{', '.join(s.tags)}]" if s.tags else ""
        print(f"[{s.id}]  {s.timestamp[:10]}  {s.project}{tag_str}")
        print(f"  {s.summary}")
        if s.next_steps:
            ellipsis = " ..." if len(s.next_steps) > 1 else ""
            print(f"  → {s.next_steps[0]}{ellipsis}")
        print()


def cmd_search(args: argparse.Namespace, data_dir: Path) -> None:
    """Full-text search across all session fields."""
    journal = _get_journal(data_dir)
    all_sessions = journal.storage.load_all()
    results = search_sessions(all_sessions, args.query, project=args.project)

    if not results:
        print(f"No sessions found matching '{args.query}'.")
        return

    print(f"Found {len(results)} session(s) matching '{args.query}':\n")
    for s in results:
        print(f"[{s.id}]  {s.timestamp[:10]}  {s.project}")
        print(f"  {s.summary}")
        print()


def cmd_handoff(args: argparse.Namespace, data_dir: Path) -> None:
    """Generate a markdown handoff document for the next AI session."""
    journal = _get_journal(data_dir)
    all_sessions = journal.storage.load_all()
    output = generate_handoff(all_sessions, project=args.project, n_sessions=args.sessions)
    print(output)


def cmd_projects(args: argparse.Namespace, data_dir: Path) -> None:
    """List all tracked projects with session counts."""
    journal = _get_journal(data_dir)
    projects = journal.get_projects()

    if not projects:
        print("No projects recorded yet.")
        return

    all_sessions = journal.storage.load_all()
    for proj in projects:
        count = sum(1 for s in all_sessions if s.project == proj)
        noun = "session" if count == 1 else "sessions"
        print(f"  {proj}  ({count} {noun})")


def cmd_show(args: argparse.Namespace, data_dir: Path) -> None:
    """Display full detail for a specific session by its short ID."""
    journal = _get_journal(data_dir)
    session = journal.get_session(args.id)

    if not session:
        print(f"Session '{args.id}' not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Session:   {session.id}")
    print(f"Project:   {session.project}")
    print(f"Time:      {session.timestamp}")
    print(f"Summary:   {session.summary}")
    if session.context:
        print(f"Context:   {session.context}")
    if session.next_steps:
        print("Next steps:")
        for step in session.next_steps:
            print(f"  - {step}")
    if session.files:
        print("Files:")
        for f in session.files:
            print(f"  - {f}")
    if session.tags:
        print(f"Tags:      {', '.join(session.tags)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ctxlog",
        description="AI session context bridge — capture and retrieve AI coding session state",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 main.py add --project canada-list --summary 'Fixed CSV parser'\n"
            "  python3 main.py list --project canada-list\n"
            "  python3 main.py search 'csv'\n"
            "  python3 main.py handoff --project canada-list\n"
            "  python3 main.py projects\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    add_p = sub.add_parser("add", help="Capture a new AI session context entry")
    add_p.add_argument("--project", "-p", help="Project name")
    add_p.add_argument("--summary", "-s", help="What were you working on?")
    add_p.add_argument("--context", "-c", default="", help="Key state at end of session")
    add_p.add_argument(
        "--next-steps", "-n", nargs="+", metavar="STEP",
        dest="next_steps", help="Next steps (multiple values accepted)"
    )
    add_p.add_argument(
        "--files", "-f", nargs="+", metavar="FILE",
        help="Files being worked on (multiple values accepted)"
    )
    add_p.add_argument(
        "--tags", "-t", nargs="+", metavar="TAG",
        help="Tags (multiple values accepted)"
    )

    # list
    list_p = sub.add_parser("list", help="List recent sessions")
    list_p.add_argument("--project", "-p", help="Filter by project name")
    list_p.add_argument("--limit", "-l", type=int, default=10, help="Max sessions to show (default: 10)")
    list_p.add_argument("--today", action="store_true", help="Show only today's sessions")

    # search
    search_p = sub.add_parser("search", help="Search sessions by keyword")
    search_p.add_argument("query", help="Search query (case-insensitive substring)")
    search_p.add_argument("--project", "-p", help="Restrict search to a specific project")

    # handoff
    handoff_p = sub.add_parser("handoff", help="Generate a markdown handoff document")
    handoff_p.add_argument("--project", "-p", help="Filter to a specific project")
    handoff_p.add_argument(
        "--sessions", "-n", type=int, default=3,
        help="Number of recent sessions to include (default: 3)"
    )

    # projects
    sub.add_parser("projects", help="List all tracked projects")

    # show
    show_p = sub.add_parser("show", help="Show full details for a session")
    show_p.add_argument("id", help="Session short ID (e.g. a3f1b2c4)")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    data_dir = Path(__file__).parent.parent / "data"

    dispatch = {
        "add": cmd_add,
        "list": cmd_list,
        "search": cmd_search,
        "handoff": cmd_handoff,
        "projects": cmd_projects,
        "show": cmd_show,
    }
    dispatch[args.command](args, data_dir)

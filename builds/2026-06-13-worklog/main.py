"""
worklog — Cross-Agent Project Activity Workstreams
Entry point: python3 main.py <command> [options]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def cmd_sync(args: argparse.Namespace, ctx) -> int:
    from src.collectors.git import collect_commits, collect_dirty_state
    from src.collectors.github import collect_github_events
    from src.correlation import correlate_events, build_workstream_records
    from src.ledger import insert_event, upsert_workstream, assign_workstream, init_schema

    init_schema(ctx.db_path)

    since_days = args.since
    print(f"Syncing project '{ctx.project_id}'...")

    # Collect
    git_events = collect_commits(ctx.git_root, ctx.project_id, since_days=since_days)
    dirty_events = collect_dirty_state(ctx.git_root, ctx.project_id)
    github_events, github_ok = collect_github_events(ctx.git_root, ctx.project_id)

    all_new = git_events + dirty_events + github_events

    if not github_ok:
        print("  GitHub: no GITHUB_TOKEN found or remote is not GitHub — skipping")
    else:
        print(f"  GitHub: {len(github_events)} event(s) collected")

    # Store and deduplicate
    inserted = 0
    for evt in all_new:
        if insert_event(ctx.db_path, evt):
            inserted += 1

    print(f"  Git: {len(git_events)} commit(s) + {len(dirty_events)} dirty-tree event(s)")
    print(f"  Stored: {inserted} new event(s) ({len(all_new) - inserted} duplicate(s) skipped)")

    # Correlate all stored events (not just new ones — correlation is stateless)
    from src.ledger import query_events
    all_events = query_events(ctx.db_path, ctx.project_id, limit=1000)
    correlated, ws_meta = correlate_events(all_events)

    # Update workstream assignments
    for evt in correlated:
        if evt.get("workstream_id"):
            assign_workstream(ctx.db_path, evt["id"], evt["workstream_id"])

    ws_records = build_workstream_records(ws_meta, ctx.project_id, correlated)
    for ws in ws_records:
        upsert_workstream(ctx.db_path, ws)

    print(f"  Workstreams: {len(ws_records)} detected")
    print(f"\nDone. Database: {ctx.db_path}")
    return 0


def cmd_checkpoint(args: argparse.Namespace, ctx) -> int:
    from src.checkpoint import load_checkpoint_file, load_checkpoint_stdin
    from src.ledger import insert_event, insert_decision, init_schema

    init_schema(ctx.db_path)

    if args.from_stdin:
        events, decisions = load_checkpoint_stdin()
    elif args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            return 1
        events, decisions = load_checkpoint_file(path)
    else:
        print("Error: provide --file PATH or --from-stdin", file=sys.stderr)
        return 1

    # Inject project_id
    for evt in events:
        evt["project_id"] = ctx.project_id
    for dec in decisions:
        pass  # workstream_id set later by correlation

    evt_inserted = sum(1 for e in events if insert_event(ctx.db_path, e))
    dec_inserted = sum(1 for d in decisions if insert_decision(ctx.db_path, d))

    print(f"Checkpoint ingested: {evt_inserted} event(s), {dec_inserted} decision(s)")
    if evt_inserted == 0:
        print("  (all already in ledger — deduplication applied)")
    return 0


def cmd_standup(args: argparse.Namespace, ctx) -> int:
    from src.views import render_standup
    from src.ledger import init_schema
    init_schema(ctx.db_path)
    print(render_standup(ctx.db_path, ctx.project_id, since_days=args.since))
    return 0


def cmd_resume(args: argparse.Namespace, ctx) -> int:
    from src.views import render_resume
    from src.ledger import init_schema
    init_schema(ctx.db_path)
    print(render_resume(ctx.db_path, ctx.project_id, args.workstream, ctx.git_root))
    return 0


def cmd_why(args: argparse.Namespace, ctx) -> int:
    from src.views import render_why
    from src.ledger import init_schema
    init_schema(ctx.db_path)
    query = " ".join(args.query)
    if not query:
        print("Error: provide a search term, e.g. worklog why 'coercion'", file=sys.stderr)
        return 1
    print(render_why(ctx.db_path, ctx.project_id, query))
    return 0


def cmd_workstreams(args: argparse.Namespace, ctx) -> int:
    from src.views import render_workstreams
    from src.ledger import init_schema
    init_schema(ctx.db_path)
    print(render_workstreams(ctx.db_path, ctx.project_id))
    return 0


def cmd_events(args: argparse.Namespace, ctx) -> int:
    from src.views import render_events
    from src.ledger import init_schema
    init_schema(ctx.db_path)
    print(render_events(
        ctx.db_path,
        ctx.project_id,
        since_days=args.since,
        event_type=args.type,
        workstream_id=args.workstream,
    ))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="worklog",
        description="Cross-agent project activity workstreams",
    )
    parser.add_argument(
        "--cwd",
        metavar="DIR",
        help="Repository root (defaults to current directory)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # sync
    p_sync = sub.add_parser("sync", help="Collect Git + GitHub events into the ledger")
    p_sync.add_argument("--since", type=int, default=30, metavar="DAYS",
                        help="Collect commits from the last N days (default: 30)")

    # checkpoint
    p_ckpt = sub.add_parser("checkpoint", help="Ingest an agent checkpoint YAML")
    grp = p_ckpt.add_mutually_exclusive_group()
    grp.add_argument("--file", metavar="PATH", help="Path to checkpoint YAML file")
    grp.add_argument("--from-stdin", action="store_true", help="Read checkpoint from stdin")

    # standup
    p_stand = sub.add_parser("standup", help="Show standup report for recent activity")
    p_stand.add_argument("--since", type=int, default=1, metavar="DAYS",
                         help="Look back N days (default: 1)")

    # resume
    p_resume = sub.add_parser("resume", help="Show resumption brief for a workstream")
    p_resume.add_argument("workstream", nargs="?", help="Workstream ID (omit for latest)")

    # why
    p_why = sub.add_parser("why", help="Search decision history by keyword")
    p_why.add_argument("query", nargs="+", help="Search terms")

    # workstreams
    sub.add_parser("workstreams", help="List all detected workstreams")

    # events
    p_events = sub.add_parser("events", help="Show raw events from the ledger")
    p_events.add_argument("--since", type=int, metavar="DAYS", help="Last N days only")
    p_events.add_argument("--type", metavar="TYPE", help="Filter by event type")
    p_events.add_argument("--workstream", metavar="WS_ID", help="Filter by workstream ID")

    return parser


COMMANDS = {
    "sync": cmd_sync,
    "checkpoint": cmd_checkpoint,
    "standup": cmd_standup,
    "resume": cmd_resume,
    "why": cmd_why,
    "workstreams": cmd_workstreams,
    "events": cmd_events,
}


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    from src.config import ProjectContext
    try:
        ctx = ProjectContext.resolve(cwd=args.cwd)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    handler = COMMANDS.get(args.command)
    if not handler:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        sys.exit(1)

    try:
        code = handler(args, ctx)
        sys.exit(code or 0)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

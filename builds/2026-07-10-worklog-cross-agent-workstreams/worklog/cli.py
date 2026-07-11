"""Command-line interface for worklog."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from . import views
from .checkpoint import CheckpointValidationError, validate_checkpoint
from .checkpoint_ingest import ingest_checkpoint
from .ledger import Ledger
from .project import NotAGitRepoError, discover_project
from .sync import default_data_dir, run_sync


def _open_ledger(repo_path: str, data_dir: Optional[str]):
    project = discover_project(repo_path)
    resolved_data_dir = data_dir or default_data_dir(project.repo_root)
    ledger = Ledger(resolved_data_dir)
    return project, ledger


def cmd_sync(args: argparse.Namespace) -> int:
    try:
        result = run_sync(args.repo, data_dir=args.data_dir, use_github=not args.no_github)
    except NotAGitRepoError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Project: {result.project.project_id} (branch {result.project.branch})")
    print(
        f"New events — commits: {result.new_commit_events}, branches: {result.new_branch_events}, "
        f"tags: {result.new_tag_events}, github: {result.new_github_events}"
    )
    if result.github_skipped_reason:
        print(f"GitHub: skipped ({result.github_skipped_reason})")
    print(f"Total new events: {result.total_new_events}")
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    try:
        project, ledger = _open_ledger(args.repo, args.data_dir)
    except NotAGitRepoError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    try:
        with open(args.from_file, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: could not read checkpoint file: {exc}", file=sys.stderr)
        return 1

    try:
        checkpoint = validate_checkpoint(raw)
    except CheckpointValidationError as exc:
        print(f"error: invalid checkpoint: {exc}", file=sys.stderr)
        return 1

    with ledger:
        result = ingest_checkpoint(ledger, project, checkpoint)

    status = "ingested" if result.newly_inserted else "already recorded (no-op)"
    print(f"Checkpoint {status}: {checkpoint.objective}")
    print(f"Workstream: {result.workstream_id}")
    print(f"Decisions recorded: {len(result.decision_event_ids)}")
    return 0


def cmd_workstreams(args: argparse.Namespace) -> int:
    project, ledger = _open_ledger(args.repo, args.data_dir)
    with ledger:
        rows = views.workstreams_view(ledger, project.project_id)
    if not rows:
        print("No workstreams yet. Run `worklog sync` first.")
        return 0
    for row in rows:
        signals = ", ".join(row["signals"]) or "none"
        print(f"{row['id']}  [{row['event_count']} events]  {row['title']}  (signals: {signals})")
    return 0


def cmd_timeline(args: argparse.Namespace) -> int:
    project, ledger = _open_ledger(args.repo, args.data_dir)
    with ledger:
        events = views.timeline(ledger, project.project_id, args.workstream)
    if not events:
        print("No events found.")
        return 0
    for event in events:
        print(f"{event.timestamp}  [{event.type}]  {event.summary}  ({event.id[:10]})")
    return 0


def cmd_standup(args: argparse.Namespace) -> int:
    project, ledger = _open_ledger(args.repo, args.data_dir)
    with ledger:
        report = views.standup(ledger, project.project_id, args.since)

    print(f"Standup — since {args.since}")
    print("\nCompleted:")
    if not report.completed:
        print("  (nothing)")
    for item in report.completed:
        print(f"  - {item['title']}: {item['commit_count']} commit(s) — {item['latest_summary']}")

    print("\nIn progress:")
    if not report.in_progress:
        print("  (nothing)")
    for item in report.in_progress:
        print(f"  - {item['title']}: {item['detail']}")

    print("\nBlocked:")
    if not report.blocked:
        print("  (nothing)")
    for item in report.blocked:
        print(f"  - {item['title']}: {item['reason']}")

    print("\nNext:")
    if not report.next_actions:
        print("  (nothing)")
    for item in report.next_actions:
        print(f"  - {item['title']}: {item['step']}")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    project, ledger = _open_ledger(args.repo, args.data_dir)
    with ledger:
        package = views.resume(ledger, project, args.workstream)

    if package.no_data:
        print("No workstreams recorded yet. Run `worklog sync` first.")
        return 0

    print(f"Workstream: {package.workstream_id}")
    print(f"Objective: {package.objective}")

    if package.head_stale:
        print(f"\n⚠ STALE: {package.head_stale_detail} — run `worklog sync` to refresh.")
    if package.stale_checkpoints:
        print(f"⚠ {len(package.stale_checkpoints)} checkpoint(s) reference commits no longer "
              "reachable from HEAD (likely rebased) — treat their file/commit context as historical.")
    if package.dirty_now or package.untracked_now:
        print(f"\nWorking tree right now: {len(package.dirty_now)} modified, "
              f"{len(package.untracked_now)} untracked")

    if package.decisions:
        print("\nDecisions:")
        for decision in package.decisions:
            print(f"  - {decision['summary']}  ({decision['reason']})")

    if package.unresolved:
        print("\nUnresolved:")
        for item in package.unresolved:
            print(f"  - {item}")

    if package.next_steps:
        print("\nNext steps:")
        for item in package.next_steps:
            print(f"  - {item}")

    if package.files:
        print(f"\nRelevant files ({len(package.files)}):")
        for path in package.files[:20]:
            print(f"  - {path}")

    print(f"\nEvidence: {package.event_count} source event(s).")
    return 0


def cmd_why(args: argparse.Namespace) -> int:
    project, ledger = _open_ledger(args.repo, args.data_dir)
    with ledger:
        results = views.why(ledger, project.project_id, args.query)

    if not results:
        print(f"No decisions found matching {args.query!r}.")
        return 0

    for result in results:
        print(f"Decision: {result.decision_summary}")
        print(f"Reason: {result.reason}")
        print(f"Workstream: {result.workstream_title} ({result.workstream_id})")
        if result.later_events:
            print("Later activity in this workstream:")
            for entry in result.later_events:
                print(f"  - {entry}")
        print()
    return 0


def cmd_show_event(args: argparse.Namespace) -> int:
    project, ledger = _open_ledger(args.repo, args.data_dir)
    with ledger:
        event = views.show_event(ledger, args.event_id)
    if not event:
        print(f"No event found with id {args.event_id!r}", file=sys.stderr)
        return 1
    print(json.dumps(event.__dict__, indent=2, default=str))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    project, ledger = _open_ledger(args.repo, args.data_dir)
    with ledger:
        events = views.search(ledger, project.project_id, args.query)
    if not events:
        print("No matching events.")
        return 0
    for event in events:
        print(f"{event.timestamp}  [{event.type}]  {event.summary}  ({event.id[:10]})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="worklog", description="Cross-agent project activity workstreams")
    parser.add_argument("--repo", default=".", help="Path to the target git repository (default: cwd)")
    parser.add_argument("--data-dir", default=None, help="Ledger storage dir (default: <repo>/.worklog)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Collect git + GitHub activity into the ledger")
    sync_parser.add_argument("--no-github", action="store_true", help="Skip GitHub collection")
    sync_parser.set_defaults(func=cmd_sync)

    checkpoint_parser = subparsers.add_parser("checkpoint", help="Ingest an agent checkpoint file")
    checkpoint_parser.add_argument("--from-file", required=True, help="Path to a checkpoint JSON file")
    checkpoint_parser.set_defaults(func=cmd_checkpoint)

    workstreams_parser = subparsers.add_parser("workstreams", help="List all workstreams")
    workstreams_parser.set_defaults(func=cmd_workstreams)

    timeline_parser = subparsers.add_parser("timeline", help="Show a chronological event timeline")
    timeline_parser.add_argument("workstream", nargs="?", default=None)
    timeline_parser.set_defaults(func=cmd_timeline)

    standup_parser = subparsers.add_parser("standup", help="Completed / in-progress / blocked / next summary")
    standup_parser.add_argument("--since", default="24h")
    standup_parser.set_defaults(func=cmd_standup)

    resume_parser = subparsers.add_parser("resume", help="Context package for a workstream")
    resume_parser.add_argument("workstream", nargs="?", default=None)
    resume_parser.set_defaults(func=cmd_resume)

    why_parser = subparsers.add_parser("why", help="Search recorded decisions")
    why_parser.add_argument("query")
    why_parser.set_defaults(func=cmd_why)

    show_event_parser = subparsers.add_parser("show-event", help="Show the raw event behind a summary")
    show_event_parser.add_argument("event_id")
    show_event_parser.set_defaults(func=cmd_show_event)

    search_parser = subparsers.add_parser("search", help="Search all events")
    search_parser.add_argument("query")
    search_parser.set_defaults(func=cmd_search)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except NotAGitRepoError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Command-line interface."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional

from . import checkpoint, freshness, ghcollect, gitcollect, views
from .correlate import Workstream, correlate, find_workstream
from .hook import run_hook
from .ledger import Ledger, make_event, utc_now
from .project import Project, WorklogError, discover


def open_ledger(project: Project) -> Ledger:
    override = os.environ.get("WORKLOG_DB")
    return Ledger(Path(override) if override else project.git_dir / "worklog" / "ledger.db")


def load(project: Project, ledger: Ledger) -> list[Workstream]:
    return correlate(ledger.events(project.project_id), ledger.overrides(project.project_id))


def resolve_ws(workstreams: list[Workstream], query: Optional[str]) -> Workstream:
    if query:
        ws = find_workstream(workstreams, query)
        if ws is None:
            raise WorklogError(f"no unique workstream matches {query!r} (see `worklog workstreams`)")
        return ws
    active = [w for w in workstreams if w.status != "completed"] or workstreams
    if not active:
        raise WorklogError("no workstreams yet; run `worklog sync` first")
    return active[0]


def emit(args: argparse.Namespace, data, text: str) -> None:
    sys.stdout.write(json.dumps(data, indent=2, default=str) + "\n" if args.json else text)


# ---- commands ---------------------------------------------------------------------------------------

def cmd_sync(args, project, ledger) -> None:
    events, state = gitcollect.collect(project, args.since)
    excluded = set(project.config.exclude_providers)
    events = [e for e in events if e["provider"] not in excluded]
    counts = ledger.ingest(events)
    previous = ledger.load_state(project.project_id) or {}
    state["last_github_sync"] = previous.get("last_github_sync")
    lines = [f"git: {counts['inserted']} new, {counts['unchanged']} unchanged"]
    if args.no_github or "github" in excluded:
        lines.append("github: skipped (Git-only mode)")
    else:
        try:
            gh_counts = ledger.ingest(ghcollect.collect(project, since=args.since))
            state["last_github_sync"] = utc_now()
            lines.append(f"github: {gh_counts['inserted']} new, {gh_counts['unchanged']} unchanged")
        except ghcollect.GitHubUnavailable as exc:
            lines.append(f"github: skipped ({exc}); continuing in Git-only mode")
    ledger.save_state(project.project_id, state)
    lines.append(f"ledger: {ledger.count(project.project_id)} events for {project.project_id}")
    emit(args, {"git": counts, "lines": lines}, "\n".join(lines) + "\n")


def cmd_checkpoint(args, project, ledger) -> None:
    if args.from_file:
        raw = checkpoint.load_file(Path(args.from_file))
    else:
        try:
            raw = json.loads(sys.stdin.read())
        except json.JSONDecodeError as exc:
            raise WorklogError(f"stdin is not valid JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise WorklogError("checkpoint must be a JSON object")
    result = checkpoint.capture(project, ledger, raw)
    emit(args, result, f"checkpoint {result['checkpoint_id']} recorded ({result['status']}, "
                       f"{result['decisions']} decision(s))\n")


def cmd_note(args, project, ledger) -> None:
    keys = []
    if args.workstream:
        ws = resolve_ws(load(project, ledger), args.workstream)
        keys.append(f"evt:{ws.events[0]['id']}")
    now = utc_now()
    digest = hashlib.sha1(args.text.encode()).hexdigest()[:8]
    metadata = {"reason": args.reason, "rejected": args.rejected or [], "supersedes": args.supersedes}
    event = make_event(ts=now, project_id=project.project_id, etype=args.type, provider="manual",
                       ref=f"manual:{now}:{digest}", summary=args.text, actor_kind="human", actor_name="user",
                       status="open" if args.type == "blocker" else "completed", keys=keys,
                       files=args.files or [], metadata=metadata)
    ledger.ingest([event])
    emit(args, {"id": event["id"]}, f"recorded {args.type} {event['id']}\n")


def cmd_workstreams(args, project, ledger) -> None:
    workstreams = load(project, ledger)
    if args.status:
        workstreams = [w for w in workstreams if w.status == args.status]
    if args.provider:
        workstreams = [w for w in workstreams if any(e["provider"] == args.provider for e in w.events)]
    if args.actor:
        workstreams = [w for w in workstreams if any(e["actor_kind"] == args.actor for e in w.events)]
    if args.since:
        cutoff = views.parse_since(args.since)
        workstreams = [w for w in workstreams if w.last_ts >= cutoff]
    emit(args, [{"id": w.id, "title": w.title, "status": w.status, "last": w.last_ts, "events": len(w.events)}
                for w in workstreams], views.render_workstreams(workstreams))


def cmd_timeline(args, project, ledger) -> None:
    ws = resolve_ws(load(project, ledger), args.workstream)
    emit(args, {"id": ws.id, "events": ws.events, "links": [vars(ln) for ln in ws.links],
                "suggestions": [vars(s) for s in ws.suggestions]}, views.render_timeline(ws))


def cmd_standup(args, project, ledger) -> None:
    since = views.parse_since(args.since)
    workstreams = load(project, ledger)
    findings = {w.id: freshness.check(project, w) for w in workstreams if w.last_ts >= since}
    data = views.standup_data(workstreams, findings, since)
    emit(args, data, views.render_standup(data, since))


def cmd_resume(args, project, ledger) -> None:
    ws = resolve_ws(load(project, ledger), args.workstream)
    state = ledger.load_state(project.project_id) or {}
    data = views.resume_data(ws, freshness.check(project, ws), gitcollect.working_state(project),
                             state.get("last_github_sync"))
    emit(args, data, views.render_resume(data))


def cmd_why(args, project, ledger) -> None:
    workstreams = load(project, ledger)
    only = resolve_ws(workstreams, args.workstream) if args.workstream else None
    data = views.why_data(workstreams, args.query, only)
    emit(args, data, views.render_why(data))


def cmd_search(args, project, ledger) -> None:
    term = args.term.lower()
    owner = {e["id"]: w.id for w in load(project, ledger) for e in w.events}
    hits = []
    for event in ledger.events(project.project_id, etype=args.type, provider=args.provider):
        blob = " ".join([event["summary"], event["ref"], " ".join(event["files"]), json.dumps(event["metadata"])]).lower()
        if term in blob:
            hits.append({"id": event["id"], "ts": event["ts"], "type": event["type"], "summary": event["summary"],
                         "workstream": owner.get(event["id"])})
    text = "".join(f"{h['ts']}  {h['type']:<10} {h['id'][:12]}  {h['workstream']}  {h['summary']}\n" for h in hits)
    emit(args, hits, text or "no matches\n")


def cmd_show_event(args, project, ledger) -> None:
    event = ledger.get_event(args.event)
    if event is None or event["project_id"] != project.project_id:
        raise WorklogError(f"no unique event matches {args.event!r}")
    owner = next((w.id for w in load(project, ledger) if any(e["id"] == event["id"] for e in w.events)), None)
    sys.stdout.write(json.dumps({**event, "workstream": owner}, indent=2) + "\n")


def _event_of(project, ledger, prefix: str) -> dict:
    event = ledger.get_event(prefix)
    if event is None or event["project_id"] != project.project_id:
        raise WorklogError(f"no unique event matches {prefix!r}")
    return event


def cmd_merge(args, project, ledger) -> None:
    workstreams = load(project, ledger)
    anchors = [resolve_ws(workstreams, q).events[0]["id"] for q in args.workstreams]
    ledger.add_override(project.project_id, "merge", {"events": anchors})
    sys.stdout.write(f"merged {len(anchors)} workstreams\n")


def cmd_split(args, project, ledger) -> None:
    event = _event_of(project, ledger, args.event)
    ledger.add_override(project.project_id, "split", {"event": event["id"]})
    sys.stdout.write(f"event {event['id']} detached into its own workstream\n")


def cmd_rename(args, project, ledger) -> None:
    ws = resolve_ws(load(project, ledger), args.workstream)
    ledger.add_override(project.project_id, "rename", {"event": ws.events[0]["id"], "title": args.title})
    sys.stdout.write(f"renamed {ws.id} to {args.title!r}\n")


def cmd_resolve(args, project, ledger) -> None:
    event = _event_of(project, ledger, args.event)
    ledger.add_override(project.project_id, "resolve", {"event": event["id"]})
    sys.stdout.write(f"marked {event['id']} resolved\n")


def cmd_purge(args, project, ledger) -> None:
    if not args.yes:
        raise WorklogError("purge deletes every recorded event for this project; re-run with --yes")
    sys.stdout.write(f"deleted {ledger.purge(project.project_id)} events (rebuild with `worklog sync`)\n")


def cmd_hook(args) -> int:
    """Stop/SessionEnd hook. Never fails the agent: problems go to stderr, exit code stays 0."""
    text = sys.stdin.read()
    try:
        payload = json.loads(text)
        cwd = payload.get("cwd") if isinstance(payload, dict) else None
        project = discover(Path(cwd or args.C))
        ledger = open_ledger(project)
        try:
            result = run_hook(project, ledger, text)
        finally:
            ledger.close()
        sys.stdout.write(f"worklog: checkpoint {result['checkpoint_id']} updated\n")
    except (WorklogError, json.JSONDecodeError, OSError) as exc:
        sys.stderr.write(f"worklog hook skipped: {exc}\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="worklog", description="Evidence-backed project workstreams from Git, "
                                     "GitHub and AI-agent checkpoints.")
    parser.add_argument("-C", default=".", metavar="DIR", help="project directory (default: current)")
    parser.add_argument("--json", action="store_true", help="machine-readable output where supported")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("sync", help="collect Git (+GitHub) activity into the ledger")
    p.add_argument("--since", help="only fetch recent activity, e.g. 30d or 2026-09-01")
    p.add_argument("--no-github", action="store_true")
    p.set_defaults(func=cmd_sync)

    p = sub.add_parser("checkpoint", help="record an agent checkpoint (JSON/YAML file or stdin JSON)")
    p.add_argument("--from-file")
    p.set_defaults(func=cmd_checkpoint)

    sub.add_parser("hook", help="Claude Code Stop/SessionEnd hook: read payload on stdin").set_defaults(hook=True)

    p = sub.add_parser("note", help="record a human decision, blocker or note")
    p.add_argument("--type", choices=["decision", "blocker", "note"], default="note")
    p.add_argument("--text", required=True)
    p.add_argument("--reason")
    p.add_argument("--rejected", action="append")
    p.add_argument("--supersedes")
    p.add_argument("--files", action="append")
    p.add_argument("--workstream")
    p.set_defaults(func=cmd_note)

    p = sub.add_parser("workstreams", help="list workstreams")
    p.add_argument("--status", choices=["in_progress", "blocked", "completed"])
    p.add_argument("--provider")
    p.add_argument("--actor", choices=["human", "agent"])
    p.add_argument("--since")
    p.set_defaults(func=cmd_workstreams)

    p = sub.add_parser("timeline", help="chronological events and grouping evidence")
    p.add_argument("workstream", nargs="?")
    p.set_defaults(func=cmd_timeline)

    p = sub.add_parser("standup", help="completed / in progress / blocked / next")
    p.add_argument("--since", default="yesterday")
    p.set_defaults(func=cmd_standup)

    p = sub.add_parser("resume", help="context package for a fresh human or agent")
    p.add_argument("workstream", nargs="?")
    p.set_defaults(func=cmd_resume)

    p = sub.add_parser("why", help="decision rationale and later evidence")
    p.add_argument("query")
    p.add_argument("--workstream")
    p.set_defaults(func=cmd_why)

    p = sub.add_parser("search", help="search events")
    p.add_argument("term")
    p.add_argument("--type")
    p.add_argument("--provider")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("show-event", help="print the raw event behind any generated statement")
    p.add_argument("event", help="event id prefix or commit SHA")
    p.set_defaults(func=cmd_show_event)

    p = sub.add_parser("merge", help="force workstreams together")
    p.add_argument("workstreams", nargs="+")
    p.set_defaults(func=cmd_merge)

    p = sub.add_parser("split", help="detach one event from its workstream")
    p.add_argument("event")
    p.set_defaults(func=cmd_split)

    p = sub.add_parser("rename", help="rename a workstream")
    p.add_argument("workstream")
    p.add_argument("title")
    p.set_defaults(func=cmd_rename)

    p = sub.add_parser("resolve", help="mark a blocker / failing CI / checkpoint as resolved")
    p.add_argument("event")
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("purge", help="delete all recorded data for this project")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_purge)
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if getattr(args, "hook", False):
        return cmd_hook(args)
    try:
        project = discover(Path(args.C))
        ledger = open_ledger(project)
        try:
            args.func(args, project, ledger)
        finally:
            ledger.close()
    except WorklogError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2
    return 0

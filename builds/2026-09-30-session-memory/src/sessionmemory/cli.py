from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import brief as brief_mod
from . import parsers
from .server import App, create_server
from .store import HIGHLIGHT_END, HIGHLIGHT_START, Store
from .summarize import SummaryError, ai_summary

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def _store(args: argparse.Namespace) -> Store:
    return Store(args.db)


def _paths(args: argparse.Namespace) -> list[Path] | None:
    if getattr(args, "demo", False):
        return [EXAMPLES]
    return [Path(p) for p in args.paths] or None


def cmd_ingest(args: argparse.Namespace) -> int:
    store = _store(args)
    counts = store.ingest(parsers.discover(_paths(args)))
    stats = store.stats()
    print(f"ingested: {counts['added']} new, {counts['updated']} updated, {counts['unchanged']} unchanged "
          f"({stats['sessions']} sessions, {stats['messages']} messages total)")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    hits = _store(args).search(" ".join(args.query), args.project, args.source, args.limit)
    if not hits:
        print("no matches")
        return 1
    for hit in hits:
        snippet = hit["snippet"].replace(HIGHLIGHT_START, "[").replace(HIGHLIGHT_END, "]").replace("\n", " ")
        print(f"{(hit['ended'] or '')[:10]}  {hit['project']} / {hit['title'][:50]}  ({hit['source']})\n    {snippet}")
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    store = _store(args)
    try:
        text = (brief_mod.ai_brief(store, args.project, max_sessions=args.sessions, days=args.days) if args.ai
                else brief_mod.build_brief(store, args.project, max_sessions=args.sessions, days=args.days))
    except SummaryError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    print(text)
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    store = _store(args)
    matches = [s for s in store.sessions(args.project, limit=args.limit) if not store.get_summary(s["id"], "ai")]
    for row in matches:
        try:
            store.save_summary(row["id"], "ai", ai_summary(store.session_object(row["id"])))
        except SummaryError as err:
            print(f"error: {err}", file=sys.stderr)
            return 2
        print(f"summarised: {row['title'][:70]}")
    print(f"{len(matches)} session(s) summarised")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    store = _store(args)
    app = App(store, _paths(args))
    counts = app.ingest()
    print(f"ingested: {counts['added']} new, {counts['updated']} updated, {counts['unchanged']} unchanged")
    server = create_server(app, args.port)
    print(f"Session Memory running at http://127.0.0.1:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sessionmemory", description="Searchable memory of your AI conversations.")
    parser.add_argument("--db", default="sessionmemory.db", help="SQLite database path (default: ./sessionmemory.db)")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_sources(p: argparse.ArgumentParser) -> None:
        p.add_argument("paths", nargs="*", help="files/folders (default: ~/.claude/projects)")
        p.add_argument("--demo", action="store_true", help="use the bundled example transcripts")

    p = sub.add_parser("ingest", help="index transcripts"); add_sources(p); p.set_defaults(func=cmd_ingest)
    p = sub.add_parser("serve", help="ingest then start the web UI"); add_sources(p)
    p.add_argument("--port", type=int, default=8765); p.set_defaults(func=cmd_serve)
    p = sub.add_parser("search", help="full-text search"); p.add_argument("query", nargs="+")
    p.add_argument("--project"); p.add_argument("--source"); p.add_argument("--limit", type=int, default=15)
    p.set_defaults(func=cmd_search)
    p = sub.add_parser("brief", help="print a project resume brief"); p.add_argument("project")
    p.add_argument("--sessions", type=int, default=6); p.add_argument("--days", type=int)
    p.add_argument("--ai", action="store_true", help="tighten with Claude (needs ANTHROPIC_API_KEY)")
    p.set_defaults(func=cmd_brief)
    p = sub.add_parser("summarize", help="AI-summarise sessions (needs ANTHROPIC_API_KEY)")
    p.add_argument("--project"); p.add_argument("--limit", type=int, default=20); p.set_defaults(func=cmd_summarize)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)

"""Command line entry point: index, search, brief, summarize, serve, demo."""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from . import store
from .brief import build_brief
from .demo import write_demo
from .server import App, make_server
from .summarize import SummarizeError, summarize_pending

DEFAULT_DB = Path.home() / ".ctxvault" / "vault.db"
DEFAULT_SRC = Path.home() / ".claude" / "projects"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ctxvault", description="Searchable vault of Claude Code sessions")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="vault database path")
    parser.add_argument("--src", default=str(DEFAULT_SRC), help="Claude Code projects directory")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("index", help="index new/changed transcripts")
    search = sub.add_parser("search", help="full-text search")
    search.add_argument("query")
    search.add_argument("--project")
    brief = sub.add_parser("brief", help="print a project resume brief")
    brief.add_argument("project")
    summ = sub.add_parser("summarize", help="AI-summarize recent sessions (needs ANTHROPIC_API_KEY)")
    summ.add_argument("--project")
    summ.add_argument("--limit", type=int, default=10)
    serve = sub.add_parser("serve", help="start the web UI")
    serve.add_argument("--port", type=int, default=8765)
    demo = sub.add_parser("demo", help="serve the UI over generated sample transcripts")
    demo.add_argument("--port", type=int, default=8765)
    return parser


def _serve(conn, src: Path, port: int) -> int:
    server = make_server(App(conn, src), port=port)
    print(f"Context Vault at http://127.0.0.1:{port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "demo":
        src = Path(tempfile.mkdtemp(prefix="ctxvault-demo-"))
        write_demo(src)
        conn = store.connect(":memory:")
        store.index_directory(conn, src)
        return _serve(conn, src, args.port)
    src = Path(args.src)
    if not src.is_dir():
        print(f"error: transcripts directory not found: {src}", file=sys.stderr)
        return 2
    conn = store.connect(args.db)
    if args.command in ("serve", "search", "brief", "summarize"):
        store.index_directory(conn, src)  # cheap when nothing changed
    if args.command == "index":
        stats = store.index_directory(conn, src)
        print(", ".join(f"{k}={v}" for k, v in stats.items()))
    elif args.command == "search":
        for hit in store.search(conn, args.query, args.project):
            print(f"[{hit['project']}] {hit['title'] or hit['session_id']} ({hit['ts'][:10]})\n    {hit['snippet']}")
    elif args.command == "brief":
        text = build_brief(conn, args.project)
        if text is None:
            print(f"error: no sessions for project '{args.project}'", file=sys.stderr)
            return 1
        print(text)
    elif args.command == "summarize":
        try:
            result = summarize_pending(conn, args.project, args.limit)
        except SummarizeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"summarized={result['summarized']}")
        for error in result["errors"]:
            print(f"  {error}", file=sys.stderr)
        return 1 if result["errors"] and not result["summarized"] else 0
    elif args.command == "serve":
        return _serve(conn, src, args.port)
    return 0

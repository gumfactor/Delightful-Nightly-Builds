"""Argparse CLI for Snipvault. Wires db/enrich/render together."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .db import (
    add_snippet,
    connect,
    get_snippet,
    list_snippets,
    remove_snippet,
    search_snippets,
)
from .enrich import default_description, detect_language, enrich_snippet, expand_query, extract_tags
from .render import render_html


def _read_code(args) -> tuple:
    """Returns (code, source_label)."""
    if args.code is not None:
        return args.code, None
    if args.file is not None:
        path = Path(args.file)
        if not path.is_file():
            print(f"error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        return path.read_text(encoding="utf-8"), str(path)
    stdin_text = sys.stdin.read()
    if not stdin_text.strip():
        print("error: no code provided (use --code, --file, or pipe via stdin)", file=sys.stderr)
        sys.exit(1)
    return stdin_text, None


def cmd_add(conn, args) -> None:
    code, source_from_file = _read_code(args)
    source = args.source or source_from_file

    # Detect from the actual file path read, not the stored `source` label —
    # an explicit --source (e.g. a project name) has no filename extension
    # and would otherwise silently override --file's extension for detection.
    language = args.lang or detect_language(source_from_file or args.title)

    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        description = args.description or default_description(code, language)
    elif args.ai_enrich:
        description, tags = enrich_snippet(code, language, args.title)
        if args.description:
            description = args.description
    else:
        description = args.description or default_description(code, language)
        tags = extract_tags(code, language)

    snippet = add_snippet(
        conn,
        title=args.title,
        language=language,
        code=code,
        description=description,
        tags=tags,
        source=source,
    )
    print(f"Saved snippet #{snippet.id}: {snippet.title} [{snippet.language}] tags={','.join(snippet.tags)}")


def cmd_search(conn, args) -> None:
    keywords = expand_query(args.query) if args.ai else args.query.split()
    results = search_snippets(conn, keywords)
    if not results:
        print("No matching snippets.")
        return
    for s in results:
        print(f"#{s.id}  {s.title}  [{s.language}]  tags={','.join(s.tags)}  used={s.usage_count}x")


def cmd_get(conn, args) -> None:
    snippet = get_snippet(conn, args.id)
    if snippet is None:
        print(f"error: no snippet with id {args.id}", file=sys.stderr)
        sys.exit(1)
    print(f"#{snippet.id}: {snippet.title}")
    print(f"language: {snippet.language}")
    if snippet.description:
        print(f"description: {snippet.description}")
    if snippet.tags:
        print(f"tags: {', '.join(snippet.tags)}")
    print("---")
    print(snippet.code)


def cmd_list(conn, args) -> None:
    results = list_snippets(conn, language=args.lang, tag=args.tag)
    if not results:
        print("No snippets found.")
        return
    for s in results:
        print(f"#{s.id}  {s.title}  [{s.language}]  tags={','.join(s.tags)}  used={s.usage_count}x")


def cmd_remove(conn, args) -> None:
    if remove_snippet(conn, args.id):
        print(f"Removed snippet #{args.id}")
    else:
        print(f"error: no snippet with id {args.id}", file=sys.stderr)
        sys.exit(1)


def cmd_render(conn, args) -> None:
    results = list_snippets(conn)
    # PRD specifies the dashboard is sorted by usage/recency, distinct from
    # list_snippets()'s default updated_at-only ordering used by `list`.
    results.sort(key=lambda s: (s.usage_count, s.updated_at), reverse=True)
    html = render_html(results)
    out_path = Path(args.output)
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {len(results)} snippet(s) to {out_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="snipvault", description="Personal code-snippet library.")
    parser.add_argument("--db", default=None, help="Path to the SQLite database (default: data/snippets.db)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Save a new snippet")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--code", default=None, help="Snippet code as a string")
    p_add.add_argument("--file", default=None, help="Read snippet code from a file")
    p_add.add_argument("--lang", default=None, help="Language (auto-detected from --file if omitted)")
    p_add.add_argument("--description", default=None)
    p_add.add_argument("--tags", default=None, help="Comma-separated tags")
    p_add.add_argument("--source", default=None, help="Optional origin label/path")
    p_add.add_argument("--ai-enrich", action="store_true", help="Use Claude Haiku to auto-generate description/tags")
    p_add.set_defaults(func=cmd_add)

    p_search = sub.add_parser("search", help="Search snippets")
    p_search.add_argument("query")
    p_search.add_argument("--ai", action="store_true", help="Expand a natural-language query via Claude Haiku")
    p_search.set_defaults(func=cmd_search)

    p_get = sub.add_parser("get", help="Print a snippet by id")
    p_get.add_argument("id", type=int)
    p_get.set_defaults(func=cmd_get)

    p_list = sub.add_parser("list", help="List snippets")
    p_list.add_argument("--lang", default=None)
    p_list.add_argument("--tag", default=None)
    p_list.set_defaults(func=cmd_list)

    p_remove = sub.add_parser("remove", help="Remove a snippet by id")
    p_remove.add_argument("id", type=int)
    p_remove.set_defaults(func=cmd_remove)

    p_render = sub.add_parser("render", help="Render a self-contained HTML dashboard")
    p_render.add_argument("--output", default="snippets.html")
    p_render.set_defaults(func=cmd_render)

    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    db_path = Path(args.db) if args.db else Path(__file__).resolve().parent.parent / "data" / "snippets.db"
    conn = connect(db_path)
    try:
        args.func(conn, args)
    finally:
        conn.close()

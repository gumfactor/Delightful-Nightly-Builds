"""Promptbook CLI: ingest / search / stats / render."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from src.ai_enrich import enrich_note
from src.ingest import ingest_directory
from src.render import render_html
from src.storage import DEFAULT_DB_PATH, connect, get_stats, search_prompts, set_ai_note

TASK_TYPES = (
    "bug-fix",
    "test",
    "docs",
    "config",
    "review",
    "refactor",
    "research",
    "feature",
    "other",
)


def default_claude_dir() -> Path:
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if config_dir:
        return Path(config_dir).expanduser() / "projects"
    return Path.home() / ".claude" / "projects"


def cmd_ingest(args: argparse.Namespace) -> int:
    claude_dir = Path(args.claude_dir) if args.claude_dir else default_claude_dir()
    db_path = Path(args.db) if args.db else DEFAULT_DB_PATH
    conn = connect(db_path)
    try:
        result = ingest_directory(conn, claude_dir)
    finally:
        conn.close()
    print(f"Scanned {result.files_scanned} session file(s), "
          f"{result.files_with_new_lines} with new activity.")
    print(f"Prompts seen: {result.prompts_seen}, new prompts stored: {result.prompts_inserted}.")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    db_path = Path(args.db) if args.db else DEFAULT_DB_PATH
    conn = connect(db_path)
    try:
        rows = search_prompts(
            conn,
            project=args.project,
            task_type=args.task_type,
            min_score=args.min_score,
            query=args.query,
            limit=args.limit,
        )
    finally:
        conn.close()

    if not rows:
        print("No matching prompts.")
        return 0

    for row in rows:
        preview = row["prompt_text"].replace("\n", " ")
        if len(preview) > 100:
            preview = preview[:97] + "..."
        print(f"[{row['score']:>2}/10] ({row['task_type']}) {preview}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    db_path = Path(args.db) if args.db else DEFAULT_DB_PATH
    conn = connect(db_path)
    try:
        stats = get_stats(conn)
    finally:
        conn.close()

    print(f"Total prompts: {stats['total']}")
    print(f"Average score: {stats['avg_score']}")
    print("By task type:")
    for task_type, count in stats["by_task_type"].items():
        print(f"  {task_type}: {count}")
    print("By project:")
    for project, count in stats["by_project"].items():
        print(f"  {project}: {count}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    db_path = Path(args.db) if args.db else DEFAULT_DB_PATH
    conn = connect(db_path)
    try:
        if args.ai:
            top_rows = search_prompts(conn, min_score=7, limit=args.ai_limit)
            for row in top_rows:
                if row["ai_note"]:
                    continue
                note = enrich_note(
                    prompt_text=row["prompt_text"],
                    task_type=row["task_type"],
                    score=row["score"],
                    tools_used=list(json.loads(row["tools_used"])),
                )
                set_ai_note(conn, row["prompt_uuid"], note)
            conn.commit()
        html = render_html(conn)
    finally:
        conn.close()

    out_path = Path(args.out)
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote dashboard to {out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="promptbook", description="Your own prompts, scored.")
    parser.add_argument("--db", help="Path to the SQLite database (default: data/promptbook.db)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="Scan local Claude Code sessions and store new prompts")
    p_ingest.add_argument("--claude-dir", help="Override the Claude Code projects directory")
    p_ingest.set_defaults(func=cmd_ingest)

    p_search = sub.add_parser("search", help="Search the prompt library")
    p_search.add_argument("--project", help="Filter by project (exact cwd string)")
    p_search.add_argument("--task-type", choices=TASK_TYPES, help="Filter by task type")
    p_search.add_argument("--min-score", type=int, help="Minimum effectiveness score (0-10)")
    p_search.add_argument("--query", help="Text to search for within prompt text")
    p_search.add_argument("--limit", type=int, default=50, help="Max results (default 50)")
    p_search.set_defaults(func=cmd_search)

    p_stats = sub.add_parser("stats", help="Show aggregate library statistics")
    p_stats.set_defaults(func=cmd_stats)

    p_render = sub.add_parser("render", help="Render the HTML dashboard")
    p_render.add_argument("--out", default="promptbook.html", help="Output HTML file path")
    p_render.add_argument("--ai", action="store_true", help="Add AI notes to top-scoring prompts")
    p_render.add_argument("--ai-limit", type=int, default=10, help="Max prompts to enrich with --ai")
    p_render.set_defaults(func=cmd_render)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    min_score = getattr(args, "min_score", None)
    if min_score is not None and (min_score < 0 or min_score > 10):
        parser.error("--min-score must be between 0 and 10")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

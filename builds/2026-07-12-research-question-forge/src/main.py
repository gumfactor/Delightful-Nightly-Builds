#!/usr/bin/env python3
"""Research Question Forge CLI.

Generates, scores, persists, and browses combinatorial research-question
skeletons for a domain taxonomy. See Manual.md for full usage.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

BUILD_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BUILD_ROOT))

from src import ai_polish, db, generator, render  # noqa: E402

DEFAULT_DB_PATH = BUILD_ROOT / "output" / "forge.db"
DEFAULT_HTML_PATH = BUILD_ROOT / "output" / "forge.html"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def cmd_generate(args: argparse.Namespace) -> None:
    conn = db.connect(args.db)
    db.init_db(conn)
    existing = db.all_skeletons(conn)
    taxonomy = generator.load_taxonomy()
    batch = generator.generate_batch(args.count, existing, taxonomy, rng_seed=args.seed)

    if not batch:
        print("No new compatible combinations could be generated.")
        return

    created_at = _now_iso()
    saved_ids = []
    for question in batch:
        polished, source = ("", "template")
        if args.polish:
            polished, source = ai_polish.polish_question(question)
        question["ai_polish"] = polished or None
        question["ai_source"] = source
        qid = db.insert_question(conn, created_at, question)
        saved_ids.append(qid)

    print(f"Generated and saved {len(saved_ids)} question(s):")
    for qid, question in zip(saved_ids, batch):
        print(f"  #{qid} [{question['testability']}, novelty {question['novelty_score']:.2f}] {question['skeleton']}")
    conn.close()


def cmd_render(args: argparse.Namespace) -> None:
    conn = db.connect(args.db)
    db.init_db(conn)
    questions = db.list_questions(conn)
    output_path = render.write_html(questions, args.output)
    print(f"Wrote {len(questions)} question(s) to {output_path}")
    conn.close()


def cmd_list(args: argparse.Namespace) -> None:
    conn = db.connect(args.db)
    db.init_db(conn)
    for row in db.list_questions(conn):
        star = "*" if row["starred"] else " "
        print(f"[{star}] #{row['id']} ({row['testability']}) {row['skeleton']}")
    conn.close()


def cmd_star(args: argparse.Namespace) -> None:
    conn = db.connect(args.db)
    db.init_db(conn)
    ok = db.set_starred(conn, args.id, not args.unstar)
    print(f"{'Unstarred' if args.unstar else 'Starred'} #{args.id}" if ok else f"No question #{args.id} found")
    conn.close()


def cmd_use(args: argparse.Namespace) -> None:
    conn = db.connect(args.db)
    db.init_db(conn)
    ok = db.set_used(conn, args.id, True)
    print(f"Marked #{args.id} as used" if ok else f"No question #{args.id} found")
    conn.close()


def cmd_tag(args: argparse.Namespace) -> None:
    conn = db.connect(args.db)
    db.init_db(conn)
    ok = db.set_tag(conn, args.id, args.value)
    print(f"Tagged #{args.id} as '{args.value}'" if ok else f"No question #{args.id} found")
    conn.close()


def cmd_search(args: argparse.Namespace) -> None:
    conn = db.connect(args.db)
    db.init_db(conn)
    results = db.search_questions(conn, args.query)
    if not results:
        print("No matches.")
    for row in results:
        print(f"#{row['id']} ({row['testability']}) {row['skeleton']}")
    conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="forge", description="Research Question Forge CLI")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to the SQLite library file")
    sub = parser.add_subparsers(dest="command", required=True)

    p_generate = sub.add_parser("generate", help="Generate a new batch of research questions")
    p_generate.add_argument("--count", type=int, default=5, help="How many questions to generate")
    p_generate.add_argument("--seed", type=int, default=None, help="Optional RNG seed for reproducible output")
    p_generate.add_argument("--polish", action="store_true", help="Call the Anthropic API to polish each question (falls back to a template if no key is set)")
    p_generate.set_defaults(func=cmd_generate)

    p_render = sub.add_parser("render", help="Render the HTML library viewer")
    p_render.add_argument("--output", default=str(DEFAULT_HTML_PATH), help="Path to write forge.html")
    p_render.set_defaults(func=cmd_render)

    p_list = sub.add_parser("list", help="List all saved questions")
    p_list.set_defaults(func=cmd_list)

    p_star = sub.add_parser("star", help="Star (or unstar) a question")
    p_star.add_argument("id", type=int)
    p_star.add_argument("--unstar", action="store_true")
    p_star.set_defaults(func=cmd_star)

    p_use = sub.add_parser("use", help="Mark a question as used")
    p_use.add_argument("id", type=int)
    p_use.set_defaults(func=cmd_use)

    p_tag = sub.add_parser("tag", help="Tag a question with a project/grant label")
    p_tag.add_argument("id", type=int)
    p_tag.add_argument("value")
    p_tag.set_defaults(func=cmd_tag)

    p_search = sub.add_parser("search", help="Full-text search saved questions")
    p_search.add_argument("query")
    p_search.set_defaults(func=cmd_search)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()

"""Counterpoint CLI — build a complete Response-to-Reviewers letter.

    python src/main.py check --comments FILE --responses FILE
    python src/main.py build --comments FILE --responses FILE --out-dir DIR [--ai] [--force]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .ai_polish import DEFAULT_MODEL, polish_response
from .parser import ParseError, parse_comments, parse_responses
from .report import render_html, render_markdown, render_plaintext
from .response_matcher import CompletenessReport, match


def _read_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        raise SystemExit(2) from None


def _load(comments_path: str, responses_path: str):
    comments_text = _read_file(comments_path)
    responses_text = _read_file(responses_path)
    try:
        comments = parse_comments(comments_text)
        responses = parse_responses(responses_text)
    except ParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    return comments, responses


def _print_report(report: CompletenessReport) -> None:
    print(f"{report.addressed}/{report.total} comments addressed ({report.percentage}%)")
    if report.missing:
        print("Missing responses for:")
        for comment_id in report.missing:
            print(f"  - {comment_id}")
    if report.orphaned:
        print("Orphaned response keys (no matching comment):")
        for comment_id in report.orphaned:
            print(f"  - {comment_id}")
    if not report.missing and not report.orphaned:
        print("All comments addressed. No orphaned response keys.")


def cmd_check(args: argparse.Namespace) -> int:
    comments, responses = _load(args.comments, args.responses)
    report = match(comments, responses)
    _print_report(report)
    return 0 if report.is_complete else 1


def cmd_build(args: argparse.Namespace) -> int:
    comments, responses = _load(args.comments, args.responses)
    report = match(comments, responses)
    _print_report(report)

    if not report.is_complete and not args.force:
        print(
            "\nRefusing to build: comments are missing responses. "
            "Add them, or pass --force to build anyway (missing comments "
            "will be visibly flagged, never silently omitted).",
            file=sys.stderr,
        )
        return 1

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    polished: dict[str, str] = {}
    for comment in comments:
        if comment.id not in responses:
            continue
        polished[comment.id] = polish_response(
            comment.text,
            responses[comment.id],
            api_key=api_key,
            model=args.model,
            use_ai=args.ai,
        )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "letter.md").write_text(render_markdown(comments, polished, report), encoding="utf-8")
    (out_dir / "letter.html").write_text(render_html(comments, polished, report), encoding="utf-8")
    (out_dir / "letter.txt").write_text(render_plaintext(comments, polished, report), encoding="utf-8")

    print(f"\nWrote letter.md, letter.html, letter.txt to {out_dir}/")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="counterpoint")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Report completeness only")
    check_parser.add_argument("--comments", required=True, help="Path to reviewer comments file")
    check_parser.add_argument("--responses", required=True, help="Path to responses file")
    check_parser.set_defaults(func=cmd_check)

    build_parser_ = subparsers.add_parser("build", help="Generate the response letter")
    build_parser_.add_argument("--comments", required=True, help="Path to reviewer comments file")
    build_parser_.add_argument("--responses", required=True, help="Path to responses file")
    build_parser_.add_argument("--out-dir", default="output", help="Output directory (default: output/)")
    build_parser_.add_argument(
        "--ai", action="store_true", help="Polish responses with the Anthropic API (requires ANTHROPIC_API_KEY)"
    )
    build_parser_.add_argument("--model", default=DEFAULT_MODEL, help=f"Model to use with --ai (default: {DEFAULT_MODEL})")
    build_parser_.add_argument(
        "--force", action="store_true", help="Build even if some comments are missing responses"
    )
    build_parser_.set_defaults(func=cmd_build)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

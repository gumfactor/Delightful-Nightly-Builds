"""Lecture Loom CLI — batch-converts raw lecture notes into a consistent
slide outline + student handout, with a deterministic timing/objective/
structure-consistency engine underneath."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from ai_polish import polish_lecture
from formatter import write_outputs
from parser import parse_lecture
from render import build_dashboard_html
from timing import DEFAULT_TARGET_MINUTES, DEFAULT_WPM, build_report

VALID_EXTENSIONS = {".md", ".txt"}


def _collect_input_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if path.is_dir():
        files = sorted(p for p in path.iterdir() if p.suffix.lower() in VALID_EXTENSIONS)
        if not files:
            raise FileNotFoundError(f"no .md or .txt files found in {path}")
        return files
    raise FileNotFoundError(f"No such file or directory: {path}")


def _load_batch(path: Path, wpm: float, target_minutes: float, use_ai: bool):
    api_key = os.environ.get("ANTHROPIC_API_KEY") if use_ai else None
    results = []
    for file_path in _collect_input_files(path):
        lecture = parse_lecture(file_path)
        report = build_report(lecture, wpm=wpm, target_minutes=target_minutes)
        polish = polish_lecture(lecture, api_key) if use_ai else None
        results.append((lecture, report, polish))
    return results


def _print_check_table(results, out) -> None:
    for lecture, report, _polish in results:
        status = report.budget_status.replace("_", " ")
        print(f"{lecture.title}", file=out)
        print(
            f"  timing: {report.total_minutes:.1f} / {report.target_minutes:.1f} min ({status})",
            file=out,
        )
        if report.budget_status == "over_budget" and report.worst_section:
            print(f"  longest section: {report.worst_section}", file=out)
        print(f"  objectives: {report.objective_flag} ({len(lecture.objectives)} found)", file=out)
        if report.dense_sections:
            print(f"  dense sections: {', '.join(report.dense_sections)}", file=out)
        if report.heading_skip_warning:
            print("  warning: heading level skipped", file=out)
        print(file=out)


def _cmd_check(args: argparse.Namespace) -> int:
    results = _load_batch(Path(args.path), args.wpm, args.target_minutes, args.ai_polish)
    _print_check_table(results, sys.stdout)
    return 0


def _cmd_format(args: argparse.Namespace) -> int:
    results = _load_batch(Path(args.path), args.wpm, args.target_minutes, args.ai_polish)
    output_dir = Path(args.output)
    for lecture, report, polish in results:
        outline_path, handout_path = write_outputs(lecture, report, output_dir, polish)
        print(f"wrote {outline_path}")
        print(f"wrote {handout_path}")
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    results = _load_batch(Path(args.path), args.wpm, args.target_minutes, args.ai_polish)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    html = build_dashboard_html([(lecture, report) for lecture, report, _ in results])
    dashboard_path = output_dir / "dashboard.html"
    dashboard_path.write_text(html, encoding="utf-8")
    print(f"wrote {dashboard_path}")
    return 0


def _add_common_args(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("path", help="A lecture note file or a folder of them")
    sub.add_argument(
        "--target-minutes",
        type=float,
        default=DEFAULT_TARGET_MINUTES,
        help=f"Target lecture length in minutes (default: {DEFAULT_TARGET_MINUTES})",
    )
    sub.add_argument(
        "--wpm",
        type=float,
        default=DEFAULT_WPM,
        help=f"Assumed instructional speaking pace in words/minute (default: {DEFAULT_WPM})",
    )
    sub.add_argument(
        "--ai-polish",
        action="store_true",
        help="Polish bullets and draft discussion questions via Claude Haiku "
        "(requires ANTHROPIC_API_KEY; falls back to a deterministic cleanup otherwise)",
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lecture-loom", description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Print timing/flags to the terminal only")
    _add_common_args(check_parser)
    check_parser.set_defaults(func=_cmd_check)

    format_parser = subparsers.add_parser("format", help="Write outline.md + handout.md per lecture")
    _add_common_args(format_parser)
    format_parser.add_argument("--output", default="loom-output", help="Output directory")
    format_parser.set_defaults(func=_cmd_format)

    render_parser = subparsers.add_parser("render", help="Build the batch HTML dashboard")
    _add_common_args(render_parser)
    render_parser.add_argument("--output", default="loom-output", help="Output directory")
    render_parser.set_defaults(func=_cmd_render)

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    try:
        if args.target_minutes <= 0:
            raise ValueError("--target-minutes must be positive")
        if args.wpm <= 0:
            raise ValueError("--wpm must be positive")
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(run())

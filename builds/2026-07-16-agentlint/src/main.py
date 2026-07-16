"""AgentLint CLI entry point.

Usage:
    python3 src/main.py audit <path> [options]
    python3 -m src.main audit <path> [options]      (equivalent)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as either `python3 src/main.py` (script) or
# `python3 -m src.main` (package) without duplicating the CLI logic.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "src"

import argparse  # noqa: E402
import os  # noqa: E402
from typing import Optional  # noqa: E402

from .ai_review import run_ai_review  # noqa: E402
from .checks import make_finding, run_all_checks  # noqa: E402
from .parser import parse_document  # noqa: E402
from .report import build_report, render_html, render_json, render_text  # noqa: E402

EXIT_OK = 0
EXIT_LINT_FAILURE = 1
EXIT_USAGE_ERROR = 2

_SEVERITY_RANK = {"error": 0, "warning": 1, "info": 2}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentlint", description=(
        "Audit an AI agent instruction file (CLAUDE.md/AGENTS.md-style doc) for broken "
        "references, missing sections, contradictions, and optional AI-reviewed semantic drift."
    ))
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="Audit an instruction file")
    audit.add_argument("path", help="Path to the instruction file to audit")
    audit.add_argument("--root", default=None,
                        help="Root directory to resolve referenced paths against "
                             "(default: the instruction file's own directory)")
    audit.add_argument("--require-sections", default="",
                        help="Comma-separated list of heading text that must be present")
    audit.add_argument("--ground-truth", default=None,
                        help="Path to a data file the AI review should cross-check claims against")
    audit.add_argument("--format", choices=["text", "json", "html"], default="text")
    audit.add_argument("--out", default=None, help="Write the report to this file instead of stdout")
    audit.add_argument("--fail-on", choices=["error", "warning", "none"], default="error",
                        help="Minimum severity that causes a non-zero exit code")
    audit.add_argument("--skip-ai", action="store_true",
                        help="Skip the AI semantic review even if ANTHROPIC_API_KEY is set")

    return parser


def run_audit(args: argparse.Namespace) -> int:
    target_path = Path(args.path)
    if not target_path.is_file():
        print(f"agentlint: error: instructions file not found: {target_path}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    instructions_text = target_path.read_text(encoding="utf-8")
    doc = parse_document(instructions_text)
    root = Path(args.root).resolve() if args.root else target_path.parent.resolve()
    required_sections = [s for s in args.require_sections.split(",") if s.strip()]

    findings = run_all_checks(doc, root, required_sections)

    ground_truth_text = None
    if args.ground_truth:
        ground_truth_path = Path(args.ground_truth)
        if ground_truth_path.is_file():
            ground_truth_text = ground_truth_path.read_text(encoding="utf-8")
        else:
            findings.append(make_finding(
                check="missing_ground_truth_file",
                severity="error",
                message=f"--ground-truth file not found: {ground_truth_path}",
                excerpt=str(ground_truth_path),
                line=None,
            ))

    if not args.skip_ai:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        findings += run_ai_review(instructions_text, ground_truth_text, api_key)

    report = build_report(findings, target=str(target_path))

    renderers = {"text": render_text, "json": render_json, "html": render_html}
    rendered = renderers[args.format](report)

    if args.out:
        Path(args.out).write_text(rendered, encoding="utf-8")
    else:
        print(rendered)

    if args.fail_on == "none":
        return EXIT_OK
    threshold = _SEVERITY_RANK[args.fail_on]
    if any(_SEVERITY_RANK.get(f["severity"], 99) <= threshold for f in report["findings"]):
        return EXIT_LINT_FAILURE
    return EXIT_OK


def main(argv: Optional[list] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.command == "audit":
        return run_audit(args)
    parser.print_help()
    return EXIT_USAGE_ERROR


if __name__ == "__main__":
    sys.exit(main())

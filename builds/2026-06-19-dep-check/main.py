#!/usr/bin/env python3
"""dep-check: Python Dependency Auditor.

Usage:
    python main.py [path]                    # scan directory or requirements file
    python main.py --format html --output report.html [path]
    python main.py --exit-on-outdated [path]
"""
import argparse
import sys
import pathlib
from src.parser import parse_requirements_txt, parse_setup_cfg, parse_pipfile
from src.pypi import fetch_package_info, extract_version_info
from src.analyzer import build_result, compute_summary
from src.report import render_terminal, render_html

_KNOWN_FILES = [
    ("requirements.txt", parse_requirements_txt),
    ("requirements-dev.txt", parse_requirements_txt),
    ("setup.cfg", parse_setup_cfg),
    ("Pipfile", parse_pipfile),
]


def _collect_requirements(path: pathlib.Path) -> list:
    """Find and parse all known requirements files at path (file or dir)."""
    requirements = []
    if path.is_file():
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.name.endswith(".txt"):
            requirements.extend(parse_requirements_txt(text, source_file=path.name))
        elif path.name == "setup.cfg":
            requirements.extend(parse_setup_cfg(text, source_file=path.name))
        elif path.name == "Pipfile":
            requirements.extend(parse_pipfile(text, source_file=path.name))
        return requirements

    for filename, parser in _KNOWN_FILES:
        candidate = path / filename
        if candidate.exists():
            text = candidate.read_text(encoding="utf-8", errors="replace")
            requirements.extend(parser(text, source_file=filename))

    return requirements


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit Python dependencies against PyPI for outdated or yanked releases."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory or requirements file to scan (default: current directory)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "html"],
        default="text",
        help="Output format: text (default) or html",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    parser.add_argument(
        "--exit-on-outdated",
        action="store_true",
        help="Exit with code 1 if any packages need updating",
    )
    args = parser.parse_args()

    scan_path = pathlib.Path(args.path).resolve()
    if not scan_path.exists():
        print(f"Error: path not found: {scan_path}", file=sys.stderr)
        return 2

    reqs = _collect_requirements(scan_path)
    if not reqs:
        print("No requirements files found (or all are empty).", file=sys.stderr)
        return 0

    results = []
    for req in reqs:
        pypi_data = fetch_package_info(req.name)
        if pypi_data is None:
            from src.models import PackageResult
            results.append(PackageResult(
                req=req,
                latest_version=None,
                pinned_upload_date=None,
                days_since_pinned=None,
                status="unknown",
            ))
        else:
            latest, upload_date, yanked, yanked_reason = extract_version_info(pypi_data, req.pinned_version)
            results.append(build_result(req, latest, upload_date, yanked, yanked_reason))

    summary = compute_summary(results)

    if args.format == "html":
        output = render_html(results, summary)
    else:
        output = render_terminal(results, summary)

    if args.output:
        pathlib.Path(args.output).write_text(output, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(output, end="")

    if args.exit_on_outdated and summary.needs_update > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

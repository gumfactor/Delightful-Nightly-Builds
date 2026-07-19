"""Argparse CLI for Protocol Forge: init, check, draft, approve, list, show."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from src.checklist import run_checklist
from src.drafting import assemble_markdown, render_stored_protocol
from src.library import ProtocolLibrary
from src.models import TEMPLATE_STUDY, Study

DEFAULT_DB = "protocol_library.db"


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "protocol"


def cmd_init(args: argparse.Namespace, stdout, stderr) -> int:
    path = Path(args.path)
    if path.exists() and not args.force:
        print(f"Error: {path} already exists. Use --force to overwrite.", file=stderr)
        return 1
    path.write_text(json.dumps(TEMPLATE_STUDY, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote study template to {path}", file=stdout)
    return 0


def cmd_check(args: argparse.Namespace, stdout, stderr) -> int:
    try:
        study = Study.from_file(args.study_file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=stderr)
        return 1

    report = run_checklist(study)

    if args.json:
        print(
            json.dumps(
                {
                    "completeness_score": report.completeness_score,
                    "findings": [
                        {
                            "severity": f.severity,
                            "code": f.code,
                            "field": f.field,
                            "message": f.message,
                        }
                        for f in report.findings
                    ],
                },
                indent=2,
            ),
            file=stdout,
        )
    else:
        print(f"Completeness score: {report.completeness_score}/100", file=stdout)
        if report.is_clean:
            print("No compliance issues found.", file=stdout)
        else:
            for f in report.findings:
                print(f"[{f.severity.upper()}] {f.code} ({f.field}): {f.message}", file=stdout)

    return 1 if report.blocking_findings else 0


def cmd_draft(args: argparse.Namespace, stdout, stderr) -> int:
    try:
        study = Study.from_file(args.study_file)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=stderr)
        return 1

    report = run_checklist(study)

    with ProtocolLibrary(args.db) as library:
        markdown, drafts = assemble_markdown(study, library, report)
        sections_for_save = {key: (draft.text, draft.source) for key, draft in drafts.items()}
        protocol_id = library.save_protocol(study, sections_for_save, report.completeness_score)

    out_path = Path(args.out) if args.out else Path(f"{_slugify(study.title)}.md")
    out_path.write_text(markdown, encoding="utf-8")

    print(f"Saved protocol #{protocol_id} ({study.title}) to library at {args.db}", file=stdout)
    print(f"Wrote draft to {out_path}", file=stdout)
    print(f"Completeness score: {report.completeness_score}/100", file=stdout)
    if report.blocking_findings:
        print(f"Warning: {len(report.blocking_findings)} blocking compliance issue(s) remain.", file=stdout)

    return 0


def cmd_approve(args: argparse.Namespace, stdout, stderr) -> int:
    with ProtocolLibrary(args.db) as library:
        try:
            library.approve(args.protocol_id)
        except ValueError as exc:
            print(f"Error: {exc}", file=stderr)
            return 1
    print(f"Protocol #{args.protocol_id} approved. Its sections are now eligible for reuse.", file=stdout)
    return 0


def cmd_list(args: argparse.Namespace, stdout, stderr) -> int:
    with ProtocolLibrary(args.db) as library:
        protocols = library.list_protocols()

    if not protocols:
        print("No protocols in library yet.", file=stdout)
        return 0

    for p in protocols:
        print(
            f"#{p['id']} [{p['status']}] {p['title']} "
            f"(score {p['completeness_score']}/100, created {p['created_at']})",
            file=stdout,
        )
    return 0


def cmd_show(args: argparse.Namespace, stdout, stderr) -> int:
    with ProtocolLibrary(args.db) as library:
        record = library.get_protocol(args.protocol_id)

    if record is None:
        print(f"Error: No protocol with id {args.protocol_id}", file=stderr)
        return 1

    print(render_stored_protocol(record), file=stdout)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="protocol_forge", description="IRB/ethics protocol drafting assistant.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Scaffold a blank study JSON template.")
    p_init.add_argument("path", help="Path to write the template to.")
    p_init.add_argument("--force", action="store_true", help="Overwrite if the file already exists.")
    p_init.set_defaults(func=cmd_init)

    p_check = sub.add_parser("check", help="Run the compliance checklist on a study file.")
    p_check.add_argument("study_file")
    p_check.add_argument("--json", action="store_true", help="Output findings as JSON.")
    p_check.set_defaults(func=cmd_check)

    p_draft = sub.add_parser("draft", help="Draft a full protocol document and save it to the library.")
    p_draft.add_argument("study_file")
    p_draft.add_argument("--out", help="Output Markdown path (default: <slugified-title>.md)")
    p_draft.add_argument("--db", default=DEFAULT_DB, help=f"Library database path (default: {DEFAULT_DB})")
    p_draft.set_defaults(func=cmd_draft)

    p_approve = sub.add_parser("approve", help="Mark a saved protocol as approved, enabling reuse.")
    p_approve.add_argument("protocol_id", type=int)
    p_approve.add_argument("--db", default=DEFAULT_DB)
    p_approve.set_defaults(func=cmd_approve)

    p_list = sub.add_parser("list", help="List all protocols in the library.")
    p_list.add_argument("--db", default=DEFAULT_DB)
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Show a stored protocol's full draft.")
    p_show.add_argument("protocol_id", type=int)
    p_show.add_argument("--db", default=DEFAULT_DB)
    p_show.set_defaults(func=cmd_show)

    return parser


def main(argv: list[str] | None = None, stdout=sys.stdout, stderr=sys.stderr) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args, stdout, stderr)

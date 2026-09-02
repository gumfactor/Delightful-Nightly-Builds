"""CiteForge CLI — batch citation-style conversion.

Run `python main.py --help` for the full command list.
"""

from __future__ import annotations

import argparse
import os
import sys

from . import ai_extract, bibtex_parser, crossref, db, render_html, styles
from .models import normalize_doi


def _parse_ids(raw: str | None) -> list[int]:
    if not raw:
        return []
    ids = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            ids.append(int(chunk))
        except ValueError:
            print(f"Warning: ignoring invalid id '{chunk}'")
    return ids


def _ordered_for_style(refs: list, style: str) -> list:
    if style in ("apa", "chicago"):
        return sorted(
            refs,
            key=lambda r: (
                r.authors[0].family.lower() if r.authors else "￿",
                r.year or "",
            ),
        )
    return refs


def cmd_add_bibtex(args, conn) -> int:
    try:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}")
        return 1
    references, warnings = bibtex_parser.parse_bibtex_to_references(text)
    added, updated = 0, 0
    for ref in references:
        _, was_new = db.upsert_reference(conn, ref)
        if was_new:
            added += 1
        else:
            updated += 1
    print(f"Parsed {len(references)} entries from {args.file}: {added} added, {updated} updated.")
    for warning in warnings:
        print(f"  ! {warning}")
    return 0


def cmd_add_doi(args, conn, transport=crossref.default_transport) -> int:
    if os.path.isfile(args.doi_or_file):
        with open(args.doi_or_file, encoding="utf-8") as f:
            dois = [line.strip() for line in f if line.strip()]
    else:
        dois = [args.doi_or_file]

    added, updated, errors = 0, 0, []
    for doi in dois:
        clean = normalize_doi(doi)
        cached = db.get_cached_crossref(conn, clean)
        try:
            if cached is not None:
                message = cached
            else:
                message = crossref.fetch_doi_metadata(doi, transport=transport)
                db.set_cached_crossref(conn, clean, message)
            ref = crossref.message_to_reference(message)
        except crossref.CrossrefError as exc:
            errors.append(str(exc))
            continue
        _, was_new = db.upsert_reference(conn, ref)
        if was_new:
            added += 1
        else:
            updated += 1
    print(f"Resolved {len(dois)} DOI(s): {added} added, {updated} updated, {len(errors)} error(s).")
    for error in errors:
        print(f"  ! {error}")
    return 0


def cmd_add_text(args, conn, ai_transport=ai_extract.default_transport) -> int:
    if args.file == "-":
        lines = sys.stdin.read().splitlines()
    else:
        try:
            with open(args.file, encoding="utf-8") as f:
                lines = f.read().splitlines()
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}")
            return 1

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    processed, flagged = 0, 0
    for line in lines:
        if not line.strip():
            continue
        ref = ai_extract.extract_reference(line, use_ai=args.ai, api_key=api_key, ai_transport=ai_transport)
        db.upsert_reference(conn, ref)
        processed += 1
        if ref.needs_review:
            flagged += 1
    print(f"Processed {processed} line(s): {flagged} flagged needs_review.")
    return 0


def cmd_list(args, conn) -> int:
    refs = db.list_references(conn)
    if not refs:
        print("Library is empty.")
        return 0
    for ref in refs:
        authors_display = ", ".join(a.family for a in ref.authors) or "(no authors)"
        flag = " [NEEDS REVIEW]" if ref.needs_review else ""
        print(f"[{ref.ref_id}] {authors_display} ({ref.year or 'n.d.'}) — {ref.title} [{ref.ref_type}]{flag}")
    return 0


def cmd_remove(args, conn) -> int:
    ok = db.remove_reference(conn, args.ref_id)
    print("Removed." if ok else f"No reference with id {args.ref_id}.")
    return 0 if ok else 1


def cmd_format(args, conn) -> int:
    refs = db.get_references(conn, _parse_ids(args.ids))
    if not refs:
        print("No references found.")
        return 1
    module = styles.STYLES[args.style]
    ordered = _ordered_for_style(refs, args.style)
    print(f"--- {styles.STYLE_LABELS[args.style]} ---")
    for ref in ordered:
        print(module.format_reference(ref))
    return 0


def cmd_compare(args, conn) -> int:
    refs = db.get_references(conn, _parse_ids(args.ids))
    if not refs:
        print("No references found.")
        return 1
    for ref in refs:
        print(f"=== [{ref.ref_id}] {ref.title} ===")
        for key, module in styles.STYLES.items():
            print(f"{styles.STYLE_LABELS[key]}:")
            print(f"  {module.format_reference(ref)}")
        print()
    return 0


def cmd_render(args, conn) -> int:
    refs = db.get_references(conn, _parse_ids(args.ids))
    html = render_html.render(refs)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {args.output} ({len(refs)} reference(s)).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="citeforge", description="Batch citation-style converter")
    parser.add_argument("--db", default="citeforge.db", help="Path to the local SQLite library")
    sub = parser.add_subparsers(dest="command", required=True)

    p_bib = sub.add_parser("add-bibtex", help="Import references from a .bib file")
    p_bib.add_argument("file")

    p_doi = sub.add_parser("add-doi", help="Resolve a DOI (or a file of DOIs) via Crossref")
    p_doi.add_argument("doi_or_file")

    p_text = sub.add_parser("add-text", help="Parse free-text reference lines ('-' for stdin)")
    p_text.add_argument("file")
    p_text.add_argument("--ai", action="store_true", help="Use Claude Haiku for lines the regex pass can't structure")

    sub.add_parser("list", help="List the library")

    p_remove = sub.add_parser("remove", help="Remove a reference by id")
    p_remove.add_argument("ref_id", type=int)

    p_format = sub.add_parser("format", help="Print the library in one target citation style")
    p_format.add_argument("--style", required=True, choices=sorted(styles.STYLES))
    p_format.add_argument("--ids", default=None, help="Comma-separated reference ids (default: all)")

    p_compare = sub.add_parser("compare", help="Print all 4 styles side by side")
    p_compare.add_argument("--ids", default=None)

    p_render = sub.add_parser("render", help="Write a self-contained HTML comparison report")
    p_render.add_argument("--ids", default=None)
    p_render.add_argument("-o", "--output", default="citeforge_report.html")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    conn = db.connect(args.db)
    try:
        handlers = {
            "add-bibtex": lambda: cmd_add_bibtex(args, conn),
            "add-doi": lambda: cmd_add_doi(args, conn),
            "add-text": lambda: cmd_add_text(args, conn),
            "list": lambda: cmd_list(args, conn),
            "remove": lambda: cmd_remove(args, conn),
            "format": lambda: cmd_format(args, conn),
            "compare": lambda: cmd_compare(args, conn),
            "render": lambda: cmd_render(args, conn),
        }
        return handlers[args.command]()
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

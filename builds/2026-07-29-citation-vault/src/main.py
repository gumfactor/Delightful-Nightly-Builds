#!/usr/bin/env python3
"""Citation Vault — a local personal research reading & citation ledger."""

import argparse
import sys
from typing import Optional

import ai_client
import bibtex
import crossref_client
import render
import resurface
import store

DEFAULT_DB = "citation_vault.db"


def cmd_add(args) -> int:
    conn = store.connect(args.db)
    try:
        if args.manual:
            if not args.title:
                print("error: --manual requires --title", file=sys.stderr)
                return 1
            authors = [a.strip() for a in (args.authors or "").split(",") if a.strip()]
            paper_id = store.add_paper(
                conn,
                title=args.title,
                authors=authors,
                year=args.year,
                journal=args.journal,
                doi=None,
            )
            print(f"Added paper #{paper_id}: {args.title}")
            return 0

        if args.search:
            candidates = crossref_client.search(args.search)
            if not candidates:
                print(f"No Crossref results for query: {args.search}")
                return 1
            print(f"Top {len(candidates)} result(s) for '{args.search}':")
            for i, c in enumerate(candidates, 1):
                authors = ", ".join(c["authors"][:3]) or "Unknown authors"
                print(f"  [{i}] {c['title']} — {authors} ({c.get('year', 'n.d.')}) DOI: {c.get('doi')}")
            choice = args.pick
            if choice is None:
                print("Pass --pick N to add one of the results above.")
                return 0
            if choice < 1 or choice > len(candidates):
                print(f"error: --pick must be between 1 and {len(candidates)}", file=sys.stderr)
                return 1
            selected = candidates[choice - 1]
            paper_id = store.add_paper(conn, **selected)
            print(f"Added paper #{paper_id}: {selected['title']}")
            return 0

        if args.doi:
            paper = crossref_client.lookup_doi(args.doi)
            paper_id = store.add_paper(conn, **paper)
            print(f"Added paper #{paper_id}: {paper['title']}")
            return 0

        print("error: provide a DOI, --search, or --manual", file=sys.stderr)
        return 1
    except store.DuplicateDoiError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except crossref_client.CrossrefError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


def cmd_status(args) -> int:
    conn = store.connect(args.db)
    try:
        store.set_status(conn, args.id, args.new_status)
        print(f"Paper #{args.id} status set to {args.new_status}")
        return 0
    except (store.PaperNotFoundError, store.InvalidStatusError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


def cmd_note(args) -> int:
    conn = store.connect(args.db)
    try:
        note_id = store.add_note(conn, args.id, args.text)
        print(f"Note #{note_id} added to paper #{args.id}")
        return 0
    except store.PaperNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


def cmd_tag(args) -> int:
    conn = store.connect(args.db)
    try:
        paper = store.paper_to_dict(store.get_paper(conn, args.id))
        tags = set(paper["tags"])
        if args.tags:
            tags.update(t.strip() for t in args.tags.split(",") if t.strip())
        if args.ai_tag:
            suggested = ai_client.suggest_tags(paper["title"], paper["abstract"])
            tags.update(suggested)
        store.set_tags(conn, args.id, sorted(tags))
        print(f"Paper #{args.id} tags: {', '.join(sorted(tags)) or '(none)'}")
        return 0
    except store.PaperNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


def cmd_list(args) -> int:
    conn = store.connect(args.db)
    try:
        rows = store.list_papers(conn, status=args.status, tag=args.tag, search=args.search)
        if not rows:
            print("No papers match.")
            return 0
        for row in rows:
            p = store.paper_to_dict(row)
            authors = ", ".join(p["authors"][:2]) or "Unknown"
            print(f"#{p['id']:<4} [{p['status']:<7}] {p['title']} — {authors} ({p['year'] or 'n.d.'})")
        return 0
    finally:
        conn.close()


def cmd_show(args) -> int:
    conn = store.connect(args.db)
    try:
        p = store.paper_to_dict(store.get_paper(conn, args.id))
        notes = store.get_notes(conn, args.id)
        print(f"#{p['id']}: {p['title']}")
        print(f"Authors: {', '.join(p['authors']) or 'Unknown'}")
        print(f"Year: {p['year'] or 'n.d.'}  Journal: {p['journal'] or 'n/a'}  DOI: {p['doi'] or 'n/a'}")
        print(f"Status: {p['status']}  Tags: {', '.join(p['tags']) or '(none)'}")
        if p["abstract"]:
            print(f"Abstract: {p['abstract']}")
        print(f"Notes ({len(notes)}):")
        for n in notes:
            print(f"  [{n['created_at']}] {n['text']}")
        return 0
    except store.PaperNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


def cmd_resurface(args) -> int:
    conn = store.connect(args.db)
    try:
        rows = store.list_papers(conn)
        papers = [store.paper_to_dict(r) for r in rows]
        candidates = resurface.find_resurfacing_candidates(papers, days=args.days)
        if not candidates:
            print("Nothing to resurface right now.")
            return 0
        for c in candidates:
            old, new, shared = c["paper"], c["matched_with"], c["shared_tags"]
            if args.ai:
                rationale = ai_client.resurface_rationale(old, new, shared)
            else:
                rationale = f"shares tags [{', '.join(shared)}] with to-read paper \"{new['title']}\""
            print(f"#{old['id']} {old['title']} — {rationale}")
        return 0
    finally:
        conn.close()


def cmd_export(args) -> int:
    conn = store.connect(args.db)
    try:
        rows = store.list_papers(conn, status=args.status, tag=args.tag)
        papers = [store.paper_to_dict(r) for r in rows]
        output = bibtex.generate_bibtex(papers)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Wrote {len(papers)} entries to {args.out}")
        else:
            print(output, end="")
        return 0
    finally:
        conn.close()


def cmd_render(args) -> int:
    conn = store.connect(args.db)
    try:
        rows = store.list_papers(conn)
        papers = [store.paper_to_dict(r) for r in rows]
        notes_by_paper = {p["id"]: [dict(n) for n in store.get_notes(conn, p["id"])] for p in papers}
        html = render.render_dashboard(papers, notes_by_paper)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Dashboard written to {args.out}")
        return 0
    finally:
        conn.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="citation-vault", description=__doc__)
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to SQLite database")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add a paper by DOI, search, or manual entry")
    p_add.add_argument("doi", nargs="?", help="DOI to look up")
    p_add.add_argument("--search", help="Free-text Crossref search")
    p_add.add_argument("--pick", type=int, help="Index of search result to add (1-based)")
    p_add.add_argument("--manual", action="store_true", help="Add a paper with no DOI")
    p_add.add_argument("--title", help="Title (for --manual)")
    p_add.add_argument("--authors", help="Comma-separated authors (for --manual)")
    p_add.add_argument("--year", type=int, help="Year (for --manual)")
    p_add.add_argument("--journal", help="Journal/venue (for --manual)")
    p_add.set_defaults(func=cmd_add)

    p_status = sub.add_parser("status", help="Update a paper's reading status")
    p_status.add_argument("id", type=int)
    p_status.add_argument("new_status", choices=store.VALID_STATUSES)
    p_status.set_defaults(func=cmd_status)

    p_note = sub.add_parser("note", help="Add a timestamped note to a paper")
    p_note.add_argument("id", type=int)
    p_note.add_argument("text")
    p_note.set_defaults(func=cmd_note)

    p_tag = sub.add_parser("tag", help="Attach tags to a paper")
    p_tag.add_argument("id", type=int)
    p_tag.add_argument("tags", nargs="?", help="Comma-separated tags")
    p_tag.add_argument("--ai-tag", action="store_true", help="Suggest additional tags via Claude Haiku (or deterministic fallback)")
    p_tag.set_defaults(func=cmd_tag)

    p_list = sub.add_parser("list", help="List papers")
    p_list.add_argument("--status", choices=store.VALID_STATUSES)
    p_list.add_argument("--tag")
    p_list.add_argument("--search")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Show full detail for a paper")
    p_show.add_argument("id", type=int)
    p_show.set_defaults(func=cmd_show)

    p_resurface = sub.add_parser("resurface", help="List settled papers worth revisiting")
    p_resurface.add_argument("--days", type=int, default=60)
    p_resurface.add_argument("--ai", action="store_true", help="Generate an AI rationale (or deterministic fallback)")
    p_resurface.set_defaults(func=cmd_resurface)

    p_export = sub.add_parser("export", help="Export papers")
    p_export.add_argument("format", choices=["bibtex"])
    p_export.add_argument("--status", choices=store.VALID_STATUSES)
    p_export.add_argument("--tag")
    p_export.add_argument("--out")
    p_export.set_defaults(func=cmd_export)

    p_render = sub.add_parser("render", help="Generate the HTML dashboard")
    p_render.add_argument("--out", default="citation_vault.html")
    p_render.set_defaults(func=cmd_render)

    return parser


def main(argv: Optional[list] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Connectome — Personal Knowledge Graph Builder.

Indexes a folder of the user's own notes into a searchable, cross-linked
local knowledge base. See ../Manual.md for full usage.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backlinks
import extraction
import linking
import render
import storage

NOTE_EXTENSIONS = (".md", ".txt")
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "connectome.db")
DEFAULT_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")


def read_notes_dir(notes_dir: str) -> dict[str, str]:
    """Return {relative_path: body} for every .md/.txt file in notes_dir."""
    bodies = {}
    if not os.path.isdir(notes_dir):
        return bodies
    for entry in sorted(os.listdir(notes_dir)):
        if entry.lower().endswith(NOTE_EXTENSIONS):
            full_path = os.path.join(notes_dir, entry)
            with open(full_path, "r", encoding="utf-8") as f:
                bodies[entry] = f.read()
    return bodies


def derive_title(filename: str, body: str) -> str:
    """Use the first Markdown heading if present, otherwise the filename."""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    name = os.path.splitext(filename)[0]
    return name.replace("-", " ").replace("_", " ").title()


def content_hash(body: str) -> str:
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def cmd_index(args: argparse.Namespace) -> None:
    conn = storage.connect(args.db)
    notes_on_disk = read_notes_dir(args.notes_dir)
    api_key = os.environ.get("ANTHROPIC_API_KEY") if args.ai else None

    existing_notes = {row["path"]: row for row in storage.all_notes(conn)}
    seen_paths = set(notes_on_disk.keys())

    removed = [path for path in existing_notes if path not in seen_paths]
    for path in removed:
        storage.delete_note(conn, existing_notes[path]["id"])

    doc_freq_estimate = extraction.compute_document_frequencies(notes_on_disk)
    total_notes = len(notes_on_disk)

    changed_note_ids = []
    skipped = 0
    for path, body in notes_on_disk.items():
        digest = content_hash(body)
        existing = existing_notes.get(path)
        if existing and existing["content_hash"] == digest:
            skipped += 1
            continue
        title = derive_title(path, body)
        note_id = storage.upsert_note(conn, path, title, body, digest)
        base_concepts = extraction.extract_concepts(body, doc_freq_estimate, total_notes)
        final_concepts = extraction.enrich_with_claude(body, base_concepts, api_key)
        storage.replace_note_concepts(conn, note_id, final_concepts)
        changed_note_ids.append(note_id)

    storage.recompute_doc_frequencies(conn)

    if changed_note_ids or removed:
        all_note_concepts = storage.get_all_note_concepts(conn)
        doc_freq = storage.get_doc_frequencies(conn)
        links = linking.compute_links(all_note_concepts, doc_freq, len(all_note_concepts))
        storage.replace_all_links(conn, links)

    conn.commit()
    print(f"Indexed {len(changed_note_ids)} new/changed note(s), skipped {skipped} unchanged, "
          f"removed {len(removed)}. Total notes: {len(notes_on_disk)}.")


def cmd_search(args: argparse.Namespace) -> None:
    conn = storage.connect(args.db)
    results = storage.search_notes(conn, args.query)
    if not results:
        print(f"No notes match '{args.query}'.")
        return
    for row in results:
        print(f"- {row['title']} ({row['path']})")


def cmd_related(args: argparse.Namespace) -> None:
    conn = storage.connect(args.db)
    note = storage.get_note_by_path(conn, args.note) or _find_by_title(conn, args.note)
    if not note:
        print(f"No note found matching '{args.note}'.")
        return
    all_links = storage.get_all_links(conn)
    related = linking.related_to(note["id"], all_links)
    if not related:
        print(f"'{note['title']}' has no related notes yet.")
        return
    id_to_title = {row["id"]: row["title"] for row in storage.all_notes(conn)}
    print(f"Notes related to '{note['title']}':")
    for link in related:
        other_title = id_to_title.get(link.note_b, "?")
        shared = ", ".join(link.shared_concepts[:5])
        print(f"  - {other_title} (score {link.score:.3f}; shared: {shared})")


def _find_by_title(conn, title: str):
    for row in storage.all_notes(conn):
        if row["title"].lower() == title.lower():
            return row
    return None


def cmd_stats(args: argparse.Namespace) -> None:
    conn = storage.connect(args.db)
    notes = storage.all_notes(conn)
    doc_freq = storage.get_doc_frequencies(conn)
    all_links = storage.get_all_links(conn)

    print(f"Notes: {len(notes)}")
    print(f"Concepts: {len(doc_freq)}")
    print(f"Links: {len(all_links)}")

    if notes:
        avg_links = (2 * len(all_links)) / len(notes)
        print(f"Average links per note: {avg_links:.2f}")

    link_counts: dict[int, int] = {}
    for link in all_links:
        link_counts[link.note_a] = link_counts.get(link.note_a, 0) + 1
        link_counts[link.note_b] = link_counts.get(link.note_b, 0) + 1
    id_to_title = {row["id"]: row["title"] for row in notes}
    hubs = sorted(link_counts.items(), key=lambda pair: pair[1], reverse=True)[:5]
    if hubs:
        print("Most-connected notes:")
        for note_id, count in hubs:
            print(f"  - {id_to_title.get(note_id, '?')} ({count} links)")


def cmd_backlinks(args: argparse.Namespace) -> None:
    conn = storage.connect(args.db)
    notes = storage.all_notes(conn)
    all_links = storage.get_all_links(conn)
    plans = backlinks.plan_backlinks(notes, all_links, top_n=args.top)
    changed = [plan for plan in plans if plan["changed"]]

    if not changed:
        print("No backlink changes to make — every note's See Also block is already up to date.")
        return

    if not args.write:
        print(f"Dry run: {len(changed)} note(s) would be updated. Re-run with --write to apply.\n")
        for plan in changed:
            print(backlinks.diff_text(plan["path"], plan["old_body"], plan["new_body"]))
        return

    if not args.skip_git_check:
        problem = backlinks.git_baseline_problem(args.notes_dir)
        if problem:
            print(
                f"Refusing to write: {problem}, so there is no reliable way to review or undo "
                "these edits. Commit your notes first (`git init && git add -A && git commit`), "
                "or pass --skip-git-check to proceed anyway (not recommended)."
            )
            raise SystemExit(1)

    written, stale = backlinks.write_plans(args.notes_dir, changed)
    if written:
        written_set = set(written)
        for plan in changed:
            if plan["path"] in written_set:
                digest = backlinks.content_hash(plan["new_body"])
                storage.upsert_note(conn, plan["path"], plan["title"], plan["new_body"], digest)
        conn.commit()
    print(f"Wrote backlinks to {len(written)} note(s).")
    if stale:
        print(
            f"Skipped {len(stale)} note(s) that changed on disk since the last `index` run "
            f"(re-run `index` then `backlinks` to include them): {', '.join(stale)}"
        )


def cmd_build(args: argparse.Namespace) -> None:
    conn = storage.connect(args.db)
    output_path = render.render_knowledge_base(conn, args.output_dir)
    print(f"Knowledge base written to {output_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="connectome", description=__doc__)
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to the SQLite database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_index = subparsers.add_parser("index", help="Index a folder of notes")
    p_index.add_argument("--notes-dir", default="sample_notes", help="Folder of .md/.txt notes")
    p_index.add_argument("--ai", action="store_true",
                          help="Use ANTHROPIC_API_KEY (if set) to refine concept extraction")
    p_index.set_defaults(func=cmd_index)

    p_search = subparsers.add_parser("search", help="Search notes by title/body/concept")
    p_search.add_argument("query")
    p_search.set_defaults(func=cmd_search)

    p_related = subparsers.add_parser("related", help="Show notes related to a given note")
    p_related.add_argument("note", help="Note title or file path")
    p_related.set_defaults(func=cmd_related)

    p_stats = subparsers.add_parser("stats", help="Show corpus statistics")
    p_stats.set_defaults(func=cmd_stats)

    p_build = subparsers.add_parser("build", help="Render the HTML knowledge base")
    p_build.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)
    p_build.set_defaults(func=cmd_build)

    p_backlinks = subparsers.add_parser(
        "backlinks", help="Write [[wiki-link]] See Also blocks into your note files"
    )
    p_backlinks.add_argument("--notes-dir", default="sample_notes",
                              help="Folder of .md/.txt notes — must match what was last indexed")
    p_backlinks.add_argument("--top", type=int, default=5, help="Max related notes per See Also block")
    p_backlinks.add_argument("--write", action="store_true",
                              help="Actually write changes (default is dry-run: prints a diff, touches nothing)")
    p_backlinks.add_argument("--skip-git-check", action="store_true",
                              help="Allow writing even if --notes-dir isn't a git repo (not recommended: no undo path)")
    p_backlinks.set_defaults(func=cmd_backlinks)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()

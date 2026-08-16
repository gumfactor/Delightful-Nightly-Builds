"""Curriculum Atlas command-line interface."""

from __future__ import annotations

import argparse
import datetime
import sys

from . import ai_enrich, analysis, parser as concept_parser, report, store

DEFAULT_DB = "curriculum_atlas.db"


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _require_course(conn, name: str):
    course = store.get_course(conn, name)
    if course is None:
        print(f"error: no course named '{name}'. Run 'add-course' first.", file=sys.stderr)
        sys.exit(1)
    return course


def cmd_add_course(args) -> int:
    conn = store.connect(args.db)
    course = store.add_course(conn, args.name)
    print(f"Course '{course.name}' ready (id={course.id}).")
    return 0


def cmd_list_courses(args) -> int:
    conn = store.connect(args.db)
    courses = store.list_courses(conn)
    if not courses:
        print("No courses registered yet. Use 'add-course' to add one.")
        return 0
    for c in courses:
        docs = store.list_documents(conn, course_id=c.id)
        terms = sorted({d.term for d in docs})
        print(f"{c.name}  ({len(docs)} document(s), terms: {', '.join(terms) or 'none'})")
    return 0


def cmd_ingest(args) -> int:
    conn = store.connect(args.db)
    course = _require_course(conn, args.course)

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as exc:
        print(f"error: could not read '{args.file}': {exc}", file=sys.stderr)
        return 1

    if args.ai_mark:
        api_key = ai_enrich.get_api_key()
        text_for_parsing = ai_enrich.auto_mark_concepts(text, api_key)
    else:
        text_for_parsing = text

    parsed = concept_parser.parse_document(text_for_parsing)
    store_parsed = store.ParsedDocument(
        concepts=[
            store.Concept(id=0, document_id=0, display_name=c.display_name,
                          normalized_name=c.normalized_name, source=c.source)
            for c in parsed.concepts
        ],
        objectives=[
            store.Objective(id=0, document_id=0, text=o.text) for o in parsed.objectives
        ],
    )
    doc = store.ingest_document(
        conn,
        course_id=course.id,
        term=args.term,
        source_path=args.file,
        ingested_at=_now_iso(),
        raw_char_count=len(text),
        parsed=store_parsed,
    )
    print(
        f"Ingested '{args.file}' into {course.name} / {args.term}: "
        f"{len(parsed.concepts)} concept(s), {len(parsed.objectives)} objective(s) "
        f"(document id={doc.id})."
    )
    return 0


def cmd_concepts(args) -> int:
    conn = store.connect(args.db)
    course_id = None
    if args.course:
        course_id = _require_course(conn, args.course).id

    rows = store.list_concepts(conn, course_id=course_id, term=args.term)
    if not rows:
        print("No concepts found for that scope.")
        return 0

    if args.ai_notes:
        api_key = ai_enrich.get_api_key()
        needed = []
        seen = set()
        for r in rows:
            norm = r["normalized_name"]
            if norm in seen:
                continue
            seen.add(norm)
            if store.get_cached_note(conn, norm) is None:
                needed.append((norm, r["display_name"]))
        if needed and api_key:
            notes = ai_enrich.generate_concept_notes(needed, api_key)
            now = _now_iso()
            for norm, note in notes.items():
                store.save_note(conn, norm, note, now)

    for r in rows:
        note = store.get_cached_note(conn, r["normalized_name"]) or ""
        line = f"[{r['source']:9}] {r['display_name']}  ({r['course_name']} / {r['term']})"
        if note:
            line += f"\n            {note}"
        print(line)
    return 0


def cmd_overlap(args) -> int:
    conn = store.connect(args.db)
    rows = store.list_concepts(conn)
    results = analysis.find_overlap(rows)
    if not results:
        print("No concepts currently appear in more than one course.")
        return 0
    for r in results:
        locs = ", ".join(f"{l['course_name']} ({l['term']})" for l in r["locations"])
        print(f"{r['display_name']}  — in {r['course_count']} course(s): {locs}")
    return 0


def cmd_gaps(args) -> int:
    conn = store.connect(args.db)
    course = _require_course(conn, args.course)
    concepts = store.list_concepts(conn, course_id=course.id, term=args.term)
    objectives = store.list_objectives(conn, course_id=course.id, term=args.term)
    if not objectives:
        print("No objectives extracted for that course/term.")
        return 0
    results = analysis.find_gaps(objectives, concepts, threshold=args.threshold)
    for r in results:
        status = "FLAGGED" if r["flagged"] else "covered"
        match = r["best_concept"] or "—"
        print(f"[{status:7}] score={r['best_score']:.2f}  best_match={match}  — {r['objective_text']}")
    return 0


def cmd_diff(args) -> int:
    conn = store.connect(args.db)
    course = _require_course(conn, args.course)
    concepts_a = store.list_concepts(conn, course_id=course.id, term=args.term_a)
    concepts_b = store.list_concepts(conn, course_id=course.id, term=args.term_b)
    result = analysis.diff_terms(concepts_a, concepts_b)
    print(f"Diff for {course.name}: {args.term_a} -> {args.term_b}")
    print(f"  Added:   {', '.join(result['added']) or '(none)'}")
    print(f"  Removed: {', '.join(result['removed']) or '(none)'}")
    print(f"  Kept:    {', '.join(result['kept']) or '(none)'}")
    return 0


def _build_dashboard_payload(conn) -> dict:
    courses = store.list_courses(conn)
    all_concepts = store.list_concepts(conn)
    overlap = analysis.find_overlap(all_concepts)

    course_payload = []
    for c in courses:
        docs = store.list_documents(conn, course_id=c.id)
        terms = sorted({d.term for d in docs})
        term_blocks = []
        for term in terms:
            term_docs = [d for d in docs if d.term == term]
            concepts = store.list_concepts(conn, course_id=c.id, term=term)
            objectives = store.list_objectives(conn, course_id=c.id, term=term)
            gaps = analysis.find_gaps(objectives, concepts)
            concept_payload = []
            for concept in concepts:
                note = store.get_cached_note(conn, concept["normalized_name"]) or ""
                concept_payload.append({
                    "display_name": concept["display_name"],
                    "source": concept["source"],
                    "note": note,
                })
            term_blocks.append({
                "term": term,
                "documents": [{"source_path": d.source_path} for d in term_docs],
                "concepts": concept_payload,
                "objectives": gaps,
            })
        course_payload.append({"name": c.name, "terms": term_blocks})

    return {
        "generated_at": _now_iso(),
        "courses": course_payload,
        "overlap": overlap,
    }


def cmd_render(args) -> int:
    conn = store.connect(args.db)

    if args.ai_notes:
        api_key = ai_enrich.get_api_key()
        rows = store.list_concepts(conn)
        needed = []
        seen = set()
        for r in rows:
            norm = r["normalized_name"]
            if norm in seen:
                continue
            seen.add(norm)
            if store.get_cached_note(conn, norm) is None:
                needed.append((norm, r["display_name"]))
        if needed and api_key:
            notes = ai_enrich.generate_concept_notes(needed, api_key)
            now = _now_iso()
            for norm, note in notes.items():
                store.save_note(conn, norm, note, now)

    payload = _build_dashboard_payload(conn)
    report.render_dashboard(payload, args.out)
    print(f"Dashboard written to {args.out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="curriculum-atlas", description="Curriculum Atlas")
    p.add_argument("--db", default=DEFAULT_DB, help="path to the SQLite database")
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("add-course", help="register a course")
    sp.add_argument("--name", required=True)
    sp.set_defaults(func=cmd_add_course)

    sp = sub.add_parser("list-courses", help="list registered courses")
    sp.set_defaults(func=cmd_list_courses)

    sp = sub.add_parser("ingest", help="ingest a syllabus/lecture file into a course+term")
    sp.add_argument("--course", required=True)
    sp.add_argument("--term", required=True)
    sp.add_argument("--file", required=True)
    sp.add_argument("--ai-mark", action="store_true",
                     help="use Claude Haiku to auto-insert [[concept]] markers when none are present")
    sp.set_defaults(func=cmd_ingest)

    sp = sub.add_parser("concepts", help="list extracted concepts")
    sp.add_argument("--course")
    sp.add_argument("--term")
    sp.add_argument("--ai-notes", action="store_true",
                     help="use Claude Haiku to generate one-sentence notes for concepts without one")
    sp.set_defaults(func=cmd_concepts)

    sp = sub.add_parser("overlap", help="show concepts shared across more than one course")
    sp.set_defaults(func=cmd_overlap)

    sp = sub.add_parser("gaps", help="flag objectives not clearly covered by any extracted concept")
    sp.add_argument("--course", required=True)
    sp.add_argument("--term", required=True)
    sp.add_argument("--threshold", type=float, default=analysis.DEFAULT_GAP_THRESHOLD)
    sp.set_defaults(func=cmd_gaps)

    sp = sub.add_parser("diff", help="compare a course's concept set between two terms")
    sp.add_argument("--course", required=True)
    sp.add_argument("--term-a", required=True)
    sp.add_argument("--term-b", required=True)
    sp.set_defaults(func=cmd_diff)

    sp = sub.add_parser("render", help="render the self-contained HTML dashboard")
    sp.add_argument("--out", default="report.html")
    sp.add_argument("--ai-notes", action="store_true",
                     help="generate concept notes via Claude Haiku before rendering")
    sp.set_defaults(func=cmd_render)

    return p


def main(argv=None) -> int:
    parser_obj = build_parser()
    args = parser_obj.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

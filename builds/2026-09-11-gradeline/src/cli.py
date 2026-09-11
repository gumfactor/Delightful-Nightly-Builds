"""GradeLine CLI: init-rubric, grade, list, show, render, compare."""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import ai, checks, render, rubric as rubric_mod, similarity, storage
from .parser import load_submissions

DEFAULT_THRESHOLD = 0.75


def _default_db_path(rubric_path: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(rubric_path)) or ".", "gradeline.db")


def _score_criteria(
    text: str,
    criteria: list[rubric_mod.Criterion],
    use_ai: bool,
    api_key: str | None,
    transport: ai.Transport,
) -> list[dict]:
    results = []
    for crit in criteria:
        if crit.manual_only:
            score = None
            hits = None
        else:
            score, hits = checks.keyword_coverage_score(text, crit.keywords, crit.min_keyword_hits, crit.max_points)

        feedback = None
        if use_ai and api_key:
            feedback = ai.draft_feedback(crit.name, crit.description, text, api_key, transport=transport)
        if feedback is None:
            feedback = ai.deterministic_feedback(
                crit.name, hits or 0, crit.min_keyword_hits, score if score is not None else 0.0, crit.max_points
            )

        results.append(
            {
                "id": crit.id,
                "name": crit.name,
                "score": score,
                "max_points": crit.max_points,
                "manual_only": crit.manual_only,
                "hits": hits,
                "min_hits": crit.min_keyword_hits,
                "feedback": feedback,
            }
        )
    return results


def grade_batch(
    submissions_path: str,
    rubric_path: str,
    db_path: str,
    use_ai: bool = False,
    threshold: float = DEFAULT_THRESHOLD,
    api_key: str | None = None,
    transport: ai.Transport = ai.default_transport,
) -> int:
    """Grades every submission at `submissions_path` against the rubric at
    `rubric_path`, persists a new batch to `db_path`, and returns the new
    batch's id."""
    loaded_rubric = rubric_mod.load_rubric(rubric_path)
    submissions = load_submissions(submissions_path)
    api_key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY", "")

    conn = storage.connect(db_path)
    with open(rubric_path, "r", encoding="utf-8") as f:
        rubric_json = f.read()
    batch_id = storage.create_batch(conn, loaded_rubric.name, rubric_json, os.path.abspath(submissions_path))

    submission_ids = []
    for sub in submissions:
        compliance = checks.check_compliance(sub.text, loaded_rubric)
        criteria_results = _score_criteria(sub.text, loaded_rubric.criteria, use_ai, api_key, transport)
        sub_id = storage.add_submission(
            conn,
            batch_id,
            sub.identifier,
            compliance.word_count,
            compliance.citation_count,
            compliance.flesch_score,
            {
                "word_count_ok": compliance.word_count_ok,
                "sections_found": compliance.sections_found,
                "sections_ok": compliance.sections_ok,
                "citations_ok": compliance.citations_ok,
            },
            criteria_results,
            None,
        )
        submission_ids.append(sub_id)

    pairs = similarity.find_similar_pairs([sub.text for sub in submissions], threshold=threshold)
    for pair in pairs:
        storage.add_similarity_pair(
            conn, batch_id, submission_ids[pair.index_a], submission_ids[pair.index_b], pair.score
        )

    conn.close()
    return batch_id


def _build_report_data(conn, batch_id: int) -> tuple[dict, list[dict], list[dict]]:
    batch_row = storage.get_batch(conn, batch_id)
    if batch_row is None:
        raise ValueError(f"No batch with id {batch_id}")
    submission_rows = storage.get_submissions(conn, batch_id)
    id_to_identifier = {row["id"]: row["identifier"] for row in submission_rows}

    submissions = []
    for row in submission_rows:
        submissions.append(
            {
                "identifier": row["identifier"],
                "word_count": row["word_count"],
                "citation_count": row["citation_count"],
                "flesch_score": row["flesch_score"],
                "compliance": json.loads(row["compliance_json"]),
                "criteria": json.loads(row["criteria_json"]),
            }
        )

    similarity_rows = storage.get_similarity_pairs(conn, batch_id)
    similarity_pairs = [
        {
            "a": id_to_identifier[row["submission_a_id"]],
            "b": id_to_identifier[row["submission_b_id"]],
            "score": row["score"],
        }
        for row in similarity_rows
    ]

    batch = {
        "rubric_name": batch_row["rubric_name"],
        "source_path": batch_row["source_path"],
        "graded_at": batch_row["graded_at"],
    }
    return batch, submissions, similarity_pairs


def render_batch(db_path: str, batch_id: int, out_path: str) -> str:
    conn = storage.connect(db_path)
    batch, submissions, similarity_pairs = _build_report_data(conn, batch_id)
    conn.close()
    html = render.render(batch, submissions, similarity_pairs)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


def _print_batch_summary(conn, batch_id: int) -> None:
    batch, submissions, similarity_pairs = _build_report_data(conn, batch_id)
    print(f"Batch #{batch_id} — {batch['rubric_name']}")
    print(f"  Source: {batch['source_path']}")
    print(f"  Graded: {batch['graded_at']}")
    print(f"  Submissions: {len(submissions)}")
    non_compliant = [s for s in submissions if not (s["compliance"]["word_count_ok"] and s["compliance"]["sections_ok"] and s["compliance"]["citations_ok"])]
    print(f"  Non-compliant: {len(non_compliant)}")
    for sub in non_compliant:
        issues = []
        if not sub["compliance"]["word_count_ok"]:
            issues.append("word count")
        if not sub["compliance"]["sections_ok"]:
            issues.append("missing sections")
        if not sub["compliance"]["citations_ok"]:
            issues.append("citations")
        print(f"    - {sub['identifier']}: {', '.join(issues)}")
    if similarity_pairs:
        print(f"  Similarity flags: {len(similarity_pairs)}")
        for pair in similarity_pairs:
            print(f"    - {pair['a']} <-> {pair['b']}: {pair['score']*100:.1f}%")
    else:
        print("  Similarity flags: 0")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gradeline", description="Batch rubric-compliance grading assistant")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init-rubric", help="Scaffold a starter rubric JSON file")
    p_init.add_argument("path", help="Where to write the starter rubric")

    p_grade = sub.add_parser("grade", help="Grade a batch of submissions against a rubric")
    p_grade.add_argument("submissions_path", help="Folder of .txt/.md files, or a single delimited file")
    p_grade.add_argument("--rubric", required=True, help="Path to the rubric JSON file")
    p_grade.add_argument("--db", help="SQLite db path (default: gradeline.db next to the rubric)")
    p_grade.add_argument("--ai", action="store_true", help="Draft AI feedback (requires ANTHROPIC_API_KEY)")
    p_grade.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="Similarity flag threshold (0-1)")
    p_grade.add_argument("--json", action="store_true", help="Print the batch summary as JSON")

    p_list = sub.add_parser("list", help="List past batches")
    p_list.add_argument("--db", required=True)

    p_show = sub.add_parser("show", help="Show a batch's summary")
    p_show.add_argument("batch_id", type=int)
    p_show.add_argument("--db", required=True)

    p_render = sub.add_parser("render", help="Render a batch as a self-contained HTML report")
    p_render.add_argument("batch_id", type=int)
    p_render.add_argument("--db", required=True)
    p_render.add_argument("--out", default="gradeline_report.html")

    p_compare = sub.add_parser("compare", help="Compare class-level criterion averages across two batches")
    p_compare.add_argument("batch_id_a", type=int)
    p_compare.add_argument("batch_id_b", type=int)
    p_compare.add_argument("--db", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.command == "init-rubric":
        rubric_mod.write_starter_rubric(args.path)
        print(f"Wrote starter rubric to {args.path}")
        return 0

    if args.command == "grade":
        db_path = args.db or _default_db_path(args.rubric)
        try:
            batch_id = grade_batch(
                args.submissions_path, args.rubric, db_path, use_ai=args.ai, threshold=args.threshold
            )
        except (rubric_mod.RubricError, ValueError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        conn = storage.connect(db_path)
        if args.json:
            batch, submissions, similarity_pairs = _build_report_data(conn, batch_id)
            print(json.dumps({"batch": batch, "submissions": submissions, "similarity_pairs": similarity_pairs}, indent=2))
        else:
            _print_batch_summary(conn, batch_id)
        conn.close()
        return 0

    if args.command == "list":
        conn = storage.connect(args.db)
        rows = storage.list_batches(conn)
        if not rows:
            print("No batches yet.")
        for row in rows:
            print(f"#{row['id']}  {row['graded_at']}  {row['rubric_name']}  ({row['source_path']})")
        conn.close()
        return 0

    if args.command == "show":
        conn = storage.connect(args.db)
        try:
            _print_batch_summary(conn, args.batch_id)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            conn.close()
            return 1
        conn.close()
        return 0

    if args.command == "render":
        try:
            out_path = render_batch(args.db, args.batch_id, args.out)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f"Wrote report to {out_path}")
        return 0

    if args.command == "compare":
        conn = storage.connect(args.db)
        try:
            _, subs_a, _ = _build_report_data(conn, args.batch_id_a)
            _, subs_b, _ = _build_report_data(conn, args.batch_id_b)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            conn.close()
            return 1
        conn.close()
        avgs_a = {a["name"]: a["avg_score"] for a in render.build_payload({}, subs_a, [])["criterion_averages"]}
        avgs_b = {b["name"]: b["avg_score"] for b in render.build_payload({}, subs_b, [])["criterion_averages"]}
        print(f"Comparing batch #{args.batch_id_a} vs #{args.batch_id_b}")
        for name in sorted(set(avgs_a) | set(avgs_b)):
            a_val = avgs_a.get(name, "n/a")
            b_val = avgs_b.get(name, "n/a")
            print(f"  {name}: {a_val} -> {b_val}")
        return 0

    return 1

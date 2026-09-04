"""CaseForge command-line interface.

    python -m src.main generate --course "Stress and Coping" --query "cortisol stress reactivity coping"
    python -m src.main list
    python -m src.main show <pmid>
    python -m src.main search <keyword>
    python -m src.main export markdown --out cases.md
    python -m src.main render --out cases.html
"""
import argparse
import os
import sys
from typing import List

from . import ai_client, db, extraction, pubmed_client, questions, render, vignette

_DB_FILENAME = "caseforge.db"
_MIN_N = 1
_MAX_N = 50
_SEARCH_BUFFER_MULTIPLIER = 3


def _db_path() -> str:
    build_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(build_root, _DB_FILENAME)


def _build_citation(article: pubmed_client.PubMedArticle) -> str:
    journal = f" {article.journal}." if article.journal else ""
    year = f" ({article.pub_year})" if article.pub_year else ""
    return f'{article.title}.{journal}{year} PMID:{article.pmid}'


def cmd_generate(args: argparse.Namespace, conn) -> int:
    if not args.course.strip():
        print("error: --course must not be empty", file=sys.stderr)
        return 2
    if not args.query.strip():
        print("error: --query must not be empty", file=sys.stderr)
        return 2
    if not (_MIN_N <= args.n <= _MAX_N):
        print(f"error: --n must be between {_MIN_N} and {_MAX_N}", file=sys.stderr)
        return 2

    try:
        pmids = pubmed_client.search_pmids(
            args.query, retmax=args.n * _SEARCH_BUFFER_MULTIPLIER
        )
    except pubmed_client.PubMedError as exc:
        print(f"error: PubMed search failed: {exc}", file=sys.stderr)
        return 1

    if args.force:
        target_pmids = pmids[: args.n]
    else:
        target_pmids = [p for p in pmids if not db.pmid_exists(conn, p)][: args.n]

    if not target_pmids:
        print(
            "No new articles found for this query "
            "(all already in the library, or PubMed returned none)."
        )
        return 0

    try:
        articles = pubmed_client.fetch_articles(target_pmids)
    except pubmed_client.PubMedError as exc:
        print(f"error: PubMed fetch failed: {exc}", file=sys.stderr)
        return 1

    if not articles:
        print("PubMed returned no usable articles (no title/abstract) for this query.")
        return 0

    created = 0
    for article in articles:
        facts = extraction.extract_all(article.abstract)
        vignette_text = vignette.assemble_deterministic_vignette(
            article.title, article.journal, article.pub_year, facts
        )
        source = "deterministic"
        if args.ai_polish:
            vignette_text, source = vignette.polish_with_ai(
                vignette_text, article.title, facts, args.register, ai_client.call_claude
            )
        discussion_questions = questions.generate_discussion_questions(facts)

        case = db.Case(
            pmid=article.pmid,
            course=args.course,
            topic_query=args.query,
            title=article.title,
            journal=article.journal,
            pub_year=article.pub_year,
            citation=_build_citation(article),
            abstract_text=article.abstract,
            sample_size=facts.get("sample_size"),
            population=facts.get("population"),
            methodology=facts.get("methodology"),
            effect_size_text=facts.get("effect_size_text"),
            p_value_text=facts.get("p_value_text"),
            vignette_text=vignette_text,
            vignette_source=source,
            discussion_questions=discussion_questions,
            created_at=db.now_iso(),
        )
        db.insert_case(conn, case, overwrite=args.force)
        created += 1
        print(f"Generated case for PMID {article.pmid}: {article.title[:80]}")

    print(f"\n{created} case(s) added to course '{args.course}'.")
    return 0


def cmd_list(args: argparse.Namespace, conn) -> int:
    cases = db.list_cases(conn, course=args.course)
    if not cases:
        print("No cases in the library yet. Run 'generate' first.")
        return 0
    for case in cases:
        print(f"{case.pmid}  [{case.course}]  {case.title[:70]}")
    return 0


def cmd_show(args: argparse.Namespace, conn) -> int:
    case = db.get_case(conn, args.pmid)
    if case is None:
        print(f"error: no case found for PMID {args.pmid}", file=sys.stderr)
        return 1
    print(f"Title: {case.title}")
    print(f"Citation: {case.citation}")
    print(f"Course: {case.course}")
    print(
        "Facts: "
        f"sample_size={case.sample_size} methodology={case.methodology} "
        f"population={case.population} effect_size={case.effect_size_text} "
        f"p_value={case.p_value_text}"
    )
    print(f"\nVignette ({case.vignette_source}):\n{case.vignette_text}")
    print("\nDiscussion Questions:")
    for index, question in enumerate(case.discussion_questions, start=1):
        print(f"  {index}. {question}")
    return 0


def cmd_search(args: argparse.Namespace, conn) -> int:
    cases = db.search_cases(conn, args.keyword)
    if not cases:
        print(f"No cases match '{args.keyword}'.")
        return 0
    for case in cases:
        print(f"{case.pmid}  [{case.course}]  {case.title[:70]}")
    return 0


def _case_to_markdown(case: db.Case) -> List[str]:
    lines = [
        f"## {case.title}",
        "",
        f"*{case.citation}*",
        "",
        case.vignette_text,
        "",
        "**Discussion Questions:**",
        "",
    ]
    lines.extend(f"- {question}" for question in case.discussion_questions)
    lines.append("")
    return lines


def cmd_export(args: argparse.Namespace, conn) -> int:
    if args.format != "markdown":
        print(f"error: unsupported export format '{args.format}'", file=sys.stderr)
        return 2
    cases = db.list_cases(conn, course=args.course)
    if not cases:
        print("No cases to export.")
        return 0

    lines: List[str] = []
    for case in cases:
        lines.extend(_case_to_markdown(case))
    content = "\n".join(lines)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(content)
        print(f"Exported {len(cases)} case(s) to {args.out}")
    else:
        print(content)
    return 0


def cmd_render(args: argparse.Namespace, conn) -> int:
    cases = db.list_cases(conn)
    html = render.render_dashboard(cases)
    out_path = args.out
    with open(out_path, "w", encoding="utf-8") as handle:
        handle.write(html)
    print(f"Rendered {len(cases)} case(s) to {out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="caseforge",
        description="Generate real-literature-grounded teaching cases from live PubMed data.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser(
        "generate", help="Fetch real PubMed articles and generate teaching cases"
    )
    generate_parser.add_argument("--course", required=True)
    generate_parser.add_argument("--query", required=True)
    generate_parser.add_argument("--n", type=int, default=3)
    generate_parser.add_argument("--ai-polish", action="store_true")
    generate_parser.add_argument(
        "--register", default="undergrad", choices=["undergrad", "graduate", "public"]
    )
    generate_parser.add_argument("--force", action="store_true")
    generate_parser.set_defaults(func=cmd_generate)

    list_parser = subparsers.add_parser("list", help="List cases in the library")
    list_parser.add_argument("--course")
    list_parser.set_defaults(func=cmd_list)

    show_parser = subparsers.add_parser("show", help="Show a single case in full")
    show_parser.add_argument("pmid")
    show_parser.set_defaults(func=cmd_show)

    search_parser = subparsers.add_parser("search", help="Search cases by keyword")
    search_parser.add_argument("keyword")
    search_parser.set_defaults(func=cmd_search)

    export_parser = subparsers.add_parser("export", help="Export cases")
    export_parser.add_argument("format", choices=["markdown"])
    export_parser.add_argument("--course")
    export_parser.add_argument("--out")
    export_parser.set_defaults(func=cmd_export)

    render_parser = subparsers.add_parser("render", help="Render the HTML dashboard")
    render_parser.add_argument("--out", default="cases.html")
    render_parser.set_defaults(func=cmd_render)

    return parser


def main(argv: List[str] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    conn = db.connect(_db_path())
    try:
        return args.func(args, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())

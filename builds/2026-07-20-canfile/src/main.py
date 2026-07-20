"""CanFile CLI — Canadian Ownership Knowledge Cards.

Usage:
    python main.py add "Tim Hortons"
    python main.py show "Tim Hortons"
    python main.py list
    python main.py search canada
    python main.py export-html [output.html]
"""
from __future__ import annotations

import argparse
import sys
from typing import Any

try:
    from . import assessment, html_report, storage, wikidata_client, wikipedia_client
except ImportError:  # allows `python src/main.py` without package install
    import assessment
    import html_report
    import storage
    import wikidata_client
    import wikipedia_client

DEFAULT_DB_PATH = "canfile.db"
DEFAULT_HTML_PATH = "canfile_report.html"


class LookupFailure(RuntimeError):
    """Raised when a company cannot be resolved to a usable Wikidata entity."""


def _gather_facts(qid: str) -> tuple[dict[str, Any], list[str]]:
    """Fetch claims for `qid`, resolve one hop of parent/owner country, and
    return (facts_dict_of_labels, source_urls)."""
    claims = wikidata_client.get_claims(qid)
    referenced_ids = [
        entity_id
        for prop in ("P17", "P159", "P749", "P127", "P31")
        for entity_id in claims.get(prop, [])
    ]
    labels = wikidata_client.resolve_labels(referenced_ids)

    def label_list(prop: str) -> list[str]:
        return [labels[qid_] for qid_ in claims.get(prop, []) if qid_ in labels]

    facts: dict[str, Any] = {
        "country_labels": label_list("P17"),
        "headquarters_labels": label_list("P159"),
        "parent_organization_labels": label_list("P749"),
        "owned_by_labels": label_list("P127"),
        "instance_of_labels": label_list("P31"),
        "parent_country_labels": [],
    }

    source_urls = [wikidata_client.entity_url(qid)]

    parent_ids = claims.get("P749", []) + claims.get("P127", [])
    if parent_ids:
        parent_qid = parent_ids[0]
        parent_claims = wikidata_client.get_claims(parent_qid)
        parent_country_ids = parent_claims.get("P17", [])
        if parent_country_ids:
            parent_country_labels = wikidata_client.resolve_labels(parent_country_ids)
            facts["parent_country_labels"] = [
                parent_country_labels[qid_]
                for qid_ in parent_country_ids
                if qid_ in parent_country_labels
            ]
        source_urls.append(wikidata_client.entity_url(parent_qid))

    return facts, source_urls


def add_company(company_name: str, db_path: str = DEFAULT_DB_PATH, api_key: str | None = None) -> dict[str, Any]:
    candidates = wikidata_client.search_entity(company_name)
    if not candidates:
        raise LookupFailure(f'No Wikidata entity found for "{company_name}".')

    best = candidates[0]
    qid = best["id"]

    facts, source_urls = _gather_facts(qid)

    summary_title = best["label"] or company_name
    summary = wikipedia_client.get_summary(summary_title)
    wikipedia_summary = summary["extract"] if summary else None
    if summary and summary.get("url"):
        source_urls.append(summary["url"])

    deterministic_result = assessment.deterministic_assessment(company_name, facts)
    assessment_text = assessment.enrich_with_claude(
        company_name, facts, deterministic_result, api_key=api_key
    )

    conn = storage.get_connection(db_path)
    try:
        card = storage.insert_card(
            conn,
            company_name=company_name,
            qid=qid,
            wikidata_facts=facts,
            wikipedia_summary=wikipedia_summary,
            assessment_text=assessment_text,
            confidence=deterministic_result["confidence"],
            verdict=deterministic_result["verdict"],
            source_urls=source_urls,
        )
    finally:
        conn.close()
    return card


def _format_card(card: dict[str, Any]) -> str:
    return (
        f"{card['company_name']} (v{card['version']}) — {card['verdict']} / {card['confidence']}\n"
        f"  {card['assessment_text']}\n"
        f"  sources: {', '.join(card['source_urls'])}"
    )


def cmd_add(args: argparse.Namespace) -> int:
    try:
        card = add_company(args.company, db_path=args.db, api_key=args.api_key)
    except (LookupFailure, wikidata_client.WikidataError, wikipedia_client.WikipediaError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(_format_card(card))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    conn = storage.get_connection(args.db)
    try:
        history = storage.get_history(conn, args.company)
    finally:
        conn.close()
    if not history:
        print(f'No knowledge card found for "{args.company}".', file=sys.stderr)
        return 1
    for card in history:
        print(_format_card(card))
        print()
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    conn = storage.get_connection(args.db)
    try:
        cards = storage.list_latest(conn)
    finally:
        conn.close()
    if not cards:
        print("No knowledge cards yet.")
        return 0
    for card in cards:
        print(_format_card(card))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    conn = storage.get_connection(args.db)
    try:
        cards = storage.search(conn, args.term)
    finally:
        conn.close()
    if not cards:
        print("No matches.")
        return 0
    for card in cards:
        print(_format_card(card))
    return 0


def cmd_export_html(args: argparse.Namespace) -> int:
    conn = storage.get_connection(args.db)
    try:
        latest_cards = storage.list_latest(conn)
        entries = [
            {"card": card, "history": storage.get_history(conn, card["company_name"])}
            for card in latest_cards
        ]
    finally:
        conn.close()
    html = html_report.render_html(entries)
    with open(args.output, "w", encoding="utf-8") as handle:
        handle.write(html)
    print(f"Wrote {args.output} ({len(entries)} companies).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CanFile — Canadian Ownership Knowledge Cards")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to the SQLite database")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Look up a company and store a new card version")
    add_parser.add_argument("company", help="Company name to look up")
    add_parser.add_argument("--api-key", default=None, help="Anthropic API key (overrides env var)")
    add_parser.set_defaults(func=cmd_add)

    show_parser = subparsers.add_parser("show", help="Show full version history for a company")
    show_parser.add_argument("company", help="Company name")
    show_parser.set_defaults(func=cmd_show)

    list_parser = subparsers.add_parser("list", help="List the latest card for every company")
    list_parser.set_defaults(func=cmd_list)

    search_parser = subparsers.add_parser("search", help="Search company names and assessment text")
    search_parser.add_argument("term", help="Search term")
    search_parser.set_defaults(func=cmd_search)

    export_parser = subparsers.add_parser("export-html", help="Render the searchable HTML index")
    export_parser.add_argument("output", nargs="?", default=DEFAULT_HTML_PATH, help="Output HTML file path")
    export_parser.set_defaults(func=cmd_export_html)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

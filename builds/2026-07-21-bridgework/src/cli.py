"""Bridgework CLI: generate, browse, export, and render the analogy library."""

from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path
from typing import Optional, Sequence

from . import ai_client, generator, novelty, render, storage, taxonomy

BUILD_ROOT = Path(__file__).resolve().parent.parent


def default_db_path() -> str:
    return str(BUILD_ROOT / "data" / "bridgework.db")


def default_html_path() -> str:
    return str(BUILD_ROOT / "data" / "bridgework.html")


def _resolve_concept(concept_id: Optional[str]):
    if concept_id is None:
        return None
    concept = taxonomy.get_concept(concept_id)
    if concept is None:
        raise ValueError(f"Unknown concept id '{concept_id}'. Run 'taxonomy' to list valid ids.")
    return concept


def _resolve_domain(domain_id: Optional[str]):
    if domain_id is None:
        return None
    domain = taxonomy.get_domain(domain_id)
    if domain is None:
        raise ValueError(f"Unknown domain id '{domain_id}'. Run 'taxonomy' to list valid ids.")
    return domain


def _resolve_audience(audience: Optional[str]):
    if audience is None:
        return None
    if audience not in taxonomy.AUDIENCES:
        raise ValueError(f"Unknown audience '{audience}'. Choose from {taxonomy.AUDIENCES}.")
    return audience


def cmd_generate(args: argparse.Namespace, out) -> int:
    concept_id = _resolve_concept(args.concept).id if args.concept else None
    domain_id = _resolve_domain(args.domain).id if args.domain else None
    audience = _resolve_audience(args.audience)

    triples = taxonomy.valid_triples(concept_id=concept_id, domain_id=domain_id, audience=audience)
    if not triples:
        print("No valid (concept, domain, audience) triples match those filters.", file=sys.stderr)
        return 1

    conn = storage.connect(args.db)
    usage = storage.usage_counts(conn)
    ranked = novelty.rank_triples_by_usage(triples, usage)

    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    # Preserve ascending-usage ordering but shuffle within each usage tier for variety.
    tiers: dict = {}
    for t in ranked:
        key = usage.get((t[0].id, t[1].id, t[2]), 0)
        tiers.setdefault(key, []).append(t)
    shuffled: list = []
    for key in sorted(tiers.keys()):
        tier = tiers[key]
        rng.shuffle(tier)
        shuffled.extend(tier)

    count = min(args.count, len(shuffled))
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    use_ai = not args.no_ai

    for concept, domain, aud in shuffled[:count]:
        record = generator.generate_entry(
            concept, domain, aud, conn, api_key=api_key, use_ai=use_ai
        )
        print(
            f"[{record['id']}] ({record['source']}, novelty={record['novelty_score']}) "
            f"{record['hook']}",
            file=out,
        )
    conn.close()
    return 0


def cmd_list(args: argparse.Namespace, out) -> int:
    concept_id = _resolve_concept(args.concept).id if args.concept else None
    domain_id = _resolve_domain(args.domain).id if args.domain else None
    audience = _resolve_audience(args.audience)

    conn = storage.connect(args.db)
    entries = storage.list_analogies(
        conn, concept_id=concept_id, domain_id=domain_id, audience=audience,
        search=args.search, limit=args.limit,
    )
    conn.close()
    if not entries:
        print("No analogies match those filters.", file=out)
        return 0
    for entry in entries:
        print(
            f"[{entry['id']}] {entry['concept_name']} -> {entry['domain_name']} "
            f"({entry['audience']}, {entry['source']}): {entry['hook']}",
            file=out,
        )
    return 0


def cmd_show(args: argparse.Namespace, out) -> int:
    conn = storage.connect(args.db)
    entry = storage.get_analogy(conn, args.id)
    conn.close()
    if entry is None:
        print(f"No analogy with id {args.id}.", file=sys.stderr)
        return 1
    print(f"Hook: {entry['hook']}", file=out)
    print(f"Analogy: {entry['analogy']}", file=out)
    print(f"Caveat: {entry['caveat']}", file=out)
    print(
        f"({entry['concept_name']} -> {entry['domain_name']}, {entry['audience']}, "
        f"{entry['source']}, novelty={entry['novelty_score']})",
        file=out,
    )
    return 0


def _entry_to_markdown(entry: dict) -> str:
    return (
        f"### {entry['hook']}\n\n{entry['analogy']}\n\n*{entry['caveat']}*\n\n"
        f"_{entry['concept_name']} → {entry['domain_name']} "
        f"({entry['audience']}, {entry['source']})_"
    )


def cmd_export(args: argparse.Namespace, out) -> int:
    conn = storage.connect(args.db)
    if args.all:
        entries = storage.list_analogies(conn)
    else:
        if args.id is None:
            print("Provide --id or --all.", file=sys.stderr)
            conn.close()
            return 1
        entry = storage.get_analogy(conn, args.id)
        entries = [entry] if entry else []
    conn.close()
    if not entries:
        print("Nothing to export.", file=sys.stderr)
        return 1
    markdown = "\n\n---\n\n".join(_entry_to_markdown(e) for e in entries)
    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
        print(f"Wrote {args.output}", file=out)
    else:
        print(markdown, file=out)
    return 0


def cmd_render(args: argparse.Namespace, out) -> int:
    conn = storage.connect(args.db)
    entries = storage.list_analogies(conn)
    conn.close()
    html = render.render_html(entries)
    output_path = args.output or default_html_path()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(html, encoding="utf-8")
    print(f"Rendered {len(entries)} analogies to {output_path}", file=out)
    return 0


def cmd_stats(args: argparse.Namespace, out) -> int:
    conn = storage.connect(args.db)
    data = storage.stats(conn)
    conn.close()
    total_triples = len(taxonomy.valid_triples())
    coverage = (data["distinct_triples"] / total_triples * 100) if total_triples else 0.0
    print(f"Total analogies: {data['total']}", file=out)
    print(
        f"Distinct triples covered: {data['distinct_triples']} / {total_triples} "
        f"({coverage:.1f}%)",
        file=out,
    )
    print(f"By subdomain: {data['by_subdomain']}", file=out)
    print(f"By source: {data['by_source']}", file=out)
    return 0


def cmd_taxonomy(args: argparse.Namespace, out) -> int:
    print("Concepts:", file=out)
    for concept in taxonomy.CONCEPTS:
        print(f"  {concept.id} [{concept.subdomain}/{concept.mechanism_type}] {concept.name}", file=out)
    print("Domains:", file=out)
    for domain in taxonomy.DOMAINS:
        print(f"  {domain.id} {domain.mechanism_types} {domain.name}", file=out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bridgework", description="Neuroscience analogy generator.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_gen = sub.add_parser("generate", help="Generate new analogies.")
    p_gen.add_argument("--count", type=int, default=3)
    p_gen.add_argument("--concept", default=None)
    p_gen.add_argument("--domain", default=None)
    p_gen.add_argument("--audience", default=None, choices=list(taxonomy.AUDIENCES))
    p_gen.add_argument("--no-ai", action="store_true")
    p_gen.add_argument("--db", default=None)
    p_gen.add_argument("--seed", type=int, default=None, help="Deterministic candidate ordering, for testing.")
    p_gen.set_defaults(func=cmd_generate)

    p_list = sub.add_parser("list", help="List stored analogies.")
    p_list.add_argument("--concept", default=None)
    p_list.add_argument("--domain", default=None)
    p_list.add_argument("--audience", default=None, choices=list(taxonomy.AUDIENCES))
    p_list.add_argument("--search", default=None)
    p_list.add_argument("--limit", type=int, default=None)
    p_list.add_argument("--db", default=None)
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="Show one analogy by id.")
    p_show.add_argument("id", type=int)
    p_show.add_argument("--db", default=None)
    p_show.set_defaults(func=cmd_show)

    p_export = sub.add_parser("export", help="Export analogies as Markdown.")
    p_export.add_argument("--id", type=int, default=None)
    p_export.add_argument("--all", action="store_true")
    p_export.add_argument("--output", default=None)
    p_export.add_argument("--db", default=None)
    p_export.set_defaults(func=cmd_export)

    p_render = sub.add_parser("render", help="Render the library to a self-contained HTML file.")
    p_render.add_argument("--output", default=None)
    p_render.add_argument("--db", default=None)
    p_render.set_defaults(func=cmd_render)

    p_stats = sub.add_parser("stats", help="Show library coverage stats.")
    p_stats.add_argument("--db", default=None)
    p_stats.set_defaults(func=cmd_stats)

    p_tax = sub.add_parser("taxonomy", help="List all concepts and domains.")
    p_tax.set_defaults(func=cmd_taxonomy)

    return parser


def main(argv: Optional[Sequence[str]] = None, out=sys.stdout) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "db", None) is None and hasattr(args, "db"):
        args.db = default_db_path()
    try:
        return args.func(args, out)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

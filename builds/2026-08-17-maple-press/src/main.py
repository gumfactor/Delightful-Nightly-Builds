"""Maple Press CLI — turns a business CSV into ready-to-publish Canada List copy."""

from __future__ import annotations

import argparse
import json
import sys

import ai_polish as ai_polish_engine
import body as body_engine
import csv_ingest
import headlines
import render
import store
import taxonomy

DEFAULT_DB = "maple_press.db"


def generate_piece(
    csv_path: str,
    piece_type: str,
    tone: str,
    occasion: str = "general",
    business: str | None = None,
    category: str | None = None,
    province: str | None = None,
    include_unverified: bool = False,
    ai_polish: bool = False,
    api_key: str | None = None,
    db_path: str = DEFAULT_DB,
) -> dict:
    """Run the full pipeline: ingest -> filter -> select -> validate -> assemble
    -> pick headline -> optionally polish -> persist. Returns the stored piece."""
    taxonomy.check_occasion(occasion)
    taxonomy.check_tone_compatibility(piece_type, tone)

    all_businesses, has_verdict_column = csv_ingest.load_businesses(csv_path)
    filtered = csv_ingest.filter_by_verdict(all_businesses, has_verdict_column, include_unverified)

    if piece_type == "spotlight":
        if not business:
            raise ValueError("'spotlight' requires --business <name>.")
        selected = csv_ingest.select_for_spotlight(filtered, business)
        selector_category = selected[0]["category"]
        selector_province = selected[0].get("province") or ""
    elif piece_type in ("gift_guide", "swap_it"):
        if not category:
            raise ValueError(f"'{piece_type}' requires --category <name>.")
        selected = csv_ingest.select_by_category(filtered, category)
        selector_category = category
        selector_province = ""
    elif piece_type == "local_spotlight":
        if not province:
            raise ValueError("'local_spotlight' requires --province <name>.")
        selected = csv_ingest.select_by_province(filtered, province)
        selector_category = ""
        selector_province = province
    else:
        raise ValueError(f"Unknown piece type: {piece_type!r}")

    taxonomy.check_eligibility(piece_type, selected)

    context = {
        "name": selected[0]["name"] if piece_type == "spotlight" else "",
        "category": selector_category,
        "count": len(selected),
        "province": selector_province,
    }

    body_text = body_engine.build_body(piece_type, tone, occasion, selected, context)

    conn = store.get_connection(db_path)
    try:
        history = store.history_full_texts(conn, piece_type)
        headline, novelty_score = headlines.select_headline(
            piece_type, occasion, context, body_text, history
        )

        final_body, was_polished = (
            ai_polish_engine.polish(body_text, piece_type, api_key)
            if ai_polish
            else (body_text, False)
        )

        piece_id = store.insert_piece(
            conn,
            piece_type,
            tone,
            occasion,
            headline,
            final_body,
            selected,
            novelty_score,
            was_polished,
        )
        piece = store.get_piece(conn, piece_id)
    finally:
        conn.close()

    return piece


def _cmd_generate(args: argparse.Namespace) -> int:
    try:
        piece = generate_piece(
            csv_path=args.csv,
            piece_type=args.type,
            tone=args.tone,
            occasion=args.occasion,
            business=args.business,
            category=args.category,
            province=args.province,
            include_unverified=args.include_unverified,
            ai_polish=args.ai_polish,
            db_path=args.db,
        )
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(piece, indent=2))
    else:
        print(f"# {piece['headline']}  (id={piece['id']})")
        print()
        print(piece["body_markdown"])
        print()
        print(
            f"[{piece['piece_type']} / {piece['tone']} / {piece['occasion']} / "
            f"novelty={piece['novelty_score']:.2f} / "
            f"{'ai-polished' if piece['ai_polished'] else 'deterministic'}]"
        )
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    conn = store.get_connection(args.db)
    try:
        pieces = store.list_pieces(conn, piece_type=args.type, tone=args.tone)
    finally:
        conn.close()

    if not pieces:
        print("No pieces yet. Run 'generate' first.")
        return 0

    for piece in pieces:
        print(f"#{piece['id']:<4} [{piece['piece_type']:<15}] {piece['headline']}")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    conn = store.get_connection(args.db)
    try:
        try:
            piece = store.get_piece(conn, args.id)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
    finally:
        conn.close()

    print(f"# {piece['headline']}  (id={piece['id']})")
    print()
    print(piece["body_markdown"])
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    conn = store.get_connection(args.db)
    try:
        try:
            piece = store.get_piece(conn, args.id)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
    finally:
        conn.close()

    if args.format == "markdown":
        content = f"# {piece['headline']}\n\n{piece['body_markdown']}\n"
    else:
        content = render.render_html([piece])

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {args.out}")
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    conn = store.get_connection(args.db)
    try:
        pieces = store.list_pieces(conn)
    finally:
        conn.close()

    html = render.render_html(pieces)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {args.out} ({len(pieces)} piece(s))")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="maple_press",
        description="Turn a Canadian business CSV into ready-to-publish editorial copy.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_generate = subparsers.add_parser("generate", help="Generate a new editorial piece.")
    p_generate.add_argument("--csv", required=True, help="Path to the business CSV.")
    p_generate.add_argument("--type", required=True, choices=taxonomy.PIECE_TYPES)
    p_generate.add_argument("--tone", required=True, choices=taxonomy.TONES)
    p_generate.add_argument("--occasion", default="general", choices=taxonomy.OCCASIONS)
    p_generate.add_argument("--business", help="Business name (required for spotlight).")
    p_generate.add_argument("--category", help="Category (required for gift_guide/swap_it).")
    p_generate.add_argument("--province", help="Province (required for local_spotlight).")
    p_generate.add_argument("--include-unverified", action="store_true")
    p_generate.add_argument("--ai-polish", action="store_true")
    p_generate.add_argument("--json", action="store_true")
    p_generate.add_argument("--db", default=DEFAULT_DB)
    p_generate.set_defaults(func=_cmd_generate)

    p_list = subparsers.add_parser("list", help="List generated pieces.")
    p_list.add_argument("--type", choices=taxonomy.PIECE_TYPES)
    p_list.add_argument("--tone", choices=taxonomy.TONES)
    p_list.add_argument("--db", default=DEFAULT_DB)
    p_list.set_defaults(func=_cmd_list)

    p_show = subparsers.add_parser("show", help="Show a stored piece.")
    p_show.add_argument("id", type=int)
    p_show.add_argument("--db", default=DEFAULT_DB)
    p_show.set_defaults(func=_cmd_show)

    p_export = subparsers.add_parser("export", help="Export a piece to a file.")
    p_export.add_argument("id", type=int)
    p_export.add_argument("--format", choices=["markdown", "html"], default="markdown")
    p_export.add_argument("--out", required=True)
    p_export.add_argument("--db", default=DEFAULT_DB)
    p_export.set_defaults(func=_cmd_export)

    p_render = subparsers.add_parser("render", help="Render the full HTML library dashboard.")
    p_render.add_argument("--out", default="maple_press.html")
    p_render.add_argument("--db", default=DEFAULT_DB)
    p_render.set_defaults(func=_cmd_render)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

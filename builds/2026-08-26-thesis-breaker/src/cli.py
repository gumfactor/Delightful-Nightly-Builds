"""Argparse CLI for Thesis Breaker: check / demo / history / render / list."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional

from . import fetch, narrative, render, rules, store
from .personas import overall_score, score_all_personas

DEFAULT_DB_PATH = "thesisbreaker.db"


def _run_pipeline(*, ticker: str, thesis_text: str, data: dict, api_key: Optional[str],
                   prior_scores: Optional[list[int]] = None) -> tuple[str, dict, int, bool, list]:
    """Returns (report_html, persona_scores_dict, overall, any_ai_polished, triggered).

    `prior_scores` are the overall scores of earlier saved runs for this
    ticker (NOT including this run); this run's own score is appended
    before rendering so the history chart reflects every run up to and
    including the one just computed.
    """
    results = rules.run_all_rules(data, thesis_text)
    persona_scores = score_all_personas(results)
    score = overall_score(persona_scores)
    score_for_storage = score if score is not None else 0

    narratives = {}
    any_polished = False
    for p in persona_scores:
        text, polished = narrative.polish(p, api_key)
        narratives[p.key] = (text, polished)
        any_polished = any_polished or polished

    full_history = (prior_scores or []) + [score_for_storage]
    html_report = render.render_report(
        ticker=ticker, thesis_text=thesis_text, data=data, results=results,
        persona_scores=persona_scores, narratives=narratives, overall_score=score,
        history_scores=full_history,
    )
    persona_scores_dict = {p.key: p.score for p in persona_scores}
    triggered = [{"key": r.key, "label": r.label, "fired": r.fired, "detail": r.detail} for r in results]
    return html_report, persona_scores_dict, score_for_storage, any_polished, triggered


def cmd_check(args: argparse.Namespace) -> int:
    conn = store.connect(args.db)
    ticker_factory = args.ticker_factory or _default_ticker_factory
    data = fetch.fetch_ticker_data(args.ticker, ticker_factory)
    prior = store.history_for_ticker(conn, args.ticker)
    prior_scores = [row.overall_score for row in prior]

    api_key = os.environ.get("ANTHROPIC_API_KEY") if args.ai_polish else None
    html_report, persona_scores_dict, score, ai_polished, triggered = _run_pipeline(
        ticker=args.ticker, thesis_text=args.thesis, data=data, api_key=api_key,
        prior_scores=prior_scores,
    )

    run_timestamp = datetime.now(timezone.utc).isoformat()
    check_id = store.insert_check(
        conn, ticker=args.ticker.upper(), thesis_text=args.thesis, run_timestamp=run_timestamp,
        fetched_data=data, triggered=triggered, persona_scores=persona_scores_dict,
        overall_score=score, ai_polished=ai_polished,
    )

    out_path = args.out or "report.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_report)

    print(f"Check #{check_id} for {args.ticker.upper()} saved. Overall bear-case score: {score}/100.")
    print(f"Report written to {out_path}")
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    fixture_path = args.fixture or os.path.join(os.path.dirname(__file__), "..", "fixtures", "sample_aapl_fetch.json")
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    thesis = args.thesis or (
        "Bullish on strong revenue growth and margin expansion; reasonably valued "
        "relative to peers with a low debt balance sheet."
    )
    conn = store.connect(args.db)
    prior = store.history_for_ticker(conn, data["ticker"])
    prior_scores = [row.overall_score for row in prior]

    api_key = os.environ.get("ANTHROPIC_API_KEY") if args.ai_polish else None
    html_report, persona_scores_dict, score, ai_polished, triggered = _run_pipeline(
        ticker=data["ticker"], thesis_text=thesis, data=data, api_key=api_key,
        prior_scores=prior_scores,
    )

    run_timestamp = datetime.now(timezone.utc).isoformat()
    check_id = store.insert_check(
        conn, ticker=data["ticker"], thesis_text=thesis, run_timestamp=run_timestamp,
        fetched_data=data, triggered=triggered, persona_scores=persona_scores_dict,
        overall_score=score, ai_polished=ai_polished,
    )

    out_path = args.out or "report.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_report)

    print(f"[demo] Check #{check_id} for {data['ticker']} saved (no network used). Overall bear-case score: {score}/100.")
    print(f"Report written to {out_path}")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    conn = store.connect(args.db)
    rows = store.history_for_ticker(conn, args.ticker)
    if not rows:
        print(f"No saved checks for {args.ticker.upper()}.")
        return 0
    for row in rows:
        print(f"#{row.id}  {row.run_timestamp}  score={row.overall_score}/100  ai_polished={row.ai_polished}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    conn = store.connect(args.db)
    row = store.get_check(conn, args.id)
    if row is None:
        print(f"No saved check with id {args.id}.", file=sys.stderr)
        return 1
    results = [rules.RuleResult(t["key"], t["label"], t["fired"], t["detail"]) for t in row.triggered]
    from .personas import PersonaScore
    persona_scores = []
    narratives = {}
    for key, score_value in row.persona_scores.items():
        fired = [r for r in results if r.fired is True]
        not_fired = [r for r in results if r.fired is False]
        unavailable = [r for r in results if r.fired is None]
        ps = PersonaScore(key, key.replace("_", " ").title(), score_value, fired, not_fired, unavailable)
        persona_scores.append(ps)
        narratives[key] = (narrative.deterministic_text(ps), bool(row.ai_polished))

    prior = [r.overall_score for r in store.history_for_ticker(conn, row.ticker) if r.id <= row.id]
    html_report = render.render_report(
        ticker=row.ticker, thesis_text=row.thesis_text, data=row.fetched_data, results=results,
        persona_scores=persona_scores, narratives=narratives, overall_score=row.overall_score,
        history_scores=prior,
    )
    out_path = args.out or "report.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_report)
    print(f"Report for check #{row.id} written to {out_path}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    conn = store.connect(args.db)
    rows = store.list_all(conn)
    if not rows:
        print("No saved checks.")
        return 0
    for row in rows:
        print(f"#{row.id}  {row.ticker}  {row.run_timestamp}  score={row.overall_score}/100")
    return 0


def _default_ticker_factory(ticker: str):
    import yfinance
    return yfinance.Ticker(ticker)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="thesis-breaker", description="Adversarial bear-case critique for your own investment thesis.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to the SQLite database file.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="Fetch real data and run the bear-case critique for a ticker.")
    p_check.add_argument("ticker")
    p_check.add_argument("--thesis", required=True)
    p_check.add_argument("--ai-polish", action="store_true")
    p_check.add_argument("--out")
    p_check.set_defaults(func=cmd_check, ticker_factory=None)

    p_demo = sub.add_parser("demo", help="Run the full pipeline against a bundled fixture, no network required.")
    p_demo.add_argument("--thesis")
    p_demo.add_argument("--ai-polish", action="store_true")
    p_demo.add_argument("--out")
    p_demo.add_argument("--fixture")
    p_demo.set_defaults(func=cmd_demo)

    p_history = sub.add_parser("history", help="Show saved checks for a ticker.")
    p_history.add_argument("ticker")
    p_history.set_defaults(func=cmd_history)

    p_render = sub.add_parser("render", help="Regenerate the HTML report for a saved check id.")
    p_render.add_argument("--id", type=int, required=True)
    p_render.add_argument("--out")
    p_render.set_defaults(func=cmd_render)

    p_list = sub.add_parser("list", help="List all saved checks.")
    p_list.set_defaults(func=cmd_list)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)

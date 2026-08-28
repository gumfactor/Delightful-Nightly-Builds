"""argparse CLI: sync / list / show / flags / render."""

from __future__ import annotations

import argparse
import os
import sys
import time
import urllib.request
from typing import Any, Callable

from src import ai_narrative, edgar_client, extract, metrics, render, storage

DEFAULT_DB_PATH = "edgar_lens.db"
DEFAULT_OUT_PATH = "dashboard.html"


def _get_user_agent(args: argparse.Namespace) -> str:
    if getattr(args, "user_agent", None):
        return args.user_agent
    return os.environ.get("EDGAR_USER_AGENT", edgar_client.DEFAULT_USER_AGENT)


def cmd_sync(
    args: argparse.Namespace,
    urlopen_func: Callable[..., Any] = urllib.request.urlopen,
    sleep_func: Callable[[float], None] | None = None,
) -> int:
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    if not tickers:
        print("No tickers provided.")
        return 1

    user_agent = _get_user_agent(args)
    conn = storage.connect(args.db)

    unresolved = [t for t in tickers if storage.get_ticker(conn, t) is None]
    if unresolved:
        print(f"Resolving {len(unresolved)} ticker(s) via SEC company_tickers.json...")
        try:
            ticker_map = edgar_client.fetch_company_tickers(user_agent, urlopen_func)
        except edgar_client.EdgarClientError as exc:
            print(f"Failed to fetch SEC ticker index: {exc}")
            ticker_map = {}
        for ticker in unresolved:
            resolved = edgar_client.resolve_ticker(ticker, ticker_map)
            if resolved is None:
                print(f"  {ticker}: not found in SEC ticker index, skipping")
                continue
            storage.upsert_ticker(conn, ticker, resolved["cik"], resolved["title"])
            print(f"  {ticker} -> CIK {resolved['cik']} ({resolved['title']})")

    synced = 0
    for ticker in tickers:
        row = storage.get_ticker(conn, ticker)
        if row is None:
            continue
        cik, company_name = row["cik"], row["company_name"]
        try:
            companyfacts = edgar_client.fetch_companyfacts(cik, user_agent, urlopen_func)
        except edgar_client.EdgarClientError as exc:
            print(f"{ticker}: failed to fetch company facts ({exc})")
            continue
        annual_rows = extract.extract_annual_financials(companyfacts)
        if not annual_rows:
            print(f"{ticker}: no annual 10-K facts found in response")
            continue
        count = storage.upsert_financials(conn, cik, ticker, company_name, annual_rows)
        print(f"{ticker}: synced {count} fiscal year(s)")
        synced += 1
        if ticker != tickers[-1]:
            edgar_client.rate_limit_sleep(sleep_func or time.sleep)

    conn.close()
    print(f"Done. {synced}/{len(tickers)} ticker(s) synced.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    conn = storage.connect(args.db)
    tickers = storage.list_tickers(conn)
    if not tickers:
        print("No tickers tracked yet. Run `sync --tickers TICK1,TICK2`.")
        conn.close()
        return 0
    for row in tickers:
        financials = storage.get_financials(conn, row["ticker"])
        years = f"{financials[0]['fiscal_year']}-{financials[-1]['fiscal_year']}" if financials else "none"
        print(f"{row['ticker']:<8} {row['company_name']:<40} CIK {row['cik']}  FY {years}")
    conn.close()
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    conn = storage.connect(args.db)
    financials = storage.get_financials(conn, args.ticker)
    conn.close()
    if not financials:
        print(f"No data for {args.ticker}. Run `sync --tickers {args.ticker}` first.")
        return 1
    enriched = metrics.compute_yearly_metrics(financials)
    print(f"{args.ticker} -- {financials[0]['company_name']}")
    print(f"{'FY':<6}{'Revenue':>16}{'Net Income':>16}{'Net Margin':>12}{'D/E':>8}{'Rev YoY':>10}")
    for row in enriched:
        rev = f"{row['revenue']:,.0f}" if row["revenue"] is not None else "—"
        ni = f"{row['net_income']:,.0f}" if row["net_income"] is not None else "—"
        nm = f"{row['net_margin']:.1%}" if row["net_margin"] is not None else "—"
        de = f"{row['debt_to_equity']:.2f}x" if row["debt_to_equity"] is not None else "—"
        yoy = f"{row['revenue_yoy']:.1%}" if row["revenue_yoy"] is not None else "—"
        print(f"{row['fiscal_year']:<6}{rev:>16}{ni:>16}{nm:>12}{de:>8}{yoy:>10}")
    return 0


def cmd_flags(args: argparse.Namespace) -> int:
    conn = storage.connect(args.db)
    tickers = storage.get_tracked_tickers(conn)
    total = 0
    for ticker in tickers:
        financials = storage.get_financials(conn, ticker)
        enriched = metrics.compute_yearly_metrics(financials)
        anomalies = metrics.flag_anomalies(enriched)
        for anomaly in anomalies:
            print(f"{ticker} FY{anomaly['fiscal_year']} [{anomaly['type']}] {anomaly['detail']}")
            total += 1
    conn.close()
    if total == 0:
        print("No anomalies flagged.")
    return 0


def build_companies_payload(
    conn: Any,
    use_ai: bool,
    api_key: str | None = None,
    urlopen_func: Callable[..., Any] = urllib.request.urlopen,
) -> list[dict[str, Any]]:
    """Build the render-ready company list, including narratives per anomaly."""
    companies: list[dict[str, Any]] = []
    for ticker_row in storage.list_tickers(conn):
        ticker = ticker_row["ticker"]
        financials = storage.get_financials(conn, ticker)
        if not financials:
            continue
        enriched = metrics.compute_yearly_metrics(financials)
        anomalies = metrics.flag_anomalies(enriched)
        resolved_key = api_key if use_ai else ""
        for anomaly in anomalies:
            anomaly["narrative"] = ai_narrative.generate_narrative(
                ticker, anomaly, resolved_key, urlopen_func
            )
        companies.append({
            "ticker": ticker,
            "company_name": ticker_row["company_name"],
            "rows": enriched,
            "anomalies": anomalies,
        })
    return companies


def cmd_render(
    args: argparse.Namespace,
    urlopen_func: Callable[..., Any] = urllib.request.urlopen,
) -> int:
    conn = storage.connect(args.db)
    api_key = os.environ.get("ANTHROPIC_API_KEY") if args.ai else ""
    companies = build_companies_payload(conn, args.ai, api_key, urlopen_func)
    conn.close()
    render.render_dashboard(companies, args.out)
    print(f"Dashboard written to {args.out} ({len(companies)} companies).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="edgar-lens", description="SEC EDGAR financial statement explorer")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite database path")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_parser = subparsers.add_parser("sync", help="Fetch and store financials for a ticker watchlist")
    sync_parser.add_argument("--tickers", required=True, help="Comma-separated tickers, e.g. AAPL,MSFT")
    sync_parser.add_argument("--user-agent", default=None, help="SEC-compliant User-Agent header")
    sync_parser.set_defaults(func=cmd_sync)

    list_parser = subparsers.add_parser("list", help="List tracked tickers")
    list_parser.set_defaults(func=cmd_list)

    show_parser = subparsers.add_parser("show", help="Show one ticker's yearly financials")
    show_parser.add_argument("ticker")
    show_parser.set_defaults(func=cmd_show)

    flags_parser = subparsers.add_parser("flags", help="List all flagged anomalies")
    flags_parser.set_defaults(func=cmd_flags)

    render_parser = subparsers.add_parser("render", help="Render the HTML dashboard")
    render_parser.add_argument("--out", default=DEFAULT_OUT_PATH, help="Output HTML file path")
    render_parser.add_argument("--ai", action="store_true", help="Use Claude Haiku for anomaly narratives")
    render_parser.set_defaults(func=cmd_render)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

"""Command line entry point."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

from . import ai, exports, report
from .demo import DEMO_COMPANIES
from .extract import extract_company
from .sec import Fetcher, SecClient, SecError, http_fetch, user_agent_from_env


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="edgar_fin", description="Multi-year financial history for US tickers from SEC EDGAR.")
    parser.add_argument("tickers", nargs="*", help="tickers, e.g. AAPL MSFT NVDA")
    parser.add_argument("--years", type=int, default=5, help="fiscal years to show (default 5)")
    parser.add_argument("--out", default="output", help="output directory (default ./output)")
    parser.add_argument("--refresh", action="store_true", help="ignore the on-disk SEC cache")
    parser.add_argument("--ai", action="store_true", help="add Claude commentary (needs ANTHROPIC_API_KEY)")
    parser.add_argument("--demo", action="store_true", help="render synthetic sample data, no network")
    return parser


def run(argv: list[str], fetch: Fetcher = http_fetch,
        ai_transport: ai.Transport = ai.http_transport,
        sleep: Callable[[float], None] | None = None, out=sys.stdout, err=sys.stderr) -> int:
    args = build_parser().parse_args(argv)
    if not 1 <= args.years <= 15:
        print("--years must be between 1 and 15", file=err)
        return 2
    out_dir = Path(args.out)
    companies: list[dict] = []
    errors: list[str] = []

    if args.demo:
        for ticker, spec in DEMO_COMPANIES.items():
            companies.append(extract_company(spec["payload"], ticker, spec["cik"], args.years))
    else:
        tickers = list(dict.fromkeys(t.strip().upper() for t in args.tickers if t.strip()))
        if not tickers:
            print("Give at least one ticker (or use --demo).", file=err)
            return 2
        try:
            client_kwargs = {"sleep": sleep} if sleep else {}
            client = SecClient(user_agent_from_env(), cache_dir=out_dir / ".cache", fetch=fetch,
                               refresh=args.refresh, **client_kwargs)
        except SecError as exc:
            print(f"error: {exc}", file=err)
            return 2
        for ticker in tickers:
            try:
                cik, title = client.resolve(ticker)
                payload = client.company_facts(cik)
                payload.setdefault("entityName", title)
                company = extract_company(payload, ticker, cik, args.years)
                if not company["years"]:
                    raise SecError(f"{ticker}: no annual 10-K data found")
                companies.append(company)
            except SecError as exc:
                errors.append(str(exc))
                print(f"warning: {exc}", file=err)

    if not companies:
        print("error: nothing to report.", file=err)
        return 1

    commentary = ai_note = None
    if args.ai:
        try:
            commentary = ai.commentary(companies, transport=ai_transport)
        except ai.AiError as exc:
            ai_note = str(exc)
            print(f"warning: {exc}", file=err)

    written = exports.write_all(companies, out_dir)
    page = out_dir / "report.html"
    page.write_text(report.render(companies, commentary, ai_note, demo=args.demo, errors=errors),
                    encoding="utf-8")
    written.append(page)
    for path in written:
        print(path, file=out)
    return 0 if not errors else 3


def main() -> None:
    sys.exit(run(sys.argv[1:]))

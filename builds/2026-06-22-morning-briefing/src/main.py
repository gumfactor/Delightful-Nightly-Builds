#!/usr/bin/env python3
"""Morning Briefing — daily digest of GitHub activity, portfolio moves, and weather windows."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

# Ensure src/ is importable when run as `python src/main.py` from the build root
sys.path.insert(0, str(Path(__file__).parent))

from ai_synthesizer import synthesize
from github_fetcher import fetch_github_activity
from market_fetcher import fetch_portfolio_data
from report import render_html, render_markdown
from weather_fetcher import fetch_weather


def _load_config(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a morning briefing report")
    parser.add_argument("--config", default="config.json", help="Path to config file")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--date", help="Override report date (YYYY-MM-DD)")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI synthesis")
    parser.add_argument("--stdout", action="store_true", help="Print markdown to stdout instead of writing files")
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent
    config_path = base_dir / args.config
    output_dir = base_dir / args.output_dir

    try:
        config = _load_config(config_path)
    except FileNotFoundError:
        print(f"Error: config not found at {config_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in config: {exc}", file=sys.stderr)
        return 1

    report_date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    target_date = date.fromisoformat(report_date)

    github_token = os.environ.get("GITHUB_TOKEN", "")
    github_data = fetch_github_activity(
        github_token,
        stale_days=config.get("stale_days", 7),
        lookback_hours=config.get("activity_lookback_hours", 24),
    )

    portfolio_data = fetch_portfolio_data(config.get("watchlist", []))

    loc = config.get("weather_location", {"lat": 43.651, "lon": -79.347})
    weather_data = fetch_weather(loc["lat"], loc["lon"], target_date)

    ai_summary = "" if args.no_ai else synthesize(github_data, portfolio_data, weather_data)

    md_text = render_markdown(report_date, github_data, portfolio_data, weather_data, ai_summary)
    html_text = render_html(report_date, github_data, portfolio_data, weather_data, ai_summary)

    if args.stdout:
        print(md_text)
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    md_path = output_dir / f"{report_date}.md"
    html_path = output_dir / f"{report_date}.html"
    md_path.write_text(md_text, encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")

    print(f"✓ {html_path}")
    print(f"✓ {md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

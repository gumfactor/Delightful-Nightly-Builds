"""Wake Log command-line interface.

Commands:
  forecast  -- fetch + score the upcoming week's windows, print a table
  generate  -- generate (and save) a trip-log entry for the best window,
               or a specific --date/--window
  list      -- list saved journal entries
  show      -- show one entry in full
  search    -- search saved entries
  render    -- write a self-contained HTML journal
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

from . import ai_polish, narrative, openmeteo, render, store

DEFAULT_LATITUDE = 43.6532   # Toronto -- placeholder; override with --lat/--lon
DEFAULT_LONGITUDE = -79.3832
DEFAULT_LOCATION_NAME = "Toronto (default -- pass --location-name/--lat/--lon)"
DEFAULT_DB_PATH = "wake_log.db"

VALID_WINDOWS = {label for label, _, _ in openmeteo.WINDOWS}


class CliError(Exception):
    """Raised for a clean, user-facing error (bad arguments, no data)."""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wake-log", description="Boating/cottage weather-window trip log")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to the SQLite journal file")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_location_args(p: argparse.ArgumentParser) -> None:
        p.add_argument("--lat", type=float, default=DEFAULT_LATITUDE, help="Latitude")
        p.add_argument("--lon", type=float, default=DEFAULT_LONGITUDE, help="Longitude")
        p.add_argument("--location-name", default=DEFAULT_LOCATION_NAME, help="Human-readable location label")

    forecast_p = sub.add_parser("forecast", help="Show the upcoming week's scored windows")
    add_location_args(forecast_p)
    forecast_p.add_argument("--days", type=int, default=7, help="Number of forecast days (1-10)")

    generate_p = sub.add_parser("generate", help="Generate and save a trip-log entry")
    add_location_args(generate_p)
    generate_p.add_argument("--days", type=int, default=7, help="Number of forecast days (1-10)")
    generate_p.add_argument("--date", default=None, help="Target date YYYY-MM-DD (default: best upcoming window)")
    generate_p.add_argument("--window", default=None, choices=sorted(VALID_WINDOWS), help="morning/afternoon/evening")
    generate_p.add_argument("--ai-polish", action="store_true", help="Attempt an AI prose polish (needs ANTHROPIC_API_KEY)")

    list_p = sub.add_parser("list", help="List saved journal entries")
    list_p.add_argument("--limit", type=int, default=20)

    show_p = sub.add_parser("show", help="Show one entry in full")
    show_p.add_argument("id", type=int)

    search_p = sub.add_parser("search", help="Search saved entries")
    search_p.add_argument("query")

    render_p = sub.add_parser("render", help="Render a self-contained HTML journal")
    add_location_args(render_p)
    render_p.add_argument("--days", type=int, default=7, help="Number of forecast days for the upcoming-windows panel")
    render_p.add_argument("--output", default="journal.html", help="Output HTML file path")
    render_p.add_argument("--offline", action="store_true", help="Skip the live forecast fetch (journal-only render)")

    return parser


def _format_window_row(w: openmeteo.WindowAggregate) -> str:
    return (
        f"{w.date}  {w.window:9s}  score={w.score:5.1f}  {w.beaufort_name:16s}"
        f"  wind={w.wind_knots:5.1f}kn  gust={w.gust_knots:5.1f}kn  temp={w.temp_c:5.1f}C"
        f"  precip={w.precip_probability:5.1f}%  cloud={w.cloud_cover:5.1f}%"
    )


def cmd_forecast(args: argparse.Namespace) -> int:
    windows = openmeteo.get_scored_windows(args.lat, args.lon, args.days)
    if not windows:
        raise CliError("no forecast windows returned")
    best = openmeteo.best_window(windows)
    print(f"Forecast for {args.location_name} ({args.lat}, {args.lon}):")
    for w in windows:
        marker = "  <-- best" if w is best else ""
        print(_format_window_row(w) + marker)
    return 0


def _select_window(windows, target_date, target_window):
    if target_date is None and target_window is None:
        best = openmeteo.best_window(windows)
        if best is None:
            raise CliError("no usable window found in the forecast (no daylight overlap or all conditions unscoreable)")
        return best

    candidates = windows
    if target_date is not None:
        candidates = [w for w in candidates if w.date == target_date]
    if target_window is not None:
        candidates = [w for w in candidates if w.window == target_window]

    if not candidates:
        raise CliError(f"no forecast window found for date={target_date!r} window={target_window!r}")
    return candidates[0]


def cmd_generate(args: argparse.Namespace) -> int:
    windows = openmeteo.get_scored_windows(args.lat, args.lon, args.days)
    if not windows:
        raise CliError("no forecast windows returned")

    window = _select_window(windows, args.date, args.window)

    with store.Store(args.db) as db:
        history = db.history_for_location(args.location_name)
        generated = narrative.generate_narrative(window, args.location_name, history)

        facts = narrative.build_facts(window, args.location_name)
        final_text = generated.text
        was_polished = False
        if args.ai_polish:
            polished = ai_polish.polish(generated.text, facts)
            if polished != generated.text:
                final_text = polished
                was_polished = True

        entry_id = db.save(
            created_at=datetime.now(timezone.utc).isoformat(),
            location_name=args.location_name,
            latitude=args.lat,
            longitude=args.lon,
            target_date=window.date,
            window_label=window.window,
            score=window.score,
            beaufort=window.beaufort_number,
            beaufort_name=window.beaufort_name,
            wind_knots=window.wind_knots,
            gust_knots=window.gust_knots,
            temp_c=window.temp_c,
            precip_probability=window.precip_probability,
            cloud_cover=window.cloud_cover,
            narrative=final_text,
            ai_polished=was_polished,
        )

    print(f"Saved entry #{entry_id} for {window.date} ({window.window}), score {window.score}/100")
    print()
    print(final_text)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    with store.Store(args.db) as db:
        entries = db.list_entries(limit=args.limit)
    if not entries:
        print("No entries logged yet.")
        return 0
    for e in entries:
        print(f"#{e.id}  {e.target_date} ({e.window_label})  score={e.score:5.1f}  {e.location_name}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    with store.Store(args.db) as db:
        entry = db.get(args.id)
    if entry is None:
        raise CliError(f"no entry with id {args.id}")
    print(f"#{entry.id}  {entry.target_date} ({entry.window_label})  {entry.location_name}")
    print(f"Score: {entry.score}/100  {entry.beaufort_name}  wind={entry.wind_knots}kn  gust={entry.gust_knots}kn")
    print(f"Temp: {entry.temp_c}C  precip={entry.precip_probability}%  cloud={entry.cloud_cover}%")
    print()
    print(entry.narrative)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    with store.Store(args.db) as db:
        results = db.search(args.query)
    if not results:
        print("No matching entries.")
        return 0
    for e in results:
        print(f"#{e.id}  {e.target_date} ({e.window_label})  score={e.score:5.1f}  {e.location_name}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    upcoming = []
    if not args.offline:
        try:
            upcoming = openmeteo.get_scored_windows(args.lat, args.lon, args.days)
        except openmeteo.OpenMeteoError as exc:
            print(f"Warning: could not fetch live forecast ({exc}); rendering journal-only.", file=sys.stderr)

    with store.Store(args.db) as db:
        entries = db.list_entries()

    render.render_to_file(entries, upcoming, args.location_name, args.output)
    print(f"Wrote {args.output}")
    return 0


COMMANDS = {
    "forecast": cmd_forecast,
    "generate": cmd_generate,
    "list": cmd_list,
    "show": cmd_show,
    "search": cmd_search,
    "render": cmd_render,
}


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return COMMANDS[args.command](args)
    except CliError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except openmeteo.OpenMeteoError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

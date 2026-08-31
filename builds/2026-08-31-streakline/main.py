"""
Streakline — cross-domain habit/streak tracker.

Commands:
  python3 main.py init
  python3 main.py import-garmin PATH/TO/Activities.csv
  python3 main.py list-types PATH/TO/Activities.csv
  python3 main.py checkin HABIT_ID [--date YYYY-MM-DD] [--note TEXT]
  python3 main.py remove HABIT_ID --date YYYY-MM-DD
  python3 main.py status
  python3 main.py render [--output FILE] [--ai] [--date YYYY-MM-DD]

All dates are treated as UTC calendar days. "Today" for --date defaults to
the current UTC date. See Manual.md for why.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from src.coach import generate_coach_note
from src.db import StreakDB
from src.garmin_import import import_activities, list_activity_types, parse_garmin_csv
from src.render import build_dashboard_data, render_html
from src.streaks import completion_rate, daily_streak, weekly_streak

_BUILD_DIR = Path(__file__).parent
_HABITS_PATH = _BUILD_DIR / "habits.json"
_HABITS_EXAMPLE_PATH = _BUILD_DIR / "habits.example.json"
_DEFAULT_DB_PATH = _BUILD_DIR / "data" / "streakline.db"


def _today_utc() -> date:
    return datetime.now(timezone.utc).date()


def _parse_date_arg(raw: str | None) -> date:
    if raw is None:
        return _today_utc()
    try:
        return date.fromisoformat(raw)
    except ValueError:
        print(f"Error: invalid date '{raw}', expected YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)


def load_habits(path: Path = _HABITS_PATH) -> list[dict]:
    if not path.exists():
        print(
            f"Error: {path.name} not found. Run 'python3 main.py init' first.",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {path.name}: {exc}", file=sys.stderr)
        sys.exit(1)

    habits = data.get("habits")
    if not isinstance(habits, list) or not habits:
        print(f"Error: {path.name} must have a non-empty 'habits' list", file=sys.stderr)
        sys.exit(1)

    ids = set()
    for habit in habits:
        for field in ("id", "name", "cadence", "source"):
            if field not in habit:
                print(f"Error: habit missing required field '{field}': {habit}", file=sys.stderr)
                sys.exit(1)
        if habit["cadence"] not in ("daily", "weekly"):
            print(f"Error: habit '{habit['id']}' has invalid cadence '{habit['cadence']}'", file=sys.stderr)
            sys.exit(1)
        if habit["source"] not in ("garmin", "manual"):
            print(f"Error: habit '{habit['id']}' has invalid source '{habit['source']}'", file=sys.stderr)
            sys.exit(1)
        if habit["id"] in ids:
            print(f"Error: duplicate habit id '{habit['id']}'", file=sys.stderr)
            sys.exit(1)
        ids.add(habit["id"])

    return habits


def cmd_init(args: argparse.Namespace) -> None:
    if _HABITS_PATH.exists():
        print(f"{_HABITS_PATH.name} already exists — leaving it in place.")
    else:
        _HABITS_PATH.write_text(_HABITS_EXAMPLE_PATH.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"Created {_HABITS_PATH.name} from the example config. Edit it, then import or check in.")
    StreakDB(_DEFAULT_DB_PATH)
    print(f"Database ready at {_DEFAULT_DB_PATH}")


def cmd_import_garmin(args: argparse.Namespace) -> None:
    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"Error: file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    habits = load_habits(Path(args.habits) if args.habits else _HABITS_PATH)
    db = StreakDB(Path(args.db) if args.db else _DEFAULT_DB_PATH)
    rows, warnings = parse_garmin_csv(csv_path)
    summary = import_activities(rows, habits, db)

    print(f"Read {summary.total_rows} rows, matched {summary.matched_rows}.")
    print(f"Inserted {summary.inserted} new completion(s); {summary.already_recorded} already recorded.")
    if summary.unmatched_types:
        print("Unmatched activity types (not in any habit's garmin_activity_types):")
        for activity_type in sorted(summary.unmatched_types):
            print(f"  - {activity_type}")
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)


def cmd_list_types(args: argparse.Namespace) -> None:
    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"Error: file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)
    rows, warnings = parse_garmin_csv(csv_path)
    for activity_type in list_activity_types(rows):
        print(activity_type)
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr)


def cmd_checkin(args: argparse.Namespace) -> None:
    habits = load_habits(Path(args.habits) if args.habits else _HABITS_PATH)
    if not any(h["id"] == args.habit_id for h in habits):
        print(f"Error: unknown habit id '{args.habit_id}'. See habits.json.", file=sys.stderr)
        sys.exit(1)

    db = StreakDB(Path(args.db) if args.db else _DEFAULT_DB_PATH)
    completion_date = _parse_date_arg(args.date)
    inserted = db.add_completion(args.habit_id, completion_date, source="manual", detail=args.note)
    if inserted:
        print(f"Checked in '{args.habit_id}' for {completion_date.isoformat()}.")
    else:
        print(f"'{args.habit_id}' already recorded for {completion_date.isoformat()}.")


def cmd_remove(args: argparse.Namespace) -> None:
    db = StreakDB(Path(args.db) if args.db else _DEFAULT_DB_PATH)
    completion_date = _parse_date_arg(args.date)
    removed = db.remove_completion(args.habit_id, completion_date)
    if removed:
        print(f"Removed '{args.habit_id}' completion for {completion_date.isoformat()}.")
    else:
        print(f"No completion found for '{args.habit_id}' on {completion_date.isoformat()}.")


def cmd_status(args: argparse.Namespace) -> None:
    habits = load_habits(Path(args.habits) if args.habits else _HABITS_PATH)
    db = StreakDB(Path(args.db) if args.db else _DEFAULT_DB_PATH)
    as_of = _parse_date_arg(args.date)

    header = f"{'Habit':<20}{'Cadence':<10}{'Current':<10}{'Longest':<10}{'30d Rate':<10}"
    print(header)
    print("-" * len(header))
    for habit in habits:
        dates = db.get_dates(habit["id"])
        cadence = habit["cadence"]
        info = weekly_streak(dates, as_of) if cadence == "weekly" else daily_streak(dates, as_of)
        rate = completion_rate(dates, as_of - timedelta(days=29), as_of, cadence)
        print(
            f"{habit['name']:<20}{cadence:<10}{info.current:<10}{info.longest:<10}{rate:.0%}"
        )


def cmd_render(args: argparse.Namespace) -> None:
    habits = load_habits(Path(args.habits) if args.habits else _HABITS_PATH)
    db = StreakDB(Path(args.db) if args.db else _DEFAULT_DB_PATH)
    as_of = _parse_date_arg(args.date)

    habit_stats = []
    for habit in habits:
        dates = db.get_dates(habit["id"])
        cadence = habit["cadence"]
        info = weekly_streak(dates, as_of) if cadence == "weekly" else daily_streak(dates, as_of)
        rate = completion_rate(dates, as_of - timedelta(days=29), as_of, cadence)
        habit_stats.append(
            {
                "id": habit["id"],
                "name": habit["name"],
                "cadence": cadence,
                "current_streak": info.current,
                "longest_streak": info.longest,
                "completion_rate": rate,
            }
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY") if args.ai else None
    coach_note = generate_coach_note(habit_stats, api_key)

    data = build_dashboard_data(habits, db, as_of, coach_note)
    html = render_html(data)

    output_path = Path(args.output) if args.output else _BUILD_DIR / "dashboard.html"
    output_path.write_text(html, encoding="utf-8")
    print(f"Dashboard written to {output_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Streakline — cross-domain habit/streak tracker")
    parser.add_argument("--db", help="Override the SQLite database path (mainly for tests/scripting)")
    parser.add_argument("--habits", help="Override the habits.json path (mainly for tests/scripting)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Create habits.json and the database if missing").set_defaults(func=cmd_init)

    p_import = subparsers.add_parser("import-garmin", help="Import a Garmin Connect Activities CSV export")
    p_import.add_argument("csv_path")
    p_import.set_defaults(func=cmd_import_garmin)

    p_list_types = subparsers.add_parser("list-types", help="List distinct Activity Type values in a Garmin CSV")
    p_list_types.add_argument("csv_path")
    p_list_types.set_defaults(func=cmd_list_types)

    p_checkin = subparsers.add_parser("checkin", help="Manually record a habit completion")
    p_checkin.add_argument("habit_id")
    p_checkin.add_argument("--date", help="YYYY-MM-DD, defaults to today (UTC)")
    p_checkin.add_argument("--note", help="Optional free-text note")
    p_checkin.set_defaults(func=cmd_checkin)

    p_remove = subparsers.add_parser("remove", help="Delete a completion")
    p_remove.add_argument("habit_id")
    p_remove.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_remove.set_defaults(func=cmd_remove)

    p_status = subparsers.add_parser("status", help="Print a terminal streak summary")
    p_status.add_argument("--date", help="Treat this YYYY-MM-DD as 'today' (for testing)")
    p_status.set_defaults(func=cmd_status)

    p_render = subparsers.add_parser("render", help="Render the HTML dashboard")
    p_render.add_argument("--output", help="Output path, defaults to dashboard.html")
    p_render.add_argument("--ai", action="store_true", help="Use ANTHROPIC_API_KEY for the coach note if set")
    p_render.add_argument("--date", help="Treat this YYYY-MM-DD as 'today' (for testing)")
    p_render.set_defaults(func=cmd_render)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

"""TripKit CLI: weather-aware trip prep and packing planner."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

import briefing  # noqa: E402
import dashboard  # noqa: E402
import geocoding  # noqa: E402
import packing  # noqa: E402
import storage  # noqa: E402
import weather  # noqa: E402

DEFAULT_HOME_COUNTRY = "Canada"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
DB_PATH = os.path.join(OUTPUT_DIR, "tripkit.db")
DASHBOARD_PATH = os.path.join(OUTPUT_DIR, "dashboard.html")


class CliError(Exception):
    """Raised for user-facing CLI validation errors."""


def parse_iso_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise CliError(f"'{value}' is not a valid date (expected YYYY-MM-DD).") from exc


def parse_tags(raw: str) -> list[str]:
    tags = [tag.strip().lower() for tag in raw.split(",") if tag.strip()]
    invalid = [tag for tag in tags if tag not in packing.ACTIVITY_TAGS]
    if invalid:
        allowed = ", ".join(packing.ACTIVITY_TAGS)
        raise CliError(f"Unknown activity tag(s): {', '.join(invalid)}. Allowed: {allowed}")
    if not tags:
        raise CliError("At least one activity tag is required.")
    return tags


def ensure_output_dir() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def cmd_add(args: argparse.Namespace, today: date | None = None) -> None:
    today = today or datetime.now(timezone.utc).date()
    start_date = parse_iso_date(args.start)
    end_date = parse_iso_date(args.end)
    if end_date < start_date:
        raise CliError("End date cannot be before start date.")
    tags = parse_tags(args.tags)

    place = geocoding.resolve_destination(args.destination)
    mode, daily_readings = weather.get_weather_for_trip(place.latitude, place.longitude, start_date, end_date, today)

    ensure_output_dir()
    conn = storage.connect(DB_PATH)
    try:
        trip_id = storage.add_trip(
            conn,
            name=args.name,
            destination_query=args.destination,
            resolved_name=place.display_name,
            country=place.country,
            latitude=place.latitude,
            longitude=place.longitude,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            activity_tags=tags,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        storage.save_weather_snapshot(
            conn, trip_id, mode, datetime.now(timezone.utc).isoformat(), [d.to_dict() for d in daily_readings]
        )
    finally:
        conn.close()

    mode_label = "live forecast" if mode == "forecast" else "historical climate-normal estimate"
    print(f"Added trip #{trip_id}: '{args.name}' to {place.display_name} ({mode_label}).")


def cmd_list(_args: argparse.Namespace) -> None:
    ensure_output_dir()
    conn = storage.connect(DB_PATH)
    try:
        trips = storage.list_trips(conn)
    finally:
        conn.close()

    if not trips:
        print("No trips saved yet. Add one with `tripkit add`.")
        return

    for trip in trips:
        tags = ", ".join(trip["activity_tags"])
        print(f"#{trip['id']}: {trip['name']} — {trip['resolved_name']} ({trip['start_date']} to {trip['end_date']}) [{tags}]")


def _build_trip_bundle(conn, trip: dict, api_key: str | None, home_country: str) -> dict:
    snapshot = storage.get_latest_weather_snapshot(conn, trip["id"])
    if snapshot is None:
        raise CliError(f"Trip #{trip['id']} has no weather data. Run `tripkit refresh {trip['id']}`.")

    duration_days = (parse_iso_date(trip["end_date"]) - parse_iso_date(trip["start_date"])).days + 1
    packing_list = packing.generate_packing_list(
        snapshot["daily"], duration_days, trip["activity_tags"], trip["country"], home_country
    )
    weather_summary = packing.summarize_weather(snapshot["daily"])

    briefing_text = briefing.generate_briefing(
        trip_name=trip["name"],
        destination_name=trip["resolved_name"],
        start_date=trip["start_date"],
        end_date=trip["end_date"],
        activity_tags=trip["activity_tags"],
        mode=snapshot["mode"],
        avg_high_c=weather_summary.avg_high_c,
        avg_low_c=weather_summary.avg_low_c,
        any_rain=weather_summary.any_rain,
        any_wind=weather_summary.any_wind,
        packing_list=packing_list,
        api_key=api_key,
    )

    return {
        **trip,
        "mode": snapshot["mode"],
        "daily": snapshot["daily"],
        "packing_list": packing_list,
        "briefing": briefing_text,
    }


def cmd_show(args: argparse.Namespace) -> None:
    ensure_output_dir()
    conn = storage.connect(DB_PATH)
    try:
        trip = storage.get_trip(conn, args.trip_id)
        if trip is None:
            raise CliError(f"No trip with id {args.trip_id}.")
        bundle = _build_trip_bundle(conn, trip, os.environ.get("ANTHROPIC_API_KEY"), DEFAULT_HOME_COUNTRY)
    finally:
        conn.close()

    print(f"\n{bundle['name']} — {bundle['resolved_name']}")
    print(f"{bundle['start_date']} to {bundle['end_date']} [{', '.join(bundle['activity_tags'])}]")
    print(f"Weather mode: {bundle['mode']}\n")
    print(bundle["briefing"] + "\n")
    for category, items in bundle["packing_list"].items():
        print(f"{category}:")
        for item in items:
            print(f"  - {item}")


def cmd_delete(args: argparse.Namespace) -> None:
    ensure_output_dir()
    conn = storage.connect(DB_PATH)
    try:
        deleted = storage.delete_trip(conn, args.trip_id)
    finally:
        conn.close()
    if deleted:
        print(f"Deleted trip #{args.trip_id}.")
    else:
        raise CliError(f"No trip with id {args.trip_id}.")


def cmd_refresh(args: argparse.Namespace, today: date | None = None) -> None:
    today = today or datetime.now(timezone.utc).date()
    ensure_output_dir()
    conn = storage.connect(DB_PATH)
    try:
        trip = storage.get_trip(conn, args.trip_id)
        if trip is None:
            raise CliError(f"No trip with id {args.trip_id}.")
        mode, daily_readings = weather.get_weather_for_trip(
            trip["latitude"], trip["longitude"], parse_iso_date(trip["start_date"]), parse_iso_date(trip["end_date"]), today
        )
        storage.save_weather_snapshot(
            conn, trip["id"], mode, datetime.now(timezone.utc).isoformat(), [d.to_dict() for d in daily_readings]
        )
    finally:
        conn.close()
    print(f"Refreshed trip #{args.trip_id} ({mode}).")


def cmd_dashboard(_args: argparse.Namespace) -> None:
    ensure_output_dir()
    conn = storage.connect(DB_PATH)
    try:
        trips = storage.list_trips(conn)
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        bundles = []
        for trip in trips:
            try:
                bundles.append(_build_trip_bundle(conn, trip, api_key, DEFAULT_HOME_COUNTRY))
            except CliError as exc:
                print(f"Skipping trip #{trip['id']}: {exc}", file=sys.stderr)
    finally:
        conn.close()

    html_output = dashboard.generate_dashboard_html(bundles)
    with open(DASHBOARD_PATH, "w", encoding="utf-8") as handle:
        handle.write(html_output)
    print(f"Dashboard written to {os.path.abspath(DASHBOARD_PATH)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tripkit", description="Weather-aware trip prep and packing planner.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a new trip.")
    add_parser.add_argument("--name", required=True)
    add_parser.add_argument("--destination", required=True)
    add_parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    add_parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    add_parser.add_argument("--tags", required=True, help=f"Comma-separated, from: {', '.join(packing.ACTIVITY_TAGS)}")
    add_parser.set_defaults(func=cmd_add)

    list_parser = subparsers.add_parser("list", help="List saved trips.")
    list_parser.set_defaults(func=cmd_list)

    show_parser = subparsers.add_parser("show", help="Show a trip's briefing and packing list.")
    show_parser.add_argument("trip_id", type=int)
    show_parser.set_defaults(func=cmd_show)

    delete_parser = subparsers.add_parser("delete", help="Delete a trip.")
    delete_parser.add_argument("trip_id", type=int)
    delete_parser.set_defaults(func=cmd_delete)

    refresh_parser = subparsers.add_parser("refresh", help="Re-fetch weather for an existing trip.")
    refresh_parser.add_argument("trip_id", type=int)
    refresh_parser.set_defaults(func=cmd_refresh)

    dashboard_parser = subparsers.add_parser("dashboard", help="Generate the self-contained HTML dashboard.")
    dashboard_parser.set_defaults(func=cmd_dashboard)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except CliError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (geocoding.GeocodingError, weather.WeatherError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

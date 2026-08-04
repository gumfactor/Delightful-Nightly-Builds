"""Dockside CLI — Cottage & Boat Season Readiness Dashboard.

Run from the build folder root:
    python3 src/main.py <command> [options]
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ai_brief  # noqa: E402
import db  # noqa: E402
import render  # noqa: E402
import scoring  # noqa: E402
import weather_client  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dockside", description="Cottage & boat season readiness dashboard"
    )
    parser.add_argument("--db", default="dockside.db", help="Path to the SQLite database file")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize the database")

    p_add_site = subparsers.add_parser("add-site", help="Add a site")
    p_add_site.add_argument("name")
    p_add_site.add_argument("--location", help="Place name to geocode, e.g. 'Muskoka, Ontario'")
    p_add_site.add_argument("--lat", type=float)
    p_add_site.add_argument("--lon", type=float)

    subparsers.add_parser("list-sites", help="List configured sites")

    p_add_task = subparsers.add_parser("add-task", help="Add a recurring seasonal task")
    p_add_task.add_argument("name")
    p_add_task.add_argument("--site", required=True)
    p_add_task.add_argument("--category", required=True, choices=sorted(db.VALID_CATEGORIES))
    p_add_task.add_argument("--window-start-month", type=int, required=True)
    p_add_task.add_argument("--window-end-month", type=int, required=True)
    p_add_task.add_argument("--max-wind", type=float, default=None, help="Max wind speed in km/h")
    p_add_task.add_argument("--min-water-temp", type=float, default=None, help="Min water temp in °C")
    p_add_task.add_argument("--dry-days", type=int, default=None, help="Consecutive dry days required")
    p_add_task.add_argument("--frost-free", action="store_true")

    p_list_tasks = subparsers.add_parser("list-tasks", help="List configured tasks")
    p_list_tasks.add_argument("--site", default=None)

    p_sync = subparsers.add_parser("sync", help="Fetch live forecast/marine data and score readiness")
    p_sync.add_argument("--site", default=None, help="Sync only this site (default: all sites)")

    p_complete = subparsers.add_parser("complete", help="Mark a task done for this season")
    p_complete.add_argument("task_id", type=int)
    p_complete.add_argument("--date", default=None, help="Completion date YYYY-MM-DD (default: today)")

    p_render = subparsers.add_parser("render", help="Render the HTML dashboard")
    p_render.add_argument("--site", required=True)
    p_render.add_argument("--output", default=None)

    p_brief = subparsers.add_parser("brief", help="Generate a season readiness briefing")
    p_brief.add_argument("--site", required=True)

    return parser


def cmd_init(args, conn) -> None:
    db.init_db(conn)
    print(f"Initialized database at {args.db}")


def cmd_add_site(args, conn) -> None:
    db.init_db(conn)
    if args.lat is not None and args.lon is not None:
        latitude, longitude, place_name = args.lat, args.lon, args.location
    elif args.location:
        result = weather_client.geocode(args.location)
        latitude, longitude, place_name = result.latitude, result.longitude, result.name
    else:
        raise SystemExit("Provide either --location or both --lat and --lon")
    site_id = db.add_site(conn, args.name, place_name, latitude, longitude)
    print(f"Added site '{args.name}' (id={site_id}) at ({latitude:.4f}, {longitude:.4f})")


def cmd_list_sites(args, conn) -> None:
    sites = db.list_sites(conn)
    if not sites:
        print("No sites configured. Add one with add-site.")
        return
    for site in sites:
        if site["marine_available"] is None:
            marine = "unknown (sync to find out)"
        else:
            marine = "yes" if site["marine_available"] else "no"
        print(
            f"[{site['id']}] {site['name']} — {site['place_name'] or ''} "
            f"({site['latitude']:.4f}, {site['longitude']:.4f}) marine_data={marine}"
        )


def cmd_add_task(args, conn) -> None:
    db.init_db(conn)
    site = db.get_site_by_name(conn, args.site)
    if site is None:
        raise SystemExit(f"No site named '{args.site}'. Add it first with add-site.")
    task_id = db.add_task(
        conn, site["id"], args.name, args.category, args.window_start_month, args.window_end_month,
        max_wind_kmh=args.max_wind, min_water_temp_c=args.min_water_temp,
        dry_days_required=args.dry_days, frost_free_required=args.frost_free,
    )
    print(f"Added task '{args.name}' (id={task_id}) to site '{args.site}'")


def cmd_list_tasks(args, conn) -> None:
    site_id = None
    if args.site:
        site = db.get_site_by_name(conn, args.site)
        if site is None:
            raise SystemExit(f"No site named '{args.site}'")
        site_id = site["id"]
    tasks = db.list_tasks(conn, site_id=site_id, active_only=False)
    if not tasks:
        print("No tasks configured. Add one with add-task.")
        return
    for task in tasks:
        print(
            f"[{task['id']}] {task['name']} ({task['category']}) "
            f"window={task['window_start_month']}-{task['window_end_month']} "
            f"active={'yes' if task['active'] else 'no'}"
        )


def _sync_site(conn, site_row, today: date) -> None:
    forecasts = weather_client.fetch_forecast(site_row["latitude"], site_row["longitude"])
    marine = weather_client.fetch_marine(site_row["latitude"], site_row["longitude"])
    marine_by_date = {m.obs_date: m for m in marine}
    db.set_marine_available(conn, site_row["id"], bool(marine))

    for f in forecasts:
        m = marine_by_date.get(f.obs_date)
        db.upsert_observation(
            conn, site_row["id"], f.obs_date.isoformat(), f.temp_min_c, f.temp_max_c,
            f.precip_mm, f.wind_speed_max_kmh,
            m.wave_height_max_m if m else None, m.water_temp_c if m else None,
        )

    print(
        f"Synced {len(forecasts)} day(s) for site '{site_row['name']}' "
        f"(marine data: {'available' if marine else 'unavailable'})"
    )

    tasks = db.list_tasks(conn, site_id=site_row["id"], active_only=True)
    observations = [scoring.Observation.from_row(r) for r in db.list_observations(conn, site_row["id"])]
    for task_row in tasks:
        task = scoring.Task.from_row(task_row)
        last_completion_year = db.get_last_completion_year(conn, task_row["id"])
        status, best, _ = scoring.classify_task_status(task, observations, today, last_completion_year)
        best_day_str = best.obs_date.isoformat() if best else "none this week"
        print(f"  [{task_row['id']}] {task_row['name']}: {status} (best day: {best_day_str})")


def cmd_sync(args, conn) -> None:
    db.init_db(conn)
    today = date.today()
    if args.site:
        site = db.get_site_by_name(conn, args.site)
        if site is None:
            raise SystemExit(f"No site named '{args.site}'")
        sites = [site]
    else:
        sites = db.list_sites(conn)
    if not sites:
        raise SystemExit("No sites configured. Add one with add-site.")
    for site_row in sites:
        _sync_site(conn, site_row, today)


def cmd_complete(args, conn) -> None:
    task_row = db.get_task(conn, args.task_id)
    if task_row is None:
        raise SystemExit(f"No task with id {args.task_id}")
    completed_date = date.fromisoformat(args.date) if args.date else date.today()
    db.record_completion(conn, args.task_id, completed_date.year, completed_date.isoformat())
    next_year_estimate = scoring.add_one_year(completed_date)
    print(
        f"Marked task '{task_row['name']}' complete for {completed_date.year}. "
        f"Next season's window opens around {next_year_estimate.strftime('%B %Y')}."
    )


def cmd_render(args, conn) -> None:
    site_row = db.get_site_by_name(conn, args.site)
    if site_row is None:
        raise SystemExit(f"No site named '{args.site}'")
    today = date.today()
    observations_rows = db.list_observations(conn, site_row["id"])
    observations = [scoring.Observation.from_row(r) for r in observations_rows]

    task_cards_data = []
    for task_row in db.list_tasks(conn, site_id=site_row["id"], active_only=True):
        task = scoring.Task.from_row(task_row)
        last_completion_year = db.get_last_completion_year(conn, task_row["id"])
        status, best, evaluations = scoring.classify_task_status(
            task, observations, today, last_completion_year
        )
        if best is not None:
            constraints_for_best = best.constraints
        elif evaluations:
            constraints_for_best = evaluations[0].constraints
        else:
            constraints_for_best = None
        task_cards_data.append({
            "task_row": task_row,
            "status": status,
            "best_day": best.obs_date if best else None,
            "constraints_for_best": constraints_for_best,
        })

    boating_scores = [
        {"obs_date": o.obs_date.isoformat(), "score": scoring.boating_comfort_score(o)}
        for o in observations
    ]
    observations_for_render = [
        {
            "obs_date": o.obs_date.isoformat(),
            "temp_max_c": o.temp_max_c,
            "temp_min_c": o.temp_min_c,
            "precip_mm": o.precip_mm,
            "wind_speed_max_kmh": o.wind_speed_max_kmh,
        }
        for o in observations
    ]

    briefing_row = db.get_latest_briefing(conn, site_row["id"])
    briefing_text = briefing_row["text"] if briefing_row else None
    briefing_source = briefing_row["source"] if briefing_row else None

    html_out = render.render_dashboard(
        site_row, task_cards_data, observations_for_render, boating_scores,
        briefing_text, briefing_source,
        datetime.utcnow().isoformat(timespec="seconds") + "Z",
    )

    output_path = args.output or f"dockside-{site_row['name'].lower().replace(' ', '-')}.html"
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html_out)
    print(f"Rendered dashboard to {output_path}")


def cmd_brief(args, conn) -> None:
    site_row = db.get_site_by_name(conn, args.site)
    if site_row is None:
        raise SystemExit(f"No site named '{args.site}'")
    today = date.today()
    observations = [scoring.Observation.from_row(r) for r in db.list_observations(conn, site_row["id"])]
    summaries = []
    for task_row in db.list_tasks(conn, site_id=site_row["id"], active_only=True):
        task = scoring.Task.from_row(task_row)
        last_completion_year = db.get_last_completion_year(conn, task_row["id"])
        status, best, _ = scoring.classify_task_status(task, observations, today, last_completion_year)
        best_day_str = best.obs_date.isoformat() if best else "none this week"
        summaries.append(f"{task_row['name']} ({task_row['category']}): {status}, best day {best_day_str}")

    today_score = None
    today_obs = next((o for o in observations if o.obs_date == today), None)
    if today_obs:
        today_score = scoring.boating_comfort_score(today_obs)

    text, source = ai_brief.generate_briefing(site_row["name"], summaries, today_score)
    db.save_briefing(conn, site_row["id"], source, text)
    print(f"[{source}] {text}")


_HANDLERS = {
    "init": cmd_init,
    "add-site": cmd_add_site,
    "list-sites": cmd_list_sites,
    "add-task": cmd_add_task,
    "list-tasks": cmd_list_tasks,
    "sync": cmd_sync,
    "complete": cmd_complete,
    "render": cmd_render,
    "brief": cmd_brief,
}


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    conn = db.connect(args.db)
    try:
        _HANDLERS[args.command](args, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

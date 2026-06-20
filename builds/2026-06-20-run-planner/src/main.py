"""Run Planner CLI — log runs, view stats, plan by weather, generate HTML report."""

import argparse
import sys
from pathlib import Path

_SRC = Path(__file__).parent
sys.path.insert(0, str(_SRC))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="run-planner",
        description="Log running workouts and plan by weather forecast.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # log
    log_p = sub.add_parser("log", help="Record a run")
    log_p.add_argument("--date", required=True, help="Run date (YYYY-MM-DD)")
    log_p.add_argument("--distance", type=float, required=True, help="Distance in km")
    log_p.add_argument("--time", required=True, help="Duration as mm:ss or hh:mm:ss")
    log_p.add_argument("--effort", choices=["easy", "moderate", "hard"], default="moderate")
    log_p.add_argument("--notes", default="", help="Optional notes")

    # week
    sub.add_parser("week", help="This week's summary")

    # streak
    sub.add_parser("streak", help="Current consecutive-day streak")

    # plan
    plan_p = sub.add_parser("plan", help="Best running windows for the next 7 days")
    plan_p.add_argument("--lat", type=float, default=43.65, help="Latitude (default: Toronto)")
    plan_p.add_argument("--lon", type=float, default=-79.38, help="Longitude (default: Toronto)")

    # report
    report_p = sub.add_parser("report", help="Generate HTML dashboard")
    report_p.add_argument("--output", default="report.html", help="Output file (default: report.html)")
    report_p.add_argument("--lat", type=float, default=43.65)
    report_p.add_argument("--lon", type=float, default=-79.38)
    report_p.add_argument("--no-weather", action="store_true", help="Skip weather fetch")

    args = parser.parse_args()

    import store
    import analytics

    if args.command == "log":
        try:
            duration_sec = store.parse_duration(args.time)
            run = store.log_run(args.date, args.distance, duration_sec, args.effort, args.notes)
            print(
                f"Logged: {run['date']} — {run['distance_km']} km"
                f" @ {run['pace']} min/km [{run['effort']}]"
            )
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "week":
        runs = store.list_runs()
        s = analytics.weekly_summary(runs)
        streak = analytics.current_streak(runs)
        print(
            f"This week: {s['run_count']} run{'s' if s['run_count'] != 1 else ''}, "
            f"{s['total_km']} km, avg pace {s['avg_pace']} min/km"
        )
        if streak > 0:
            print(f"Streak: {streak} consecutive day{'s' if streak != 1 else ''}")

    elif args.command == "streak":
        runs = store.list_runs()
        streak = analytics.current_streak(runs)
        if streak == 0:
            print("No current streak.")
        else:
            print(f"Streak: {streak} consecutive day{'s' if streak != 1 else ''}")

    elif args.command == "plan":
        import weather as wx
        print(f"Fetching forecast for ({args.lat}, {args.lon})…")
        try:
            raw = wx.fetch_forecast(args.lat, args.lon)
            hours = wx.parse_forecast(raw)
            windows = wx.best_windows(hours, top_n=5)
            print(f"\n{'Time':<22} {'Feels Like':>10} {'Wind':>9} {'Rain%':>6} {'Score':>6}  Rating")
            print("-" * 70)
            for w in windows:
                from datetime import datetime as dt
                time_str = dt.fromisoformat(w["time"]).strftime("%a %b %d, %-I%p")
                print(
                    f"{time_str:<22} {w['apparent_temp_c']:>8.1f}°C"
                    f" {w['wind_speed_kmh']:>7.1f}km/h"
                    f" {w['precip_probability']:>5.0f}%"
                    f"  {w['score']:>5.1f}  {w['label']}"
                )
        except Exception as exc:
            print(f"Weather fetch failed: {exc}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "report":
        import weather as wx
        import report as rpt

        runs = store.list_runs()
        weekly_data = analytics.mileage_by_week(runs)
        summary = analytics.weekly_summary(runs)

        windows = []
        if not args.no_weather:
            try:
                raw = wx.fetch_forecast(args.lat, args.lon)
                hours = wx.parse_forecast(raw)
                windows = wx.best_windows(hours, top_n=10)
            except Exception as exc:
                print(f"Warning: weather fetch failed ({exc}) — skipping forecast.", file=sys.stderr)

        html = rpt.render_html(runs, weekly_data, windows, summary)
        out = Path(args.output)
        out.write_text(html)
        print(f"Report saved to {out.resolve()}")


if __name__ == "__main__":
    main()

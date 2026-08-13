#!/usr/bin/env python3
"""Macro Kitchen CLI — profile-and-training-aware meal planning.

Usage:
  python3 src/main.py profile set --sex male --age 38 --height-cm 178 --weight-kg 76 \\
      --activity-level moderate --goal maintain --goal-rate 0
  python3 src/main.py import-garmin sample_data/sample_garmin_activities.csv
  python3 src/main.py generate [--diet TAG] [--exclude TAG] [--ai-notes]
  python3 src/main.py list
  python3 src/main.py show <plan_id>
  python3 src/main.py grocery <plan_id>
  python3 src/main.py render [<plan_id>] [--out PATH]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BUILD_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BUILD_ROOT))

from src import ai_notes, garmin_import, grocery, nutrition, planner, render, storage
from src.recipes import RECIPES, VALID_TAGS

DB_PATH = str(BUILD_ROOT / "data" / "macro_kitchen.db")
DEFAULT_RENDER_PATH = str(BUILD_ROOT / "data" / "dashboard.html")

RECIPES_BY_ID = {r["id"]: r for r in RECIPES}


def cmd_profile_set(args: argparse.Namespace) -> int:
    conn = storage.connect(DB_PATH)
    profile = {
        "sex": args.sex,
        "age": args.age,
        "height_cm": args.height_cm,
        "weight_kg": args.weight_kg,
        "activity_level": args.activity_level,
        "goal": args.goal,
        "goal_rate_kg_per_week": args.goal_rate,
    }
    try:
        nutrition.calculate_bmr(profile["sex"], profile["age"], profile["height_cm"],
                                 profile["weight_kg"])
        nutrition.calculate_tdee(1500, profile["activity_level"])
        if profile["goal"] not in nutrition.VALID_GOALS:
            raise nutrition.NutritionError(f"goal must be one of {sorted(nutrition.VALID_GOALS)}")
    except nutrition.NutritionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    storage.save_profile(conn, profile)
    print("Profile saved.")
    return 0


def cmd_import_garmin(args: argparse.Namespace) -> int:
    conn = storage.connect(DB_PATH)
    summary = garmin_import.parse_activities_csv(args.csv_path)
    for warning in summary.warnings:
        print(f"Warning: {warning}", file=sys.stderr)

    import_id = storage.save_garmin_import(conn, summary)
    print(
        f"Imported {summary.activity_count} activities "
        f"({summary.window_start} to {summary.window_end}): "
        f"{summary.total_distance_km} km, {summary.total_calories} kcal logged. "
        f"Daily eating-budget adjustment: +{summary.daily_adjustment_kcal} kcal/day. "
        f"(import id {import_id})"
    )
    return 0


def _resolve_target(conn, use_garmin: bool):
    profile = storage.load_profile(conn)
    if profile is None:
        print("Error: no profile set. Run 'profile set' first.", file=sys.stderr)
        return None, None

    daily_adjustment = 0.0
    garmin_import_id = None
    if use_garmin:
        latest = storage.load_latest_garmin_import(conn)
        if latest is not None:
            daily_adjustment = latest["daily_adjustment_kcal"]
            garmin_import_id = latest["id"]

    target = nutrition.full_target(
        sex=profile["sex"], age=profile["age"], height_cm=profile["height_cm"],
        weight_kg=profile["weight_kg"], activity_level=profile["activity_level"],
        goal=profile["goal"], goal_rate_kg_per_week=profile["goal_rate_kg_per_week"],
        daily_adjustment_kcal=daily_adjustment,
    )
    return target, garmin_import_id


def cmd_generate(args: argparse.Namespace) -> int:
    conn = storage.connect(DB_PATH)

    if args.diet and args.diet not in VALID_TAGS:
        print(f"Error: --diet must be one of {sorted(VALID_TAGS)}", file=sys.stderr)
        return 1
    if args.exclude and args.exclude not in VALID_TAGS:
        print(f"Error: --exclude must be one of {sorted(VALID_TAGS)}", file=sys.stderr)
        return 1

    target, garmin_import_id = _resolve_target(conn, use_garmin=not args.no_garmin)
    if target is None:
        return 1

    try:
        meals = planner.generate_plan(
            target_calories=target.calories,
            target_protein_g=target.protein_g,
            diet_filter=args.diet,
            exclude_filter=args.exclude,
        )
    except planner.PlannerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    day_notes = {}
    ai_notes_used = False
    if args.ai_notes:
        day_totals = planner.plan_day_totals(meals, RECIPES_BY_ID)
        for day_index, totals in day_totals.items():
            names = [
                RECIPES_BY_ID[m["recipe_id"]]["name"]
                for m in meals if m["day_index"] == day_index
            ]
            note, used_ai = ai_notes.generate_day_note(totals, names)
            day_notes[day_index] = note
            ai_notes_used = ai_notes_used or used_ai

    plan_id = storage.save_plan(
        conn, target, args.diet, args.exclude, garmin_import_id, meals, day_notes, ai_notes_used
    )
    print(f"Generated plan #{plan_id}: {target.calories} kcal/day target "
          f"({target.protein_g}g P / {target.carbs_g}g C / {target.fat_g}g F).")
    if args.ai_notes:
        print(f"Chef's notes source: {'Claude Haiku' if ai_notes_used else 'deterministic template'}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    conn = storage.connect(DB_PATH)
    plans = storage.list_plans(conn)
    if not plans:
        print("No plans yet. Run 'generate' first.")
        return 0
    for plan in plans:
        print(
            f"#{plan['id']}  {plan['created_at'][:19]}  "
            f"{plan['target_calories']} kcal  diet={plan['diet_filter'] or '-'}"
        )
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    conn = storage.connect(DB_PATH)
    result = storage.load_plan(conn, args.plan_id)
    if result is None:
        print(f"Error: no plan with id {args.plan_id}", file=sys.stderr)
        return 1

    plan = result["plan"]
    day_totals = planner.plan_day_totals(result["meals"], RECIPES_BY_ID)
    print(f"Plan #{plan['id']} — target {plan['target_calories']} kcal/day")
    for day_index in sorted(day_totals):
        totals = day_totals[day_index]
        print(f"\nDay {day_index + 1}: {round(totals['calories'])} kcal, "
              f"{round(totals['protein_g'])}g P")
        for meal in sorted(
            (m for m in result["meals"] if m["day_index"] == day_index),
            key=lambda m: m["slot"],
        ):
            recipe = RECIPES_BY_ID[meal["recipe_id"]]
            multiplier = meal["portion_multiplier"]
            suffix = f" ({multiplier}x portion)" if multiplier != 1.0 else ""
            print(f"  {meal['slot']:>9}: {recipe['name']}{suffix}")
    return 0


def cmd_grocery(args: argparse.Namespace) -> int:
    conn = storage.connect(DB_PATH)
    result = storage.load_plan(conn, args.plan_id)
    if result is None:
        print(f"Error: no plan with id {args.plan_id}", file=sys.stderr)
        return 1

    items = grocery.aggregate_grocery_list(result["meals"], RECIPES_BY_ID)
    for item in items:
        print(f"  {item['qty']:>7} {item['unit']:<6} {item['name']}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    conn = storage.connect(DB_PATH)
    if args.plan_id is not None:
        result = storage.load_plan(conn, args.plan_id)
    else:
        result = storage.load_latest_plan(conn)

    if result is None:
        print("Error: no plan found to render.", file=sys.stderr)
        return 1

    items = grocery.aggregate_grocery_list(result["meals"], RECIPES_BY_ID)
    payload = render.build_dashboard_payload(result["plan"], result["meals"], items)
    html = render.render_html(payload)

    out_path = Path(args.out) if args.out else Path(DEFAULT_RENDER_PATH)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"Dashboard written to {out_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="macro-kitchen")
    subparsers = parser.add_subparsers(dest="command", required=True)

    profile_parser = subparsers.add_parser("profile")
    profile_sub = profile_parser.add_subparsers(dest="profile_command", required=True)
    set_parser = profile_sub.add_parser("set")
    set_parser.add_argument("--sex", required=True, choices=sorted(nutrition.VALID_SEX))
    set_parser.add_argument("--age", required=True, type=int)
    set_parser.add_argument("--height-cm", required=True, type=float)
    set_parser.add_argument("--weight-kg", required=True, type=float)
    set_parser.add_argument("--activity-level", required=True,
                             choices=sorted(nutrition.ACTIVITY_MULTIPLIERS))
    set_parser.add_argument("--goal", required=True, choices=sorted(nutrition.VALID_GOALS))
    set_parser.add_argument("--goal-rate", type=float, default=0.0,
                             help="kg/week, ignored when --goal maintain")
    set_parser.set_defaults(func=cmd_profile_set)

    import_parser = subparsers.add_parser("import-garmin")
    import_parser.add_argument("csv_path")
    import_parser.set_defaults(func=cmd_import_garmin)

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--diet", choices=sorted(VALID_TAGS), default=None)
    generate_parser.add_argument("--exclude", choices=sorted(VALID_TAGS), default=None)
    generate_parser.add_argument("--ai-notes", action="store_true")
    generate_parser.add_argument("--no-garmin", action="store_true",
                                  help="ignore any imported Garmin activity data")
    generate_parser.set_defaults(func=cmd_generate)

    list_parser = subparsers.add_parser("list")
    list_parser.set_defaults(func=cmd_list)

    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("plan_id", type=int)
    show_parser.set_defaults(func=cmd_show)

    grocery_parser = subparsers.add_parser("grocery")
    grocery_parser.add_argument("plan_id", type=int)
    grocery_parser.set_defaults(func=cmd_grocery)

    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("plan_id", type=int, nargs="?", default=None)
    render_parser.add_argument("--out", default=None)
    render_parser.set_defaults(func=cmd_render)

    return parser


def main(argv: list | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

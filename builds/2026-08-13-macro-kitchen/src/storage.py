"""SQLite persistence for profile, Garmin imports, and generated plans."""
from __future__ import annotations

import datetime as dt
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    sex TEXT NOT NULL,
    age INTEGER NOT NULL,
    height_cm REAL NOT NULL,
    weight_kg REAL NOT NULL,
    activity_level TEXT NOT NULL,
    goal TEXT NOT NULL,
    goal_rate_kg_per_week REAL NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS garmin_import (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    imported_at TEXT NOT NULL,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    total_distance_km REAL NOT NULL,
    total_duration_min REAL NOT NULL,
    total_calories REAL NOT NULL,
    activity_count INTEGER NOT NULL,
    daily_adjustment_kcal REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    target_calories REAL NOT NULL,
    target_protein_g REAL NOT NULL,
    target_carbs_g REAL NOT NULL,
    target_fat_g REAL NOT NULL,
    diet_filter TEXT,
    exclude_filter TEXT,
    used_garmin_import_id INTEGER,
    ai_notes_used INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (used_garmin_import_id) REFERENCES garmin_import(id)
);

CREATE TABLE IF NOT EXISTS plan_meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id INTEGER NOT NULL,
    day_index INTEGER NOT NULL,
    slot TEXT NOT NULL,
    recipe_id TEXT NOT NULL,
    portion_multiplier REAL NOT NULL DEFAULT 1.0,
    day_note TEXT,
    FOREIGN KEY (plan_id) REFERENCES plans(id)
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def save_profile(conn: sqlite3.Connection, profile: dict) -> None:
    conn.execute(
        """
        INSERT INTO profile (id, sex, age, height_cm, weight_kg, activity_level,
                              goal, goal_rate_kg_per_week, updated_at)
        VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            sex=excluded.sex, age=excluded.age, height_cm=excluded.height_cm,
            weight_kg=excluded.weight_kg, activity_level=excluded.activity_level,
            goal=excluded.goal, goal_rate_kg_per_week=excluded.goal_rate_kg_per_week,
            updated_at=excluded.updated_at
        """,
        (
            profile["sex"], profile["age"], profile["height_cm"], profile["weight_kg"],
            profile["activity_level"], profile["goal"], profile["goal_rate_kg_per_week"], _now(),
        ),
    )
    conn.commit()


def load_profile(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("SELECT * FROM profile WHERE id = 1").fetchone()
    return dict(row) if row else None


def save_garmin_import(conn: sqlite3.Connection, summary) -> int:
    cursor = conn.execute(
        """
        INSERT INTO garmin_import (imported_at, window_start, window_end, total_distance_km,
                                    total_duration_min, total_calories, activity_count,
                                    daily_adjustment_kcal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            _now(), summary.window_start, summary.window_end, summary.total_distance_km,
            summary.total_duration_min, summary.total_calories, summary.activity_count,
            summary.daily_adjustment_kcal,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def load_latest_garmin_import(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute(
        "SELECT * FROM garmin_import ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return dict(row) if row else None


def save_plan(
    conn: sqlite3.Connection,
    target,
    diet_filter: str | None,
    exclude_filter: str | None,
    used_garmin_import_id: int | None,
    meals: list,
    day_notes: dict | None,
    ai_notes_used: bool,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO plans (created_at, target_calories, target_protein_g, target_carbs_g,
                            target_fat_g, diet_filter, exclude_filter, used_garmin_import_id,
                            ai_notes_used)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            _now(), target.calories, target.protein_g, target.carbs_g, target.fat_g,
            diet_filter, exclude_filter, used_garmin_import_id, int(ai_notes_used),
        ),
    )
    plan_id = cursor.lastrowid
    day_notes = day_notes or {}
    for meal in meals:
        conn.execute(
            "INSERT INTO plan_meals (plan_id, day_index, slot, recipe_id, "
            "portion_multiplier, day_note) VALUES (?, ?, ?, ?, ?, ?)",
            (plan_id, meal["day_index"], meal["slot"], meal["recipe_id"],
             meal.get("portion_multiplier", 1.0), day_notes.get(meal["day_index"])),
        )
    conn.commit()
    return plan_id


def load_plan(conn: sqlite3.Connection, plan_id: int) -> dict | None:
    plan_row = conn.execute("SELECT * FROM plans WHERE id = ?", (plan_id,)).fetchone()
    if plan_row is None:
        return None
    meal_rows = conn.execute(
        "SELECT * FROM plan_meals WHERE plan_id = ? ORDER BY day_index, slot", (plan_id,)
    ).fetchall()
    return {"plan": dict(plan_row), "meals": [dict(r) for r in meal_rows]}


def load_latest_plan(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("SELECT id FROM plans ORDER BY id DESC LIMIT 1").fetchone()
    if row is None:
        return None
    return load_plan(conn, row["id"])


def list_plans(conn: sqlite3.Connection) -> list:
    rows = conn.execute("SELECT * FROM plans ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

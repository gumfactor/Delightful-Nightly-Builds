import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src import garmin_import, nutrition, planner, storage
from src.recipes import RECIPES

RECIPES_BY_ID = {r["id"]: r for r in RECIPES}


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    return storage.connect(db_path)


def test_save_and_load_profile_roundtrip(conn):
    profile = {
        "sex": "male", "age": 38, "height_cm": 178.0, "weight_kg": 76.0,
        "activity_level": "moderate", "goal": "maintain", "goal_rate_kg_per_week": 0.0,
    }
    storage.save_profile(conn, profile)
    loaded = storage.load_profile(conn)
    assert loaded["sex"] == "male"
    assert loaded["age"] == 38
    assert loaded["weight_kg"] == 76.0


def test_load_profile_returns_none_when_unset(conn):
    assert storage.load_profile(conn) is None


def test_save_profile_upserts_not_duplicates(conn):
    profile = {
        "sex": "male", "age": 38, "height_cm": 178.0, "weight_kg": 76.0,
        "activity_level": "moderate", "goal": "maintain", "goal_rate_kg_per_week": 0.0,
    }
    storage.save_profile(conn, profile)
    profile["weight_kg"] = 75.0
    storage.save_profile(conn, profile)
    count = conn.execute("SELECT COUNT(*) AS c FROM profile").fetchone()["c"]
    assert count == 1
    assert storage.load_profile(conn)["weight_kg"] == 75.0


def test_save_and_load_garmin_import_roundtrip(conn):
    summary = garmin_import.GarminSummary(
        window_start="2026-08-04", window_end="2026-08-10",
        total_distance_km=40.0, total_duration_min=250.0, total_calories=3800.0,
        activity_count=6, daily_adjustment_kcal=271.4, warnings=[],
    )
    import_id = storage.save_garmin_import(conn, summary)
    loaded = storage.load_latest_garmin_import(conn)
    assert loaded["id"] == import_id
    assert loaded["activity_count"] == 6
    assert loaded["daily_adjustment_kcal"] == pytest.approx(271.4)


def test_save_plan_creates_new_version_each_time(conn):
    target = nutrition.full_target(
        sex="male", age=38, height_cm=178, weight_kg=76,
        activity_level="moderate", goal="maintain", goal_rate_kg_per_week=0,
    )
    meals = planner.generate_plan(target.calories, target.protein_g)

    id1 = storage.save_plan(conn, target, None, None, None, meals, {}, False)
    id2 = storage.save_plan(conn, target, None, None, None, meals, {}, False)
    assert id1 != id2
    assert len(storage.list_plans(conn)) == 2


def test_load_plan_roundtrip_meals_match(conn):
    target = nutrition.full_target(
        sex="female", age=30, height_cm=165, weight_kg=60,
        activity_level="light", goal="lose", goal_rate_kg_per_week=0.5,
    )
    meals = planner.generate_plan(target.calories, target.protein_g)
    plan_id = storage.save_plan(conn, target, None, None, None, meals, {0: "test note"}, False)

    result = storage.load_plan(conn, plan_id)
    assert result["plan"]["target_calories"] == target.calories
    assert len(result["meals"]) == 28
    day0_notes = [m["day_note"] for m in result["meals"] if m["day_index"] == 0]
    assert "test note" in day0_notes


def test_load_plan_returns_none_for_missing_id(conn):
    assert storage.load_plan(conn, 999) is None


def test_load_latest_plan_returns_most_recent(conn):
    target = nutrition.full_target(
        sex="male", age=38, height_cm=178, weight_kg=76,
        activity_level="moderate", goal="maintain", goal_rate_kg_per_week=0,
    )
    meals = planner.generate_plan(target.calories, target.protein_g)
    storage.save_plan(conn, target, None, None, None, meals, {}, False)
    id2 = storage.save_plan(conn, target, None, None, None, meals, {}, False)

    latest = storage.load_latest_plan(conn)
    assert latest["plan"]["id"] == id2

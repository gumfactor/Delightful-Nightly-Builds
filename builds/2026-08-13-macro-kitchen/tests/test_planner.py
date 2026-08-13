import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src import planner
from src.recipes import RECIPES


def test_generate_plan_produces_28_meals():
    plan = planner.generate_plan(target_calories=2400, target_protein_g=150)
    assert len(plan) == 28


def test_generate_plan_covers_all_7_days_and_4_slots():
    plan = planner.generate_plan(target_calories=2400, target_protein_g=150)
    days = {m["day_index"] for m in plan}
    slots = {m["slot"] for m in plan}
    assert days == set(range(7))
    assert slots == {"breakfast", "lunch", "dinner", "snack"}
    for day in range(7):
        day_slots = sorted(m["slot"] for m in plan if m["day_index"] == day)
        assert day_slots == ["breakfast", "dinner", "lunch", "snack"]


def test_generate_plan_is_deterministic():
    plan_a = planner.generate_plan(target_calories=2400, target_protein_g=150)
    plan_b = planner.generate_plan(target_calories=2400, target_protein_g=150)
    assert plan_a == plan_b


def test_generate_plan_respects_diet_filter():
    plan = planner.generate_plan(target_calories=2000, target_protein_g=100, diet_filter="vegan")
    recipes_by_id = {r["id"]: r for r in RECIPES}
    for meal in plan:
        assert "vegan" in recipes_by_id[meal["recipe_id"]]["tags"]


def test_generate_plan_respects_exclude_filter():
    plan = planner.generate_plan(target_calories=2200, target_protein_g=130, exclude_filter="gluten_free")
    # exclude_filter removes recipes that HAVE the tag — remaining recipes must not have it.
    recipes_by_id = {r["id"]: r for r in RECIPES}
    for meal in plan:
        assert "gluten_free" not in recipes_by_id[meal["recipe_id"]]["tags"]


def test_generate_plan_raises_for_impossible_filter_combo():
    with pytest.raises(planner.PlannerError):
        planner.generate_plan(
            target_calories=2000, target_protein_g=100,
            diet_filter="vegan", exclude_filter="dairy_free",
        )


def test_generate_plan_raises_for_nonpositive_calories():
    with pytest.raises(planner.PlannerError):
        planner.generate_plan(target_calories=0, target_protein_g=100)


def test_no_repeat_within_3_days_per_slot_when_pool_allows():
    plan = planner.generate_plan(target_calories=2400, target_protein_g=150)
    for slot in ["breakfast", "lunch", "dinner", "snack"]:
        slot_meals = sorted(
            (m for m in plan if m["slot"] == slot), key=lambda m: m["day_index"]
        )
        for i in range(len(slot_meals) - 1):
            for j in range(i + 1, len(slot_meals)):
                gap = slot_meals[j]["day_index"] - slot_meals[i]["day_index"]
                if gap < planner.NO_REPEAT_WINDOW:
                    assert slot_meals[i]["recipe_id"] != slot_meals[j]["recipe_id"]


def test_plan_day_totals_sums_correctly():
    plan = planner.generate_plan(target_calories=2400, target_protein_g=150)
    recipes_by_id = {r["id"]: r for r in RECIPES}
    totals = planner.plan_day_totals(plan, recipes_by_id)
    assert len(totals) == 7
    day0_meals = [m for m in plan if m["day_index"] == 0]
    expected_calories = sum(
        recipes_by_id[m["recipe_id"]]["calories"] * m["portion_multiplier"] for m in day0_meals
    )
    assert totals[0]["calories"] == pytest.approx(expected_calories)


def test_every_meal_has_a_valid_portion_multiplier():
    plan = planner.generate_plan(target_calories=2800, target_protein_g=170)
    for meal in plan:
        assert meal["portion_multiplier"] in planner.PORTION_MULTIPLIERS


def test_daily_totals_within_reasonable_tolerance_of_target():
    target_calories = 2500
    plan = planner.generate_plan(target_calories=target_calories, target_protein_g=160)
    recipes_by_id = {r["id"]: r for r in RECIPES}
    totals = planner.plan_day_totals(plan, recipes_by_id)
    for day_index, day_totals in totals.items():
        deviation = abs(day_totals["calories"] - target_calories) / target_calories
        assert deviation <= 0.10, f"Day {day_index} deviated {deviation:.1%} from target"

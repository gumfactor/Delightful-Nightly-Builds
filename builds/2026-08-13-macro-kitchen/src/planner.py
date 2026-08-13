"""Deterministic constrained meal-plan builder.

No randomness: given the same recipe bank, target macros, and filters, the
planner always produces the same 7-day plan. Selection is a greedy search that
picks, for each day/slot, the recipe (from the filtered, not-recently-used pool)
that most reduces the day's remaining squared deviation from its calorie/protein
budget, prioritizing filling meals in a fixed slot order so results are stable.
"""
from __future__ import annotations

from src.recipes import RECIPES, VALID_SLOTS

SLOT_ORDER = ["breakfast", "lunch", "dinner", "snack"]
DAYS = 7
NO_REPEAT_WINDOW = 3  # a recipe can't be reused in the same slot within this many days

# Recipes are written as single realistic servings; a higher-calorie target (an
# active adult can easily need 2800-3200 kcal/day) is met by scaling the portion,
# the same way a person would actually eat a larger serving rather than a 5th meal.
PORTION_MULTIPLIERS = [0.75, 1.0, 1.25, 1.5, 1.75, 2.0]


class PlannerError(ValueError):
    """Raised when the recipe pool can't satisfy the requested constraints."""


def _filter_recipes(diet_filter: str | None, exclude_filter: str | None) -> list:
    pool = list(RECIPES)
    if diet_filter:
        pool = [r for r in pool if diet_filter in r["tags"]]
    if exclude_filter:
        pool = [r for r in pool if exclude_filter not in r["tags"]]
    return pool


def _score(
    recipe: dict, multiplier: float, remaining_calories: float, remaining_protein: float
) -> float:
    """Lower is better: squared deviation from the two most important remaining budgets."""
    cal_dev = (recipe["calories"] * multiplier) - remaining_calories
    protein_dev = (recipe["protein_g"] * multiplier) - remaining_protein
    return cal_dev**2 + (protein_dev**2 * 4)  # weight protein deviation more heavily


def generate_plan(
    target_calories: float,
    target_protein_g: float,
    diet_filter: str | None = None,
    exclude_filter: str | None = None,
) -> list:
    """Return a list of 28 dicts: {day_index, slot, recipe_id, portion_multiplier}."""
    if target_calories <= 0:
        raise PlannerError("target_calories must be positive")

    pool_by_slot = {}
    for slot in SLOT_ORDER:
        slot_pool = [
            r for r in _filter_recipes(diet_filter, exclude_filter) if r["slot"] == slot
        ]
        if len(slot_pool) < 2:
            raise PlannerError(
                f"Not enough recipes for slot '{slot}' after filtering "
                f"(diet={diet_filter!r}, exclude={exclude_filter!r}); found {len(slot_pool)}, need >= 2."
            )
        pool_by_slot[slot] = sorted(slot_pool, key=lambda r: r["id"])  # stable order

    # Per-slot budget: split calories/protein evenly across the day's 4 slots,
    # with snack getting a smaller share.
    slot_share = {"breakfast": 0.27, "lunch": 0.32, "dinner": 0.32, "snack": 0.09}

    recent_use = {slot: [] for slot in SLOT_ORDER}  # slot -> list of (day_index, recipe_id)
    plan = []

    for day_index in range(DAYS):
        for slot in SLOT_ORDER:
            remaining_calories = target_calories * slot_share[slot]
            remaining_protein = target_protein_g * slot_share[slot]

            blocked_ids = {
                rid for (used_day, rid) in recent_use[slot]
                if day_index - used_day < NO_REPEAT_WINDOW
            }
            candidates = [r for r in pool_by_slot[slot] if r["id"] not in blocked_ids]
            if not candidates:
                # Every recipe in the pool is currently blocked by the no-repeat rule —
                # relax the constraint for this single pick rather than fail the whole plan.
                candidates = pool_by_slot[slot]

            best_recipe, best_multiplier = min(
                (
                    (recipe, multiplier)
                    for recipe in candidates
                    for multiplier in PORTION_MULTIPLIERS
                ),
                key=lambda pair: _score(pair[0], pair[1], remaining_calories, remaining_protein),
            )
            plan.append({
                "day_index": day_index, "slot": slot, "recipe_id": best_recipe["id"],
                "portion_multiplier": best_multiplier,
            })
            recent_use[slot].append((day_index, best_recipe["id"]))

    return plan


def plan_day_totals(plan: list, recipes_by_id: dict) -> dict:
    """day_index -> {calories, protein_g, carbs_g, fat_g} summed across that day's meals."""
    totals = {
        d: {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0} for d in range(DAYS)
    }
    for meal in plan:
        recipe = recipes_by_id[meal["recipe_id"]]
        multiplier = meal.get("portion_multiplier", 1.0)
        day = totals[meal["day_index"]]
        day["calories"] += recipe["calories"] * multiplier
        day["protein_g"] += recipe["protein_g"] * multiplier
        day["carbs_g"] += recipe["carbs_g"] * multiplier
        day["fat_g"] += recipe["fat_g"] * multiplier
    return totals

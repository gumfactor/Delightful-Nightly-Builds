"""Aggregate ingredients across every meal in a plan into a shopping list."""
from __future__ import annotations


def aggregate_grocery_list(plan: list, recipes_by_id: dict) -> list:
    """Return a sorted list of {name, unit, qty} summed across all meals in the plan.

    Same ingredient name in different units is kept as separate line items
    (e.g. "milk / ml" and "milk / cup" would not be merged) — no unit-conversion
    table is attempted, since that's a real ambiguity source better left explicit
    than silently guessed at.
    """
    totals: dict[tuple[str, str], float] = {}

    for meal in plan:
        recipe = recipes_by_id[meal["recipe_id"]]
        multiplier = meal.get("portion_multiplier", 1.0)
        for ingredient in recipe["ingredients"]:
            key = (ingredient["name"], ingredient["unit"])
            totals[key] = totals.get(key, 0.0) + ingredient["qty"] * multiplier

    grocery_list = [
        {"name": name, "unit": unit, "qty": round(qty, 2)}
        for (name, unit), qty in totals.items()
    ]
    grocery_list.sort(key=lambda item: item["name"])
    return grocery_list

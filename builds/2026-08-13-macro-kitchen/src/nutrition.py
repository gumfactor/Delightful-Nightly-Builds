"""Deterministic BMR/TDEE/macro-target calculations (Mifflin-St Jeor)."""
from __future__ import annotations

from dataclasses import dataclass

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

VALID_SEX = {"male", "female"}
VALID_GOALS = {"lose", "maintain", "gain"}

# 1 kg of body fat ~= 7700 kcal.
KCAL_PER_KG = 7700.0

# Macro caloric density.
KCAL_PER_G_PROTEIN = 4.0
KCAL_PER_G_CARB = 4.0
KCAL_PER_G_FAT = 9.0

# Never let goal-rate math push the target below this fraction of BMR.
MIN_TARGET_AS_FRACTION_OF_BMR = 1.05


class NutritionError(ValueError):
    """Raised when profile inputs are invalid."""


@dataclass(frozen=True)
class MacroTarget:
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float


def calculate_bmr(sex: str, age: int, height_cm: float, weight_kg: float) -> float:
    """Mifflin-St Jeor BMR in kcal/day."""
    if sex not in VALID_SEX:
        raise NutritionError(f"sex must be one of {sorted(VALID_SEX)}, got {sex!r}")
    if age <= 0 or age > 120:
        raise NutritionError(f"age must be between 1 and 120, got {age}")
    if height_cm <= 0:
        raise NutritionError(f"height_cm must be positive, got {height_cm}")
    if weight_kg <= 0:
        raise NutritionError(f"weight_kg must be positive, got {weight_kg}")

    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == "male" else base - 161


def calculate_tdee(bmr: float, activity_level: str) -> float:
    if activity_level not in ACTIVITY_MULTIPLIERS:
        raise NutritionError(
            f"activity_level must be one of {sorted(ACTIVITY_MULTIPLIERS)}, got {activity_level!r}"
        )
    return bmr * ACTIVITY_MULTIPLIERS[activity_level]


def apply_goal_adjustment(
    tdee: float, bmr: float, goal: str, goal_rate_kg_per_week: float
) -> float:
    """Adjust TDEE for a weight loss/gain goal, never dropping below a BMR-based floor."""
    if goal not in VALID_GOALS:
        raise NutritionError(f"goal must be one of {sorted(VALID_GOALS)}, got {goal!r}")
    if goal_rate_kg_per_week < 0:
        raise NutritionError("goal_rate_kg_per_week must be >= 0")

    daily_delta = (goal_rate_kg_per_week * KCAL_PER_KG) / 7.0
    if goal == "lose":
        target = tdee - daily_delta
    elif goal == "gain":
        target = tdee + daily_delta
    else:
        target = tdee

    floor = bmr * MIN_TARGET_AS_FRACTION_OF_BMR
    return max(target, floor)


def apply_activity_adjustment(target_calories: float, daily_adjustment_kcal: float) -> float:
    """Add a Garmin-derived activity adjustment on top of the goal-adjusted target."""
    return target_calories + daily_adjustment_kcal


def calculate_macro_target(target_calories: float, weight_kg: float, goal: str) -> MacroTarget:
    """Split a calorie target into protein/carb/fat/fiber grams.

    Protein: 1.8 g/kg body weight (2.0 g/kg when the goal is a loss, to protect
    lean mass in a deficit) — grounded in body weight, not just a % of calories.
    Fat: 27% of total calories.
    Carbs: whatever's left after protein and fat.
    Fiber: a flat 14g per 1000 kcal floor (standard dietary guideline ratio).
    """
    if target_calories <= 0:
        raise NutritionError(f"target_calories must be positive, got {target_calories}")
    if weight_kg <= 0:
        raise NutritionError(f"weight_kg must be positive, got {weight_kg}")

    protein_per_kg = 2.0 if goal == "lose" else 1.8
    protein_g = protein_per_kg * weight_kg
    protein_kcal = protein_g * KCAL_PER_G_PROTEIN

    fat_kcal = target_calories * 0.27
    fat_g = fat_kcal / KCAL_PER_G_FAT

    remaining_kcal = target_calories - protein_kcal - fat_kcal
    if remaining_kcal < 0:
        # Extremely low target_calories relative to protein need — clamp carbs to 0
        # rather than produce a negative gram value.
        carbs_g = 0.0
    else:
        carbs_g = remaining_kcal / KCAL_PER_G_CARB

    fiber_g = (target_calories / 1000.0) * 14.0

    return MacroTarget(
        calories=round(target_calories, 1),
        protein_g=round(protein_g, 1),
        carbs_g=round(carbs_g, 1),
        fat_g=round(fat_g, 1),
        fiber_g=round(fiber_g, 1),
    )


def full_target(
    sex: str,
    age: int,
    height_cm: float,
    weight_kg: float,
    activity_level: str,
    goal: str,
    goal_rate_kg_per_week: float,
    daily_adjustment_kcal: float = 0.0,
) -> MacroTarget:
    """Convenience wrapper: profile inputs -> final MacroTarget."""
    bmr = calculate_bmr(sex, age, height_cm, weight_kg)
    tdee = calculate_tdee(bmr, activity_level)
    goal_adjusted = apply_goal_adjustment(tdee, bmr, goal, goal_rate_kg_per_week)
    final_calories = apply_activity_adjustment(goal_adjusted, daily_adjustment_kcal)
    return calculate_macro_target(final_calories, weight_kg, goal)

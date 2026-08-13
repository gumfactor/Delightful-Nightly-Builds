import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from src import nutrition


def test_bmr_male_reference_value():
    # Mifflin-St Jeor, male, 38y, 178cm, 76kg:
    # 10*76 + 6.25*178 - 5*38 + 5 = 760 + 1112.5 - 190 + 5 = 1687.5
    bmr = nutrition.calculate_bmr("male", 38, 178, 76)
    assert bmr == pytest.approx(1687.5, abs=0.1)


def test_bmr_female_reference_value():
    # 10*60 + 6.25*165 - 5*30 - 161 = 600 + 1031.25 - 150 - 161 = 1320.25
    bmr = nutrition.calculate_bmr("female", 30, 165, 60)
    assert bmr == pytest.approx(1320.25, abs=0.1)


def test_bmr_rejects_invalid_sex():
    with pytest.raises(nutrition.NutritionError):
        nutrition.calculate_bmr("other", 30, 170, 70)


def test_bmr_rejects_nonpositive_weight():
    with pytest.raises(nutrition.NutritionError):
        nutrition.calculate_bmr("male", 30, 170, 0)


def test_tdee_applies_correct_multiplier():
    bmr = 1600.0
    tdee = nutrition.calculate_tdee(bmr, "moderate")
    assert tdee == pytest.approx(1600 * 1.55)


def test_tdee_rejects_invalid_activity_level():
    with pytest.raises(nutrition.NutritionError):
        nutrition.calculate_tdee(1600, "superhuman")


def test_goal_adjustment_maintain_is_unchanged():
    target = nutrition.apply_goal_adjustment(2400, 1600, "maintain", 0)
    assert target == pytest.approx(2400)


def test_goal_adjustment_loss_reduces_calories():
    # 0.5 kg/week loss = 550 kcal/day deficit (0.5*7700/7)
    target = nutrition.apply_goal_adjustment(2400, 1600, "lose", 0.5)
    assert target == pytest.approx(2400 - 550, abs=1)


def test_goal_adjustment_never_drops_below_bmr_floor():
    # An aggressive loss rate that would push below BMR must be floored.
    target = nutrition.apply_goal_adjustment(1700, 1600, "lose", 3.0)
    assert target >= 1600 * nutrition.MIN_TARGET_AS_FRACTION_OF_BMR - 0.01


def test_goal_adjustment_gain_increases_calories():
    target = nutrition.apply_goal_adjustment(2400, 1600, "gain", 0.25)
    assert target > 2400


def test_activity_adjustment_adds_kcal():
    assert nutrition.apply_activity_adjustment(2000, 300) == 2300


def test_macro_target_kcal_roundtrip_within_tolerance():
    target = nutrition.calculate_macro_target(2400, 76, "maintain")
    reconstructed = (
        target.protein_g * nutrition.KCAL_PER_G_PROTEIN
        + target.carbs_g * nutrition.KCAL_PER_G_CARB
        + target.fat_g * nutrition.KCAL_PER_G_FAT
    )
    assert reconstructed == pytest.approx(2400, rel=0.02)


def test_macro_target_loss_goal_uses_higher_protein_per_kg():
    lose_target = nutrition.calculate_macro_target(2000, 76, "lose")
    maintain_target = nutrition.calculate_macro_target(2000, 76, "maintain")
    assert lose_target.protein_g > maintain_target.protein_g


def test_macro_target_rejects_nonpositive_calories():
    with pytest.raises(nutrition.NutritionError):
        nutrition.calculate_macro_target(0, 76, "maintain")


def test_full_target_end_to_end_produces_sane_numbers():
    target = nutrition.full_target(
        sex="male", age=38, height_cm=178, weight_kg=76,
        activity_level="moderate", goal="maintain", goal_rate_kg_per_week=0,
    )
    assert 1800 < target.calories < 3200
    assert target.protein_g > 0
    assert target.carbs_g >= 0
    assert target.fat_g > 0


def test_full_target_with_activity_adjustment_is_higher_than_without():
    base = nutrition.full_target(
        sex="male", age=38, height_cm=178, weight_kg=76,
        activity_level="moderate", goal="maintain", goal_rate_kg_per_week=0,
    )
    boosted = nutrition.full_target(
        sex="male", age=38, height_cm=178, weight_kg=76,
        activity_level="moderate", goal="maintain", goal_rate_kg_per_week=0,
        daily_adjustment_kcal=300,
    )
    assert boosted.calories > base.calories

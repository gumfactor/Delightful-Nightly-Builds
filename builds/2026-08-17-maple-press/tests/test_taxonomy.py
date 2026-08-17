import pytest

import taxonomy


def _businesses(n):
    return [{"name": f"Business {i}", "category": "Skincare"} for i in range(n)]


def test_check_eligibility_spotlight_accepts_one():
    taxonomy.check_eligibility("spotlight", _businesses(1))  # should not raise


def test_check_eligibility_spotlight_rejects_multiple():
    with pytest.raises(ValueError, match="expects exactly 1"):
        taxonomy.check_eligibility("spotlight", _businesses(2))


def test_check_eligibility_spotlight_rejects_zero():
    with pytest.raises(ValueError, match="at least 1"):
        taxonomy.check_eligibility("spotlight", _businesses(0))


def test_check_eligibility_gift_guide_rejects_two():
    with pytest.raises(ValueError, match="at least 3"):
        taxonomy.check_eligibility("gift_guide", _businesses(2))


def test_check_eligibility_gift_guide_accepts_three():
    taxonomy.check_eligibility("gift_guide", _businesses(3))  # should not raise


def test_check_eligibility_swap_it_accepts_two():
    taxonomy.check_eligibility("swap_it", _businesses(2))  # should not raise


def test_check_eligibility_swap_it_rejects_one():
    with pytest.raises(ValueError, match="at least 2"):
        taxonomy.check_eligibility("swap_it", _businesses(1))


def test_check_eligibility_local_spotlight_rejects_one():
    with pytest.raises(ValueError, match="at least 2"):
        taxonomy.check_eligibility("local_spotlight", _businesses(1))


def test_check_eligibility_local_spotlight_accepts_two():
    taxonomy.check_eligibility("local_spotlight", _businesses(2))  # should not raise


def test_check_eligibility_unknown_piece_type_raises():
    with pytest.raises(ValueError, match="Unknown piece type"):
        taxonomy.check_eligibility("not_a_real_type", _businesses(5))


def test_check_tone_compatibility_social_swap_it_rejected():
    with pytest.raises(ValueError, match="not valid"):
        taxonomy.check_tone_compatibility("swap_it", "social")


def test_check_tone_compatibility_social_local_spotlight_rejected():
    with pytest.raises(ValueError, match="not valid"):
        taxonomy.check_tone_compatibility("local_spotlight", "social")


def test_check_tone_compatibility_social_spotlight_accepted():
    taxonomy.check_tone_compatibility("spotlight", "social")  # should not raise


def test_check_tone_compatibility_social_gift_guide_accepted():
    taxonomy.check_tone_compatibility("gift_guide", "social")  # should not raise


def test_check_tone_compatibility_unknown_tone_raises():
    with pytest.raises(ValueError, match="Unknown tone"):
        taxonomy.check_tone_compatibility("spotlight", "sarcastic")


def test_check_occasion_valid_does_not_raise():
    taxonomy.check_occasion("holiday")  # should not raise


def test_check_occasion_unknown_raises():
    with pytest.raises(ValueError, match="Unknown occasion"):
        taxonomy.check_occasion("black-friday")

import pytest

import headlines


def test_select_headline_deterministic_with_no_history():
    context = {"name": "", "category": "Coffee", "count": 2, "province": ""}
    body_text = "Some deterministic body text about Coffee businesses."
    headline, overlap = headlines.select_headline("swap_it", "general", context, body_text, [])
    expected = headlines.FORMULA_BANK["swap_it"]["general"][0].format(**context)
    assert headline == expected
    assert overlap == 0.0


def test_select_headline_deterministic_repeat_call_same_result():
    context = {"name": "", "category": "Coffee", "count": 2, "province": ""}
    body_text = "Some deterministic body text about Coffee businesses."
    headline_a, _ = headlines.select_headline("swap_it", "general", context, body_text, [])
    headline_b, _ = headlines.select_headline("swap_it", "general", context, body_text, [])
    assert headline_a == headline_b


def test_select_headline_avoids_near_duplicate_with_history():
    context = {"name": "", "category": "Coffee", "count": 2, "province": ""}
    body_text = "Some deterministic body text about Coffee businesses."

    first_headline, _ = headlines.select_headline("swap_it", "general", context, body_text, [])
    history = [f"{first_headline}\n\n{body_text}"]

    second_headline, second_overlap = headlines.select_headline(
        "swap_it", "general", context, body_text, history
    )

    assert second_headline != first_headline
    assert second_overlap < 1.0


def test_select_headline_unknown_piece_type_raises():
    with pytest.raises(ValueError, match="Unknown piece type"):
        headlines.select_headline("not_real", "general", {}, "body", [])


def test_select_headline_unknown_occasion_raises():
    context = {"name": "Acme", "category": "Skincare", "count": 1, "province": ""}
    with pytest.raises(ValueError, match="No headline formulas"):
        headlines.select_headline("spotlight", "black-friday", context, "body", [])


def test_formula_bank_covers_every_piece_type_and_occasion():
    import taxonomy

    for piece_type in taxonomy.PIECE_TYPES:
        assert piece_type in headlines.FORMULA_BANK
        for occasion in taxonomy.OCCASIONS:
            formulas = headlines.FORMULA_BANK[piece_type].get(occasion)
            assert formulas, f"missing formulas for ({piece_type}, {occasion})"

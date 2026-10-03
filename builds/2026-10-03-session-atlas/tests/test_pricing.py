import json

import pytest

from atlas.pricing import DEFAULT_PRICES, estimate_cost, family_for, load_prices


def test_cost_matches_manual_arithmetic():
    usage = {"claude-sonnet-4-5": {"input": 1_000_000, "output": 1_000_000, "cache_write": 0, "cache_read": 1_000_000}}
    cost, unpriced = estimate_cost(usage, DEFAULT_PRICES)
    assert cost == pytest.approx(3.0 + 15.0 + 0.3) and not unpriced


def test_unknown_model_is_flagged_and_costs_zero():
    cost, unpriced = estimate_cost({"mystery-1": {"input": 500, "output": 5}}, DEFAULT_PRICES)
    assert cost == 0 and unpriced


def test_unknown_model_with_zero_tokens_is_not_flagged():
    assert estimate_cost({"mystery-1": {"input": 0}}, DEFAULT_PRICES) == (0.0, False)


def test_family_match_is_case_insensitive():
    assert family_for("Claude-OPUS-4", DEFAULT_PRICES) == "opus"


def test_price_overrides_merge_over_defaults(tmp_path):
    path = tmp_path / "p.json"
    path.write_text(json.dumps({"sonnet": {"input": 9}, "newmodel": {"output": 2}}))
    prices = load_prices(path)
    assert prices["sonnet"]["input"] == 9 and prices["sonnet"]["output"] == 15.0
    assert prices["newmodel"]["output"] == 2 and prices["newmodel"]["input"] == 0.0
    assert DEFAULT_PRICES["sonnet"]["input"] == 3.0  # defaults not mutated


def test_bad_price_file_raises_value_error(tmp_path):
    path = tmp_path / "p.json"
    path.write_text("[1]")
    with pytest.raises(ValueError):
        load_prices(path)
    with pytest.raises(ValueError):
        load_prices(tmp_path / "missing.json")

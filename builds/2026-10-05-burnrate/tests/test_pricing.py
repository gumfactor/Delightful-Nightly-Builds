import json

import pytest

from burnrate.pricing import PriceTable, PricingError


@pytest.fixture
def table():
    return PriceTable({"sonnet": {"input": 3, "output": 15}, "sonnet-special": {"input": 1, "output": 2}})


def test_longest_substring_wins(table):
    assert table.rate_for("claude-sonnet-special-1").input == 1
    assert table.rate_for("claude-sonnet-4-5").input == 3


def test_unknown_model_is_unpriced(table):
    assert table.rate_for("mystery") is None
    assert table.cost("mystery", 1, 1, 1, 1) is None


def test_cost_uses_default_cache_multipliers(table):
    cost = table.cost("sonnet", 1_000_000, 1_000_000, 1_000_000, 1_000_000)
    assert cost == pytest.approx(3 + 15 + 3.75 + 0.3)


def test_cache_savings_is_input_minus_read_rate(table):
    assert table.cache_savings("sonnet", 1_000_000) == pytest.approx(2.7)
    assert table.cache_savings("mystery", 1_000_000) == 0.0


def test_load_rejects_bad_files(tmp_path):
    bad = tmp_path / "p.json"
    bad.write_text("not json")
    with pytest.raises(PricingError):
        PriceTable.load(bad)
    bad.write_text(json.dumps({"models": {"x": {"input": "a"}}}))
    with pytest.raises(PricingError):
        PriceTable.load(bad)


def test_default_pricing_file_loads():
    assert PriceTable.load().rate_for("claude-haiku-4-5-20251001") is not None

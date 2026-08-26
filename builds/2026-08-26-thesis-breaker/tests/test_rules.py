from src.rules import (
    valuation_stretch, growth_deceleration, margin_debt_risk,
    insider_selling, narrative_fragility, run_all_rules,
)


def make_data(**overrides):
    base = {
        "ticker": "AAPL",
        "sector": "Technology",
        "trailing_pe": 20.0,
        "forward_pe": 18.0,
        "price_to_sales": 5.0,
        "debt_to_equity": 50.0,
        "quarterly_revenue_yoy_growth": None,
        "quarterly_operating_margin": None,
        "insider_transactions": None,
    }
    base.update(overrides)
    return base


def test_valuation_stretch_fires_above_sector_threshold():
    data = make_data(trailing_pe=40.0, sector="Technology")
    result = valuation_stretch(data)
    assert result.fired is True
    assert "35.0" in result.detail


def test_valuation_stretch_clear_below_threshold():
    data = make_data(trailing_pe=20.0, sector="Technology")
    result = valuation_stretch(data)
    assert result.fired is False


def test_valuation_stretch_unavailable_when_pe_missing():
    data = make_data(trailing_pe=None)
    result = valuation_stretch(data)
    assert result.fired is None


def test_valuation_stretch_uses_default_threshold_for_unknown_sector():
    data = make_data(trailing_pe=26.0, sector="Unknown Sector")
    result = valuation_stretch(data)
    assert result.fired is True  # default threshold is 25.0


def test_growth_deceleration_fires_on_monotonic_decline():
    data = make_data(quarterly_revenue_yoy_growth=[0.03, 0.07, 0.09, 0.12])
    result = growth_deceleration(data)
    assert result.fired is True


def test_growth_deceleration_clear_when_not_monotonic():
    data = make_data(quarterly_revenue_yoy_growth=[0.15, 0.07, 0.09, 0.05])
    result = growth_deceleration(data)
    assert result.fired is False


def test_growth_deceleration_unavailable_with_insufficient_data():
    data = make_data(quarterly_revenue_yoy_growth=[0.05])
    result = growth_deceleration(data)
    assert result.fired is None


def test_margin_debt_risk_fires_on_high_debt():
    data = make_data(debt_to_equity=250.0, quarterly_operating_margin=None)
    result = margin_debt_risk(data)
    assert result.fired is True


def test_margin_debt_risk_fires_on_declining_margin_even_with_low_debt():
    data = make_data(debt_to_equity=10.0, quarterly_operating_margin=[0.27, 0.29, 0.31])
    result = margin_debt_risk(data)
    assert result.fired is True


def test_margin_debt_risk_clear_when_both_fine():
    data = make_data(debt_to_equity=10.0, quarterly_operating_margin=[0.31, 0.30, 0.29])
    result = margin_debt_risk(data)
    assert result.fired is False


def test_margin_debt_risk_unavailable_when_nothing_provided():
    data = make_data(debt_to_equity=None, quarterly_operating_margin=None)
    result = margin_debt_risk(data)
    assert result.fired is None


def test_insider_selling_fires_when_sells_exceed_buys():
    data = make_data(insider_transactions=[
        {"insider": "Doe, Jane", "transaction": "Sale", "shares": 5000.0, "value": 850000.0},
        {"insider": "Smith, Bob", "transaction": "Purchase", "shares": 1000.0, "value": 170000.0},
    ])
    result = insider_selling(data)
    assert result.fired is True


def test_insider_selling_clear_when_buys_exceed_sells():
    data = make_data(insider_transactions=[
        {"insider": "Doe, Jane", "transaction": "Sale", "shares": 100.0, "value": 10000.0},
        {"insider": "Smith, Bob", "transaction": "Purchase", "shares": 5000.0, "value": 900000.0},
    ])
    result = insider_selling(data)
    assert result.fired is False


def test_insider_selling_unavailable_when_no_transactions():
    data = make_data(insider_transactions=None)
    result = insider_selling(data)
    assert result.fired is None


def test_narrative_fragility_clear_when_no_keywords_present():
    result = narrative_fragility(make_data(), "This company has interesting products.")
    assert result.fired is False


def test_narrative_fragility_fires_on_unverifiable_claim():
    data = make_data(trailing_pe=None)
    result = narrative_fragility(data, "This stock looks reasonably valued right now.")
    assert result.fired is True
    assert "valuation" in result.detail


def test_narrative_fragility_fires_on_contradicted_claim():
    data = make_data(trailing_pe=40.0, sector="Technology")
    prior = [valuation_stretch(data)]
    result = narrative_fragility(data, "This stock looks reasonably valued right now.", prior_results=prior)
    assert result.fired is True
    assert "contradicts" in result.detail


def test_run_all_rules_returns_five_results():
    data = make_data(trailing_pe=40.0, sector="Technology")
    results = run_all_rules(data, "reasonably valued")
    assert len(results) == 5
    keys = {r.key for r in results}
    assert keys == {
        "valuation_stretch", "growth_deceleration", "margin_debt_risk",
        "insider_selling", "narrative_fragility",
    }

from src.rules import RuleResult
from src.personas import PersonaScore
from src.render import render_report


def make_results():
    return [
        RuleResult("valuation_stretch", "Valuation Stretch", True, "P/E of 40 exceeds threshold of 35."),
        RuleResult("growth_deceleration", "Growth Deceleration", False, "Growth did not decelerate."),
        RuleResult("margin_debt_risk", "Margin / Debt Risk", None, "Not enough data."),
        RuleResult("insider_selling", "Insider Selling Signal", None, "No data available."),
        RuleResult("narrative_fragility", "Narrative Fragility", True, "Contradicted claim."),
    ]


def make_personas():
    r = make_results()
    return [
        PersonaScore("value_skeptic", "Value Skeptic", 70, [r[0]], [r[1]], [r[2], r[3]]),
        PersonaScore("macro_bear", "Macro Bear", 30, [], [r[1]], [r[2]]),
        PersonaScore("governance_hawk", "Governance Hawk", None, [], [], [r[3]]),
    ]


def base_data(insider_transactions=None):
    return {
        "sector": "Technology", "trailing_pe": 40.0, "forward_pe": 32.0,
        "price_to_sales": 8.0, "debt_to_equity": 50.0,
        "quarterly_revenue_yoy_growth": [0.03, 0.07, 0.09, 0.12],
        "quarterly_operating_margin": [0.27, 0.29, 0.31],
        "insider_transactions": insider_transactions,
    }


def render(ticker="AAPL", thesis_text="Bullish thesis.", history_scores=None, insider_transactions=None):
    personas = make_personas()
    narratives = {p.key: (f"Narrative for {p.name}", False) for p in personas}
    return render_report(
        ticker=ticker, thesis_text=thesis_text, data=base_data(insider_transactions), results=make_results(),
        persona_scores=personas, narratives=narratives, overall_score=50,
        history_scores=history_scores,
    )


def test_render_includes_all_three_persona_names():
    html = render()
    assert "Value Skeptic" in html
    assert "Macro Bear" in html
    assert "Governance Hawk" in html


def test_render_escapes_script_tag_in_thesis_text():
    payload = "</script><script>alert(1)</script>"
    html = render(thesis_text=payload)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_render_escapes_ticker_field():
    payload = "<img src=x onerror=alert(1)>"
    html = render(ticker=payload)
    assert "<img src=x onerror=alert(1)>" not in html
    assert "&lt;img" in html


def test_render_shows_history_chart_only_with_two_or_more_runs():
    with_history = render(history_scores=[40, 55])
    without_history = render(history_scores=[40])
    assert "historyChart" in with_history
    assert "historyChart" not in without_history


def test_render_includes_triggered_checklist_labels():
    html = render()
    assert "Valuation Stretch" in html
    assert "Narrative Fragility" in html


def test_render_produces_valid_looking_html_document():
    html = render()
    assert html.strip().startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_render_shows_insider_transaction_table_when_present():
    html = render(insider_transactions=[
        {"insider": "Doe, Jane", "transaction": "Sale", "shares": 5000, "value": 850000},
    ])
    assert "Doe, Jane" in html
    assert "Insider Transactions" in html


def test_render_omits_insider_table_when_unavailable():
    html = render(insider_transactions=None)
    assert "Insider Transactions" not in html


def test_render_escapes_malicious_insider_name():
    payload = "<img src=x onerror=alert(1)>"
    html = render(insider_transactions=[
        {"insider": payload, "transaction": "Sale", "shares": 100, "value": 1000},
    ])
    assert "<img src=x onerror=alert(1)>" not in html
    assert "&lt;img src=x onerror=alert(1)&gt;" in html

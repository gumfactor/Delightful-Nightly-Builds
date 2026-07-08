import datetime
import json
import re

from src import report_html
from src.parser import Transaction


def _txn(date, description, amount, category="Other", recurring=False):
    t = Transaction(date=date, description=description, amount=amount, category=category)
    t.recurring = recurring
    return t


def _render(transactions=None, budget_status=None):
    transactions = transactions or [
        _txn(datetime.date(2026, 1, 1), "Test Merchant", -10.0, category="Dining"),
    ]
    summary = {
        "total_income": 1000.0, "total_expenses": 10.0, "net": 990.0,
        "transaction_count": len(transactions), "months_covered": 1, "avg_daily_spend": 10.0,
    }
    monthly = [{"month": "2026-01", "income": 1000.0, "expenses": 10.0, "net": 990.0}]
    categories = [{"category": "Dining", "total": 10.0, "count": 1, "pct_of_expenses": 100.0}]
    top_merchants = [{"merchant": "Test Merchant", "total": 10.0, "count": 1}]
    recurring = []
    return report_html.render_html(
        summary, monthly, categories, top_merchants, recurring, transactions,
        budget_status, "Test insights paragraph.",
    )


def test_html_contains_pinned_chartjs_version():
    html = _render()
    assert "chart.js@4.4.4" in html


def test_html_embeds_transaction_data_as_json():
    html = _render()
    match = re.search(
        r'<script id="ledger-data" type="application/json">(.*?)</script>', html, re.DOTALL
    )
    assert match is not None
    data = json.loads(match.group(1))
    assert data["summary"]["total_income"] == 1000.0
    assert len(data["transactions"]) == 1


def test_html_is_well_formed_document():
    html = _render()
    assert html.strip().startswith("<!DOCTYPE html>")
    assert "<html" in html and html.rstrip().endswith("</html>")
    assert "<head>" in html and "</head>" in html
    assert "<body>" in html and "</body>" in html
    assert "<title>Ledger Lens" in html


def test_html_escapes_transaction_description_xss():
    malicious = [_txn(datetime.date(2026, 1, 1), "<script>alert(1)</script>", -5.0)]
    html = _render(transactions=malicious)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_html_renders_budget_section_when_provided():
    budget_status = [{
        "category": "Dining", "monthly_cap": 50, "monthly_avg_actual": 60.0,
        "over_budget": True, "pct_of_cap": 120.0,
    }]
    html = _render(budget_status=budget_status)
    assert "Budget vs. Actual" in html
    assert "over" in html


def test_html_shows_no_budgets_message_when_absent():
    html = _render(budget_status=None)
    assert "No budgets.json provided" in html


def test_html_guards_chart_calls_against_missing_chartjs():
    # If the Chart.js CDN fails to load, `Chart` is undefined in the browser.
    # The inline script must check for that before calling `new Chart(...)`,
    # otherwise a ReferenceError there would abort the search/sort code below it.
    html = _render()
    script_start = html.index('<script>\n  const data')
    script = html[script_start:]
    assert "typeof Chart === 'undefined'" in script
    chart_guard_pos = script.index("typeof Chart === 'undefined'")
    first_new_chart_pos = script.index("new Chart(")
    assert chart_guard_pos < first_new_chart_pos

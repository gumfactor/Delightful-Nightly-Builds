import datetime

from src import analyze
from src.parser import Transaction


def _txn(date, description, amount, category="Other"):
    return Transaction(date=date, description=description, amount=amount, category=category)


def test_compute_summary_totals():
    txns = [
        _txn(datetime.date(2026, 1, 1), "Salary", 2000.0),
        _txn(datetime.date(2026, 1, 5), "Groceries", -100.0),
        _txn(datetime.date(2026, 1, 10), "Dining", -50.0),
    ]
    summary = analyze.compute_summary(txns)
    assert summary["total_income"] == 2000.0
    assert summary["total_expenses"] == 150.0
    assert summary["net"] == 1850.0
    assert summary["transaction_count"] == 3


def test_avg_daily_spend_calculation():
    txns = [
        _txn(datetime.date(2026, 1, 1), "A", -100.0),
        _txn(datetime.date(2026, 1, 11), "B", -100.0),
    ]
    summary = analyze.compute_summary(txns)
    # 11-day span (inclusive), $200 total expenses -> ~18.18/day
    assert summary["avg_daily_spend"] == round(200 / 11, 2)


def test_monthly_breakdown_groups_correctly():
    txns = [
        _txn(datetime.date(2026, 1, 5), "A", -50.0),
        _txn(datetime.date(2026, 2, 5), "B", -75.0),
        _txn(datetime.date(2026, 2, 20), "C", 500.0),
    ]
    monthly = analyze.compute_monthly_breakdown(txns)
    assert len(monthly) == 2
    jan, feb = monthly
    assert jan["month"] == "2026-01"
    assert jan["expenses"] == 50.0
    assert feb["income"] == 500.0
    assert feb["expenses"] == 75.0


def test_category_breakdown_sums_to_total_expenses():
    txns = [
        _txn(datetime.date(2026, 1, 1), "A", -30.0, category="Groceries"),
        _txn(datetime.date(2026, 1, 2), "B", -20.0, category="Dining"),
        _txn(datetime.date(2026, 1, 3), "C", -10.0, category="Groceries"),
        _txn(datetime.date(2026, 1, 4), "D", 1000.0, category="Income"),
    ]
    breakdown = analyze.compute_category_breakdown(txns)
    total = sum(row["total"] for row in breakdown)
    assert round(total, 2) == 60.0
    groceries = next(r for r in breakdown if r["category"] == "Groceries")
    assert groceries["total"] == 40.0
    assert groceries["count"] == 2


def test_top_merchants_ranking():
    txns = [
        _txn(datetime.date(2026, 1, 1), "Starbucks", -5.0),
        _txn(datetime.date(2026, 1, 2), "Starbucks", -5.0),
        _txn(datetime.date(2026, 1, 3), "Amazon", -100.0),
    ]
    top = analyze.compute_top_merchants(txns)
    assert top[0]["merchant"] == "Amazon"
    assert top[0]["total"] == 100.0
    starbucks = next(m for m in top if "Starbucks" in m["merchant"])
    assert starbucks["count"] == 2
    assert starbucks["total"] == 10.0


def test_recurring_detection_flags_repeated_merchant():
    txns = [
        _txn(datetime.date(2026, 1, 3), "NETFLIX.COM", -16.99),
        _txn(datetime.date(2026, 2, 3), "NETFLIX.COM", -16.99),
        _txn(datetime.date(2026, 3, 3), "NETFLIX.COM", -16.99),
    ]
    recurring = analyze.detect_recurring(txns)
    assert len(recurring) == 1
    assert recurring[0]["merchant"] == "NETFLIX.COM"
    assert recurring[0]["occurrences"] == 3
    assert all(t.recurring for t in txns)


def test_recurring_detection_ignores_one_off_charge():
    txns = [
        _txn(datetime.date(2026, 1, 3), "ONE TIME PURCHASE", -200.0),
        _txn(datetime.date(2026, 2, 5), "DIFFERENT MERCHANT", -50.0),
    ]
    recurring = analyze.detect_recurring(txns)
    assert recurring == []
    assert not any(t.recurring for t in txns)


def test_recurring_detection_requires_similar_amount():
    # Same merchant but wildly different amounts across months should not be
    # collapsed into one recurring group covering both.
    txns = [
        _txn(datetime.date(2026, 1, 5), "AMAZON.CA", -15.00),
        _txn(datetime.date(2026, 2, 5), "AMAZON.CA", -15.50),
        _txn(datetime.date(2026, 3, 5), "AMAZON.CA", -300.00),
    ]
    recurring = analyze.detect_recurring(txns)
    assert len(recurring) == 1
    assert recurring[0]["occurrences"] == 2
    assert recurring[0]["avg_amount"] < 100


def test_recurring_detection_requires_multiple_distinct_months():
    txns = [
        _txn(datetime.date(2026, 1, 3), "GYM MEMBERSHIP", -40.0),
        _txn(datetime.date(2026, 1, 17), "GYM MEMBERSHIP", -40.0),
    ]
    # Same month twice does not count as recurring across months.
    recurring = analyze.detect_recurring(txns)
    assert recurring == []


def test_budget_comparison_flags_over_budget():
    category_breakdown = [
        {"category": "Groceries", "total": 700.0, "count": 10, "pct_of_expenses": 50.0},
        {"category": "Dining", "total": 100.0, "count": 5, "pct_of_expenses": 10.0},
    ]
    budgets = {"Groceries": 600, "Dining": 300}
    results = analyze.compare_budgets(category_breakdown, budgets, months_covered=1)
    groceries = next(r for r in results if r["category"] == "Groceries")
    dining = next(r for r in results if r["category"] == "Dining")
    assert groceries["over_budget"] is True
    assert dining["over_budget"] is False


def test_budget_comparison_handles_missing_category():
    results = analyze.compare_budgets([], {"Travel": 200}, months_covered=1)
    assert results[0]["monthly_avg_actual"] == 0.0
    assert results[0]["over_budget"] is False


def test_normalize_merchant_strips_reference_numbers():
    a = analyze.normalize_merchant("AMAZON.CA*123456789")
    b = analyze.normalize_merchant("amazon.ca")
    assert a == b


def test_fallback_insights_mentions_top_category():
    summary = {
        "total_expenses": 500.0, "transaction_count": 10,
        "months_covered": 1, "avg_daily_spend": 16.67,
    }
    categories = [{"category": "Groceries", "total": 300.0, "pct_of_expenses": 60.0, "count": 5}]
    text = analyze.generate_fallback_insights(summary, categories, [])
    assert "Groceries" in text
    assert "500.00" in text

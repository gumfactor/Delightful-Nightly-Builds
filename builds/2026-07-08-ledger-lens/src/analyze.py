"""Monthly aggregation, recurring-charge detection, and budget comparison."""

from __future__ import annotations

import re
from collections import defaultdict

_MERCHANT_NOISE_RE = re.compile(r"\d{3,}|#\S+|\*\S+")
_WHITESPACE_RE = re.compile(r"\s+")

RECURRING_MIN_MONTHS = 2
RECURRING_AMOUNT_TOLERANCE = 0.05  # 5%


def normalize_merchant(description: str) -> str:
    """Collapse a description down to a stable merchant key for recurring detection."""
    cleaned = _MERCHANT_NOISE_RE.sub("", description.lower())
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned


def month_key(date) -> str:
    return f"{date.year:04d}-{date.month:02d}"


def compute_summary(transactions: list) -> dict:
    income = sum(t.amount for t in transactions if t.amount > 0)
    expenses = sum(-t.amount for t in transactions if t.amount < 0)
    net = income - expenses

    months = sorted({month_key(t.date) for t in transactions})
    if transactions:
        span_days = (max(t.date for t in transactions) - min(t.date for t in transactions)).days + 1
    else:
        span_days = 0
    avg_daily_spend = expenses / span_days if span_days > 0 else 0.0

    return {
        "total_income": round(income, 2),
        "total_expenses": round(expenses, 2),
        "net": round(net, 2),
        "transaction_count": len(transactions),
        "months_covered": len(months),
        "avg_daily_spend": round(avg_daily_spend, 2),
    }


def compute_monthly_breakdown(transactions: list) -> list:
    by_month = defaultdict(lambda: {"income": 0.0, "expenses": 0.0})
    for txn in transactions:
        key = month_key(txn.date)
        if txn.amount > 0:
            by_month[key]["income"] += txn.amount
        else:
            by_month[key]["expenses"] += -txn.amount

    return [
        {
            "month": month,
            "income": round(data["income"], 2),
            "expenses": round(data["expenses"], 2),
            "net": round(data["income"] - data["expenses"], 2),
        }
        for month, data in sorted(by_month.items())
    ]


def compute_category_breakdown(transactions: list) -> list:
    totals = defaultdict(float)
    counts = defaultdict(int)
    for txn in transactions:
        if txn.amount < 0:
            totals[txn.category] += -txn.amount
            counts[txn.category] += 1

    total_expenses = sum(totals.values())
    breakdown = []
    for category, total in totals.items():
        pct = (total / total_expenses * 100) if total_expenses > 0 else 0.0
        breakdown.append({
            "category": category,
            "total": round(total, 2),
            "count": counts[category],
            "pct_of_expenses": round(pct, 1),
        })
    return sorted(breakdown, key=lambda r: r["total"], reverse=True)


def compute_top_merchants(transactions: list, limit: int = 10) -> list:
    totals = defaultdict(float)
    counts = defaultdict(int)
    display_name = {}
    for txn in transactions:
        if txn.amount >= 0:
            continue
        key = normalize_merchant(txn.description)
        totals[key] += -txn.amount
        counts[key] += 1
        display_name.setdefault(key, txn.description.strip())

    merchants = [
        {"merchant": display_name[key], "total": round(total, 2), "count": counts[key]}
        for key, total in totals.items()
    ]
    return sorted(merchants, key=lambda r: r["total"], reverse=True)[:limit]


def detect_recurring(transactions: list) -> list:
    """Flag transactions that repeat (same normalized merchant, similar amount)
    across at least RECURRING_MIN_MONTHS distinct months. Mutates txn.recurring
    in place and returns a summary list of the recurring charge groups.
    """
    groups = defaultdict(list)
    for txn in transactions:
        if txn.amount >= 0:
            continue
        groups[normalize_merchant(txn.description)].append(txn)

    recurring_summary = []
    for key, txns in groups.items():
        months_seen = {month_key(t.date) for t in txns}
        if len(months_seen) < RECURRING_MIN_MONTHS:
            continue

        # Within this merchant, cluster by similar amount (handles price changes
        # as separate clusters rather than false-negative-ing the whole merchant).
        clusters = []
        for txn in sorted(txns, key=lambda t: -t.amount):
            placed = False
            for cluster in clusters:
                ref_amount = cluster[0].amount
                if ref_amount == 0:
                    continue
                if abs(txn.amount - ref_amount) / abs(ref_amount) <= RECURRING_AMOUNT_TOLERANCE:
                    cluster.append(txn)
                    placed = True
                    break
            if not placed:
                clusters.append([txn])

        for cluster in clusters:
            cluster_months = {month_key(t.date) for t in cluster}
            if len(cluster_months) < RECURRING_MIN_MONTHS:
                continue
            for txn in cluster:
                txn.recurring = True
            avg_amount = sum(-t.amount for t in cluster) / len(cluster)
            recurring_summary.append({
                "merchant": cluster[0].description.strip(),
                "avg_amount": round(avg_amount, 2),
                "occurrences": len(cluster),
                "months_seen": len(cluster_months),
            })

    return sorted(recurring_summary, key=lambda r: r["avg_amount"], reverse=True)


def compare_budgets(category_breakdown: list, budgets: dict, months_covered: int) -> list:
    """Compare average monthly category spend against per-category monthly caps."""
    months = max(months_covered, 1)
    results = []
    for category, cap in budgets.items():
        matching = next((c for c in category_breakdown if c["category"] == category), None)
        actual_total = matching["total"] if matching else 0.0
        monthly_avg = actual_total / months
        results.append({
            "category": category,
            "monthly_cap": cap,
            "monthly_avg_actual": round(monthly_avg, 2),
            "over_budget": monthly_avg > cap,
            "pct_of_cap": round((monthly_avg / cap * 100), 1) if cap > 0 else 0.0,
        })
    return sorted(results, key=lambda r: r["pct_of_cap"], reverse=True)


def generate_fallback_insights(summary: dict, category_breakdown: list, monthly: list) -> str:
    """Deterministic template used when no ANTHROPIC_API_KEY is available."""
    if not category_breakdown:
        return "No expense transactions were found in this period."

    top = category_breakdown[0]
    parts = [
        f"Total spending was ${summary['total_expenses']:.2f} across "
        f"{summary['transaction_count']} transactions over {summary['months_covered']} "
        f"month(s), averaging ${summary['avg_daily_spend']:.2f} per day.",
        f"The largest category was {top['category']} at ${top['total']:.2f} "
        f"({top['pct_of_expenses']:.1f}% of total expenses).",
    ]

    if len(monthly) >= 2:
        prev, latest = monthly[-2], monthly[-1]
        delta = latest["expenses"] - prev["expenses"]
        direction = "up" if delta > 0 else "down"
        parts.append(
            f"Spending in {latest['month']} was {direction} "
            f"${abs(delta):.2f} compared to {prev['month']}."
        )

    return " ".join(parts)

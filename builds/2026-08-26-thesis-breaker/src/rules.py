"""Deterministic bear-case rule engine.

Each rule takes the fetched data dict (see src/fetch.py) plus the raw
thesis text and returns a RuleResult. `fired` is a three-state value:
  True  -> the risk condition is met
  False -> checked, and the risk condition is NOT met
  None  -> could not be evaluated (the underlying data field is unavailable)
`None` must never be coerced to False — an unavailable check is reported
to the user as unavailable, not as a clean bill of health.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Static, documented per-sector valuation "stretch" threshold on trailing P/E.
# Not a live-fetched sector average (see FutureFeatures.md) -- a conservative,
# hand-set reference so the check is deterministic and testable.
SECTOR_PE_THRESHOLDS = {
    "Technology": 35.0,
    "Healthcare": 30.0,
    "Financial Services": 18.0,
    "Financials": 18.0,
    "Energy": 15.0,
    "Consumer Cyclical": 25.0,
    "Consumer Defensive": 22.0,
    "Industrials": 22.0,
}
DEFAULT_PE_THRESHOLD = 25.0

# yfinance reports debtToEquity as a percentage-style number (154.2 == 1.54x).
DEBT_TO_EQUITY_RISK_THRESHOLD = 200.0

NARRATIVE_KEYWORDS = {
    "valuation": ["cheap", "reasonably valued", "undervalued", "fair value", "attractive valuation"],
    "growth": ["strong growth", "accelerating", "growing fast", "revenue growth", "expanding"],
    "margin": ["margin expansion", "improving margins", "profitability improving"],
    "debt": ["low debt", "strong balance sheet", "little debt", "healthy balance sheet"],
    "insider": ["insiders buying", "management confidence", "insider ownership"],
}


@dataclass
class RuleResult:
    key: str
    label: str
    fired: Optional[bool]
    detail: str


def valuation_stretch(data: dict) -> RuleResult:
    pe = data.get("trailing_pe")
    sector = data.get("sector")
    if pe is None:
        return RuleResult("valuation_stretch", "Valuation Stretch", None,
                           "Trailing P/E unavailable for this ticker; cannot evaluate valuation stretch.")
    threshold = SECTOR_PE_THRESHOLDS.get(sector, DEFAULT_PE_THRESHOLD)
    if pe > threshold:
        return RuleResult("valuation_stretch", "Valuation Stretch", True,
                           f"Trailing P/E of {pe:.1f} exceeds the {sector or 'default'} stretch threshold of {threshold:.1f}.")
    return RuleResult("valuation_stretch", "Valuation Stretch", False,
                       f"Trailing P/E of {pe:.1f} is within the {sector or 'default'} threshold of {threshold:.1f}.")


def growth_deceleration(data: dict) -> RuleResult:
    growth = data.get("quarterly_revenue_yoy_growth")
    if not growth or len(growth) < 2:
        return RuleResult("growth_deceleration", "Growth Deceleration", None,
                           "Fewer than 2 quarters of YoY revenue growth available; cannot evaluate deceleration.")
    # growth is most-recent-first; strictly monotonic deceleration means
    # each quarter's growth is lower than the one before it, oldest to newest.
    chronological = list(reversed(growth))
    decelerating = all(chronological[i] < chronological[i - 1] for i in range(1, len(chronological)))
    pct = [f"{g * 100:.0f}%" for g in growth]
    if decelerating:
        return RuleResult("growth_deceleration", "Growth Deceleration", True,
                           f"Revenue YoY growth has decelerated every quarter: {' -> '.join(reversed(pct))} (oldest to newest).")
    return RuleResult("growth_deceleration", "Growth Deceleration", False,
                       f"Revenue YoY growth has not decelerated in every quarter: {' -> '.join(reversed(pct))} (oldest to newest).")


def margin_debt_risk(data: dict) -> RuleResult:
    debt_to_equity = data.get("debt_to_equity")
    margins = data.get("quarterly_operating_margin")

    debt_flag = None if debt_to_equity is None else debt_to_equity > DEBT_TO_EQUITY_RISK_THRESHOLD
    margin_flag = None
    if margins and len(margins) >= 3:
        chronological = list(reversed(margins[:3]))
        margin_flag = chronological[2] < chronological[1] < chronological[0]

    if debt_flag is None and margin_flag is None:
        return RuleResult("margin_debt_risk", "Margin / Debt Risk", None,
                           "Neither debt-to-equity nor a 3-quarter margin trend is available; cannot evaluate.")

    fired = bool(debt_flag) or bool(margin_flag)
    parts = []
    if debt_to_equity is not None:
        parts.append(f"debt/equity of {debt_to_equity:.0f} ({'above' if debt_flag else 'at or below'} the {DEBT_TO_EQUITY_RISK_THRESHOLD:.0f} risk threshold)")
    if margin_flag is not None:
        parts.append("operating margin declined for 2 consecutive quarters" if margin_flag
                      else "operating margin did not decline for 2 consecutive quarters")
    return RuleResult("margin_debt_risk", "Margin / Debt Risk", fired, "; ".join(parts).capitalize() + ".")


def insider_selling(data: dict) -> RuleResult:
    transactions = data.get("insider_transactions")
    if not transactions:
        return RuleResult("insider_selling", "Insider Selling Signal", None,
                           "No insider transaction data available; cannot evaluate.")
    sell_value = sum(t["value"] or 0 for t in transactions if "sale" in t["transaction"].lower() or "sell" in t["transaction"].lower())
    buy_value = sum(t["value"] or 0 for t in transactions if "purchase" in t["transaction"].lower() or "buy" in t["transaction"].lower())
    fired = sell_value > buy_value
    return RuleResult("insider_selling", "Insider Selling Signal", fired,
                       f"Reported insider sell value (${sell_value:,.0f}) {'exceeds' if fired else 'does not exceed'} buy value (${buy_value:,.0f}).")


# Which prior rule's `fired=True` contradicts a bullish claim in that category.
_CONTRADICTING_RULE = {
    "valuation": "valuation_stretch",
    "growth": "growth_deceleration",
    "margin": "margin_debt_risk",
    "debt": "margin_debt_risk",
    "insider": "insider_selling",
}


def narrative_fragility(data: dict, thesis_text: str, prior_results: Optional[list[RuleResult]] = None) -> RuleResult:
    text = thesis_text.lower()
    matched_categories = [cat for cat, words in NARRATIVE_KEYWORDS.items() if any(w in text for w in words)]
    if not matched_categories:
        return RuleResult("narrative_fragility", "Narrative Fragility", False,
                           "No soft/unverifiable claim keywords detected in the thesis text.")

    field_by_category = {
        "valuation": data.get("trailing_pe"),
        "growth": data.get("quarterly_revenue_yoy_growth"),
        "margin": data.get("quarterly_operating_margin"),
        "debt": data.get("debt_to_equity"),
        "insider": data.get("insider_transactions"),
    }
    by_key = {r.key: r for r in (prior_results or [])}

    unverifiable = [cat for cat in matched_categories if field_by_category.get(cat) is None]
    contradicted = [
        cat for cat in matched_categories
        if by_key.get(_CONTRADICTING_RULE.get(cat, "")) is not None
        and by_key[_CONTRADICTING_RULE[cat]].fired is True
    ]

    if contradicted:
        return RuleResult("narrative_fragility", "Narrative Fragility", True,
                           f"Thesis makes a bullish claim in {', '.join(contradicted)} that the fetched data directly contradicts.")
    if unverifiable:
        return RuleResult("narrative_fragility", "Narrative Fragility", True,
                           f"Thesis makes claims in {', '.join(unverifiable)} with no corresponding fetched data to verify them against.")
    return RuleResult("narrative_fragility", "Narrative Fragility", False,
                       f"Thesis claims in {', '.join(matched_categories)} all have corresponding fetched data available and none are contradicted.")


ALL_RULES = [valuation_stretch, growth_deceleration, margin_debt_risk, insider_selling]


def run_all_rules(data: dict, thesis_text: str) -> list[RuleResult]:
    results = [rule(data) for rule in ALL_RULES]
    results.append(narrative_fragility(data, thesis_text, prior_results=results))
    return results

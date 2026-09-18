"""Deterministic rule engine for Tri-Agency (NSERC/CIHR/SSHRC) budget
expenditure eligibility, grounded in the Tri-Agency Guide on Financial
Administration (TAGFA) principles-based framework.

This is a decision-support heuristic against the *general* public guide.
It is not legal or financial advice and does not replace the
administering institution's research grants/financial office. It never
declares a line item definitively "eligible" -- only that no known
blocking rule fired, subject to the three general principles below.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

STATUS_OUTSIDE_PERIOD = "outside_grant_period"
STATUS_INELIGIBLE = "ineligible"
STATUS_REQUIRES_JUSTIFICATION = "requires_justification"
STATUS_NO_BLOCKING_RULE = "no_blocking_rule_found"

# The three general TAGFA principles, verified via web search against
# NSERC's own FAQ summary and multiple institutional research-office
# quick-reference pages (Waterloo, Queen's, Acadia, Guelph, UCalgary,
# Carleton), since the build container's egress proxy blocks a direct
# fetch of the primary nserc-crsng.gc.ca guide text.
PRINCIPLE_DIRECT_COST = (
    "Principle: direct cost & attribution -- the expenditure must "
    "contribute to the direct costs of the funded research, with "
    "benefits directly attributable to the grant."
)
PRINCIPLE_NOT_INSTITUTION_PROVIDED = (
    "Principle: not normally institution-provided -- grant funds must "
    "not be used for a good or service the administering institution "
    "normally provides to its research personnel (this is what "
    "institutional overhead / the Research Support Fund is for)."
)
PRINCIPLE_ECONOMICAL = (
    "Principle: effective and economical -- the expenditure must "
    "achieve the intended research outcome with due regard for "
    "minimizing cost."
)


@dataclass(frozen=True)
class LineItem:
    item: str
    category: str
    amount: float
    item_date: date
    justification: str = ""

    @property
    def haystack(self) -> str:
        return f"{self.item} {self.category} {self.justification}".lower()


@dataclass(frozen=True)
class Verdict:
    line: LineItem
    status: str
    reason: str
    principle: str


@dataclass(frozen=True)
class _KeywordRule:
    name: str
    patterns: tuple[str, ...]
    status: str
    reason: str
    principle: str
    conditional: bool = False
    clears_if: str = ""  # substring that, if present in justification, clears a conditional rule

    def matches(self, line: LineItem) -> bool:
        return any(re.search(p, line.haystack) for p in self.patterns)


# Always-ineligible rules, each keyed to a specific TAGFA directive or
# explicitly named ineligible item found in institutional summaries of
# the current guide.
_ALWAYS_INELIGIBLE_RULES: tuple[_KeywordRule, ...] = (
    _KeywordRule(
        name="alcohol",
        patterns=(r"\balcohol\b", r"\bwine\b", r"\bbeer\b", r"\bliquor\b", r"\bbar tab\b"),
        status=STATUS_INELIGIBLE,
        reason="Alcoholic beverages are explicitly ineligible under TAGFA, regardless of context.",
        principle=PRINCIPLE_ECONOMICAL,
    ),
    _KeywordRule(
        name="tuition",
        patterns=(r"\btuition\b", r"\bthesis fee\b", r"\bthesis-related\b"),
        status=STATUS_INELIGIBLE,
        reason="Tuition and thesis-related education costs are explicitly ineligible under TAGFA.",
        principle=PRINCIPLE_DIRECT_COST,
    ),
    _KeywordRule(
        name="institution_overhead",
        patterns=(
            r"\boverhead\b",
            r"\bgeneral it\b",
            r"\bnetwork infrastructure\b",
            r"\bbasic (telecom|phone|internet)\b",
            r"\boffice rent\b",
            r"\butilities\b",
            r"\bgeneral (clerical|admin(istrative)?) support\b",
        ),
        status=STATUS_INELIGIBLE,
        reason=(
            "Costs the administering institution normally provides "
            "(space, utilities, general IT/telecom infrastructure, "
            "general clerical/admin support) are covered by "
            "institutional overhead, not chargeable directly to the grant."
        ),
        principle=PRINCIPLE_NOT_INSTITUTION_PROVIDED,
    ),
    _KeywordRule(
        name="passport_immigration",
        patterns=(r"\bpassport\b", r"\bimmigration fee\b", r"\bvisa renewal\b(?! for research)"),
        status=STATUS_INELIGIBLE,
        reason="Passport and immigration fees are explicitly ineligible under TAGFA (note: research-purpose entry visas ARE eligible -- this rule targets passport/immigration fees specifically).",
        principle=PRINCIPLE_DIRECT_COST,
    ),
    _KeywordRule(
        name="international_drivers_licence",
        patterns=(r"\binternational driver'?s licen[cs]e\b",),
        status=STATUS_INELIGIBLE,
        reason="International driver's licences are explicitly ineligible under TAGFA.",
        principle=PRINCIPLE_DIRECT_COST,
    ),
    _KeywordRule(
        name="commuting",
        patterns=(r"\bcommut(e|ing)\b", r"\bhome to (office|lab|work)\b"),
        status=STATUS_INELIGIBLE,
        reason="Commuting costs between home and place of employment are explicitly ineligible under TAGFA.",
        principle=PRINCIPLE_DIRECT_COST,
    ),
    _KeywordRule(
        name="frequent_flyer_airfare",
        patterns=(r"\bfrequent flyer\b", r"\bpoints[- ]booked airfare\b", r"\bairfare.*points\b"),
        status=STATUS_INELIGIBLE,
        reason="Airfare reimbursement for tickets purchased with frequent-flyer points is explicitly ineligible under TAGFA.",
        principle=PRINCIPLE_ECONOMICAL,
    ),
    _KeywordRule(
        name="sabbatical_living",
        patterns=(r"\bsabbatical\b",),
        status=STATUS_INELIGIBLE,
        reason="Living expenses during sabbatical leave are explicitly ineligible under TAGFA.",
        principle=PRINCIPLE_DIRECT_COST,
    ),
)

_HOSPITALITY_RULE = _KeywordRule(
    name="hospitality",
    patterns=(r"\bhospitality\b", r"\brefreshments\b", r"\bcatering\b", r"\blunch\b", r"\bparty\b"),
    status=STATUS_REQUIRES_JUSTIFICATION,
    reason=(
        "Hospitality (non-alcoholic meals/refreshments) is only eligible "
        "when directly related to a funded research activity or "
        "gathering -- add a justification tying it to a specific "
        "research assembly to clear this flag."
    ),
    principle=PRINCIPLE_DIRECT_COST,
    conditional=True,
)

_RESEARCH_GATHERING_MARKERS = (
    "research meeting",
    "research gathering",
    "lab meeting",
    "workshop",
    "conference",
    "seminar",
    "symposium",
    "data collection",
    "participant",
    "research team",
    "grant-funded",
    "funded research",
    "project meeting",
)


def _has_research_gathering_justification(line: LineItem) -> bool:
    just = line.justification.lower()
    return any(marker in just for marker in _RESEARCH_GATHERING_MARKERS)


def evaluate(line: LineItem, grant_start: date, grant_end: date) -> Verdict:
    """Evaluate a single line item against the Tri-Agency rule set.

    Evaluation order (first match wins, matching PRD's stated order):
    1. Date-range check (short-circuits everything else)
    2. Always-ineligible keyword rules
    3. Conditional (hospitality) rule
    4. Default: no blocking rule found
    """
    if line.item_date < grant_start or line.item_date > grant_end:
        return Verdict(
            line=line,
            status=STATUS_OUTSIDE_PERIOD,
            reason=(
                f"Dated {line.item_date.isoformat()}, outside the eligible "
                f"grant period {grant_start.isoformat()} to {grant_end.isoformat()}."
            ),
            principle=PRINCIPLE_DIRECT_COST,
        )

    for rule in _ALWAYS_INELIGIBLE_RULES:
        if rule.matches(line):
            return Verdict(line=line, status=rule.status, reason=rule.reason, principle=rule.principle)

    if _HOSPITALITY_RULE.matches(line):
        if _has_research_gathering_justification(line):
            return Verdict(
                line=line,
                status=STATUS_NO_BLOCKING_RULE,
                reason=(
                    "Hospitality justification ties this expense to a "
                    "research-related gathering, clearing the "
                    "conditional flag. Still subject to the general "
                    "principles below."
                ),
                principle=PRINCIPLE_DIRECT_COST,
            )
        return Verdict(
            line=line,
            status=_HOSPITALITY_RULE.status,
            reason=_HOSPITALITY_RULE.reason,
            principle=_HOSPITALITY_RULE.principle,
        )

    if not line.justification.strip():
        return Verdict(
            line=line,
            status=STATUS_REQUIRES_JUSTIFICATION,
            reason=(
                "No justification text linking this line item to the "
                "funded research. Add one so it can be checked against "
                "the direct-cost principle."
            ),
            principle=PRINCIPLE_DIRECT_COST,
        )

    return Verdict(
        line=line,
        status=STATUS_NO_BLOCKING_RULE,
        reason=(
            "No specific TAGFA blocking rule matched this line item. "
            "This is not a guarantee of eligibility -- it still must "
            "satisfy the three general principles."
        ),
        principle=PRINCIPLE_DIRECT_COST,
    )


def evaluate_all(lines: list[LineItem], grant_start: date, grant_end: date) -> list[Verdict]:
    return [evaluate(line, grant_start, grant_end) for line in lines]

import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from rules import (  # noqa: E402
    STATUS_INELIGIBLE,
    STATUS_NO_BLOCKING_RULE,
    STATUS_OUTSIDE_PERIOD,
    STATUS_REQUIRES_JUSTIFICATION,
    LineItem,
    evaluate,
)

GRANT_START = date(2026, 4, 1)
GRANT_END = date(2027, 3, 31)


def _line(item="Item", category="Category", amount=100.0, item_date=date(2026, 5, 1), justification=""):
    return LineItem(item=item, category=category, amount=amount, item_date=item_date, justification=justification)


def test_date_before_grant_start_is_outside_period():
    line = _line(item_date=date(2026, 3, 15), justification="fine otherwise")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_OUTSIDE_PERIOD


def test_date_after_grant_end_is_outside_period():
    line = _line(item_date=date(2027, 4, 5), justification="fine otherwise")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_OUTSIDE_PERIOD


def test_date_on_start_boundary_is_inside_period():
    line = _line(item_date=GRANT_START, justification="boundary check")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status != STATUS_OUTSIDE_PERIOD


def test_date_on_end_boundary_is_inside_period():
    line = _line(item_date=GRANT_END, justification="boundary check")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status != STATUS_OUTSIDE_PERIOD


def test_alcohol_rule_fires():
    line = _line(item="Lab party wine", category="Hospitality")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_INELIGIBLE
    assert "alcohol" in verdict.reason.lower()


def test_alcohol_rule_does_not_fire_on_unrelated_item():
    line = _line(item="Graduate student stipend", category="Personnel", justification="RA salary")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert "alcohol" not in verdict.reason.lower()


def test_tuition_rule_fires():
    line = _line(item="Tuition reimbursement", category="Personnel")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_INELIGIBLE
    assert "tuition" in verdict.reason.lower()


def test_tuition_rule_does_not_fire_on_unrelated_item():
    line = _line(item="Equipment purchase", category="Equipment", justification="oscilloscope for aim 1")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert "tuition" not in verdict.reason.lower()


def test_institution_overhead_rule_fires():
    line = _line(item="General office internet service", category="Overhead")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_INELIGIBLE
    assert "institution" in verdict.reason.lower()


def test_institution_overhead_rule_does_not_fire_on_unrelated_item():
    line = _line(item="Field recording equipment", category="Equipment", justification="for data collection")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert "institution normally provides" not in verdict.reason.lower()


def test_passport_rule_fires():
    line = _line(item="Passport renewal for fieldwork", category="Travel")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_INELIGIBLE
    assert "passport" in verdict.reason.lower()


def test_international_drivers_licence_rule_fires():
    line = _line(item="International driver's licence", category="Travel")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_INELIGIBLE
    assert "driver" in verdict.reason.lower()


def test_commuting_rule_fires():
    line = _line(item="Commute mileage reimbursement", category="Travel", justification="daily commute between home and lab")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_INELIGIBLE
    assert "commut" in verdict.reason.lower()


def test_commuting_rule_does_not_fire_on_fieldwork_travel():
    line = _line(item="Flight to field site", category="Travel", justification="travel to remote data collection site")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert "commut" not in verdict.reason.lower()


def test_frequent_flyer_rule_fires():
    line = _line(item="Flight booked with frequent flyer points", category="Travel", justification="reimbursement claimed")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_INELIGIBLE
    assert "frequent" in verdict.reason.lower() or "points" in verdict.reason.lower()


def test_sabbatical_rule_fires():
    line = _line(item="Sabbatical housing costs", category="Personal")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_INELIGIBLE
    assert "sabbatical" in verdict.reason.lower()


def test_hospitality_flagged_without_justification():
    line = _line(item="Office party catering", category="Hospitality", justification="")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_REQUIRES_JUSTIFICATION
    assert "hospitality" in verdict.reason.lower()


def test_hospitality_cleared_with_research_gathering_justification():
    line = _line(
        item="Team lunch after data collection wrap-up",
        category="Hospitality",
        justification="research team lunch after final data collection session",
    )
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_NO_BLOCKING_RULE


def test_alcohol_rule_takes_precedence_over_hospitality():
    line = _line(item="Lab holiday party wine", category="Hospitality", justification="")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_INELIGIBLE
    assert "alcohol" in verdict.reason.lower()


def test_unmatched_category_with_justification_is_no_blocking_rule():
    line = _line(item="Conference registration", category="Dissemination", justification="Presenting grant-funded findings")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_NO_BLOCKING_RULE


def test_unmatched_category_without_justification_requires_justification():
    line = _line(item="Equipment - oscilloscope", category="Equipment", justification="")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_REQUIRES_JUSTIFICATION


def test_no_blocking_rule_is_never_labeled_as_guaranteed_eligible():
    line = _line(item="Equipment - laptop", category="Equipment", justification="fMRI data analysis pipeline")
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_NO_BLOCKING_RULE
    assert "not a guarantee" in verdict.reason.lower()


def test_period_check_short_circuits_before_ineligible_category_rule():
    # Item would match the alcohol rule, but its date is outside the
    # grant period -- the period check must fire first per the PRD's
    # documented evaluation order.
    line = _line(item="Wine for lab party", category="Hospitality", item_date=date(2026, 1, 1))
    verdict = evaluate(line, GRANT_START, GRANT_END)
    assert verdict.status == STATUS_OUTSIDE_PERIOD

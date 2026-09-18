import csv
import io
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from report import render_html, render_terminal, totals_by_status, write_flagged_csv  # noqa: E402
from rules import (  # noqa: E402
    STATUS_INELIGIBLE,
    STATUS_NO_BLOCKING_RULE,
    STATUS_OUTSIDE_PERIOD,
    STATUS_REQUIRES_JUSTIFICATION,
    LineItem,
    Verdict,
)

GRANT_START = date(2026, 4, 1)
GRANT_END = date(2027, 3, 31)


def _verdicts():
    return [
        Verdict(
            line=LineItem(item="Stipend", category="Personnel", amount=1000.0, item_date=date(2026, 5, 1), justification="RA salary"),
            status=STATUS_NO_BLOCKING_RULE,
            reason="No blocking rule found.",
            principle="p1",
        ),
        Verdict(
            line=LineItem(item="Wine", category="Hospitality", amount=100.0, item_date=date(2026, 6, 1), justification=""),
            status=STATUS_INELIGIBLE,
            reason="Alcohol is ineligible.",
            principle="p2",
        ),
        Verdict(
            line=LineItem(item="Catering", category="Hospitality", amount=200.0, item_date=date(2026, 7, 1), justification=""),
            status=STATUS_REQUIRES_JUSTIFICATION,
            reason="Needs justification.",
            principle="p3",
        ),
        Verdict(
            line=LineItem(item="Late item", category="Travel", amount=50.0, item_date=date(2027, 5, 1), justification=""),
            status=STATUS_OUTSIDE_PERIOD,
            reason="Outside period.",
            principle="p4",
        ),
    ]


def test_totals_by_status_matches_hand_computed_expectation():
    totals = totals_by_status(_verdicts())
    assert totals[STATUS_NO_BLOCKING_RULE] == 1000.0
    assert totals[STATUS_INELIGIBLE] == 100.0
    assert totals[STATUS_REQUIRES_JUSTIFICATION] == 200.0
    assert totals[STATUS_OUTSIDE_PERIOD] == 50.0


def test_terminal_report_includes_total_and_disclaimer():
    text = render_terminal(_verdicts(), GRANT_START, GRANT_END)
    assert "$1,350.00" in text  # total of 1000+100+200+50
    assert "not legal or financial advice" in text.lower()


def test_write_flagged_csv_contains_only_flagged_rows():
    verdicts = _verdicts()
    out_path = "/tmp/eligible_spend_test_flagged.csv"
    count = write_flagged_csv(verdicts, out_path)
    assert count == 3  # ineligible, requires_justification, outside_period -- not the clean one
    with open(out_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 3
    items = {row["item"] for row in rows}
    assert "Stipend" not in items
    assert "Wine" in items
    os.remove(out_path)


def test_html_report_renders_without_error_and_contains_expected_totals():
    html_out = render_html(_verdicts(), GRANT_START, GRANT_END)
    assert "<!DOCTYPE html>" in html_out
    assert "$1,350.00" in html_out


def test_html_report_escapes_hostile_payload_in_item_and_justification():
    hostile = Verdict(
        line=LineItem(
            item='<img src=x onerror="window.__xss=true">',
            category="Hospitality",
            amount=50.0,
            item_date=date(2026, 6, 1),
            justification='</script><script>window.__xss2=true;</script>',
        ),
        status=STATUS_REQUIRES_JUSTIFICATION,
        reason="Needs justification.",
        principle="p",
    )
    html_out = render_html([hostile], GRANT_START, GRANT_END)
    # The payload is only safe if it stays inside the JSON data block (where
    # it is inert text, hydrated via textContent in JS) and never opens a
    # real extra <script> element by way of an un-neutralized "</script>".
    row_data_block = html_out.split('id="row-data">')[1].split("</script>")[0]
    assert "<img src=x onerror=" in row_data_block  # present as inert JSON text, never live HTML
    assert "<\\/script><script>window.__xss2" in html_out  # neutralized, not a real tag boundary
    # Exactly the page's own two real closing </script> tags should remain --
    # the payload's own "</script>" occurrences must all have been neutralized,
    # otherwise the payload would prematurely close the JSON <script> block and
    # open a real, executable <script> element.
    assert html_out.count("</script>") == 2


def test_html_report_includes_ai_notes_when_provided():
    verdicts = _verdicts()
    ai_notes = {2: "This plausibly satisfies the direct-cost principle."}
    html_out = render_html(verdicts, GRANT_START, GRANT_END, ai_notes)
    assert "This plausibly satisfies the direct-cost principle." in html_out


def test_html_report_omits_ai_notes_when_none_provided():
    html_out = render_html(_verdicts(), GRANT_START, GRANT_END, {})
    assert '"ai_note": null' in html_out.replace(" ", "") or '"ai_note":null' in html_out.replace(" ", "")

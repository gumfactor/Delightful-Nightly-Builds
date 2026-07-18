from datetime import date, datetime, timezone

from src.deltas import DeltaSummary, PeriodDelta
from src.html_report import IndicatorSnapshot, render_dashboard
from src.indicators import Indicator


def make_indicator(label="USD/CAD Exchange Rate", series_id="FXUSDCAD"):
    return Indicator(
        series_id=series_id,
        label=label,
        unit="CAD per USD",
        source="Bank of Canada Valet",
        fetch=lambda recent: [],
    )


def make_summary():
    month = PeriodDelta(compare_date=date(2026, 6, 1), compare_value=1.30, change=0.02, pct_change=1.54)
    return DeltaSummary(latest_date=date(2026, 7, 1), latest_value=1.32, day=None, week=None, month=month)


def test_indicator_label_is_escaped_in_visible_heading():
    dangerous_label = "R&D </script><img src=x onerror=alert(1)>"
    snapshot = IndicatorSnapshot(
        indicator=make_indicator(label=dangerous_label),
        history=[(date(2026, 6, 1), 1.30), (date(2026, 7, 1), 1.32)],
        deltas=make_summary(),
        last_fetched_at="2026-07-18T08:00:00+00:00",
    )
    html_doc = render_dashboard([snapshot], "briefing", "template", datetime.now(timezone.utc))

    # The panel heading is rendered as literal HTML text, so it must be
    # escaped there regardless of what the JS-only chart payload contains
    # (a JS string literal is never parsed as HTML/DOM by the browser).
    heading_start = html_doc.index("<h2>")
    heading_end = html_doc.index("</h2>")
    heading_html = html_doc[heading_start:heading_end]
    assert "<img src=x onerror=alert(1)>" not in heading_html
    assert "&lt;img src=x onerror=alert(1)&gt;" in heading_html


def test_empty_state_shown_for_indicator_with_no_history():
    snapshot = IndicatorSnapshot(
        indicator=make_indicator(),
        history=[],
        deltas=None,
        last_fetched_at=None,
    )
    html_doc = render_dashboard([snapshot], "briefing", "template", datetime.now(timezone.utc))

    assert "No data yet" in html_doc


def test_script_tag_breakout_is_neutralized_in_embedded_json():
    dangerous_label = "</script><script>alert(1)</script>"
    snapshot = IndicatorSnapshot(
        indicator=make_indicator(label=dangerous_label),
        history=[(date(2026, 6, 1), 1.30), (date(2026, 7, 1), 1.32)],
        deltas=make_summary(),
        last_fetched_at="2026-07-18T08:00:00+00:00",
    )
    html_doc = render_dashboard([snapshot], "briefing", "template", datetime.now(timezone.utc))

    # Only the two legitimate <script> tags this template always emits
    # (Chart.js CDN load + inline renderer) should appear as real tags.
    assert html_doc.count("<script>alert(1)</script>") == 0


def test_briefing_text_is_escaped():
    snapshot = IndicatorSnapshot(
        indicator=make_indicator(),
        history=[(date(2026, 7, 1), 1.32)],
        deltas=None,
        last_fetched_at=None,
    )
    html_doc = render_dashboard(
        [snapshot], "<b>bold claim</b>", "ai", datetime.now(timezone.utc)
    )

    assert "<b>bold claim</b>" not in html_doc
    assert "&lt;b&gt;bold claim&lt;/b&gt;" in html_doc


def test_delta_badges_rendered_for_available_and_unavailable_periods():
    snapshot = IndicatorSnapshot(
        indicator=make_indicator(),
        history=[(date(2026, 6, 1), 1.30), (date(2026, 7, 1), 1.32)],
        deltas=make_summary(),
        last_fetched_at="2026-07-18T08:00:00+00:00",
    )
    html_doc = render_dashboard([snapshot], "briefing", "template", datetime.now(timezone.utc))

    assert "day: n/a" in html_doc
    assert "week: n/a" in html_doc
    assert "month:" in html_doc
    assert "1.54%" in html_doc

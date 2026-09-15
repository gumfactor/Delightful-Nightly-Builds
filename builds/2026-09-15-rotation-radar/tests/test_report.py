from src import report
from src.analytics import SectorPoint, SectorResult
from src.storage import QuadrantTransition


def _result(ticker, ratio, momentum, quadrant, tail_dates=("2026-01-01", "2026-01-02")):
    points = [
        SectorPoint(date=d, rs_ratio=ratio, rs_momentum=momentum, quadrant=quadrant)
        for d in tail_dates
    ]
    return SectorResult(ticker=ticker, tail=points, latest=points[-1], previous=points[0])


def test_build_html_contains_required_sections():
    snapshots = {"XLK": _result("XLK", 105.0, 102.0, "Leading")}
    transitions = [QuadrantTransition(ticker="XLK", previous_quadrant="Improving", current_quadrant="Leading", changed=True)]
    html_text = report.build_html(snapshots, transitions, "Tech is leading.", "SPY", "2026-01-02 00:00:00 UTC", 10)

    assert "<title>Rotation Radar</title>" in html_text
    assert "rrg-chart" in html_text
    assert "sector-table" in html_text
    assert "XLK" in html_text
    assert "csv-link" in html_text


def test_build_html_escapes_hostile_ticker_like_string():
    hostile = "<img src=x onerror=alert(1)>"
    snapshots = {hostile: _result(hostile, 105.0, 102.0, "Leading")}
    transitions = [QuadrantTransition(ticker=hostile, previous_quadrant="Improving", current_quadrant="Leading", changed=True)]
    html_text = report.build_html(snapshots, transitions, "commentary", "SPY", "2026-01-02", 10)

    assert "<img src=x onerror=alert(1)>" not in html_text
    assert "&lt;img" in html_text


def test_build_html_escapes_hostile_commentary_and_neutralizes_script_breakout():
    hostile_commentary = "</script><script>window.__xss=true;</script>"
    snapshots = {"XLK": _result("XLK", 100.0, 100.0, "Leading")}
    transitions = []
    html_text = report.build_html(snapshots, transitions, hostile_commentary, "SPY", "2026-01-02", 10)

    assert "</script><script>window.__xss" not in html_text
    assert "<\\/script><script>window.__xss" in html_text


def test_build_html_neutralizes_script_breakout_in_json_data_block():
    hostile_ticker = "</script><script>window.__xss2=true;</script>"
    snapshots = {hostile_ticker: _result(hostile_ticker, 100.0, 100.0, "Leading")}
    html_text = report.build_html(snapshots, [], "commentary", "SPY", "2026-01-02", 10)
    assert "</script><script>window.__xss2" not in html_text


def test_build_html_shows_no_change_badge_when_unchanged():
    snapshots = {"XLK": _result("XLK", 100.0, 100.0, "Leading")}
    transitions = [QuadrantTransition(ticker="XLK", previous_quadrant="Leading", current_quadrant="Leading", changed=False)]
    html_text = report.build_html(snapshots, transitions, "commentary", "SPY", "2026-01-02", 10)
    assert "badge changed" not in html_text


def test_build_html_shows_change_badge_when_changed():
    snapshots = {"XLK": _result("XLK", 100.0, 100.0, "Leading")}
    transitions = [QuadrantTransition(ticker="XLK", previous_quadrant="Weakening", current_quadrant="Leading", changed=True)]
    html_text = report.build_html(snapshots, transitions, "commentary", "SPY", "2026-01-02", 10)
    assert "badge changed" in html_text
    assert "Weakening" in html_text


def test_build_csv_header_and_rows():
    rows = [("XLK", "2026-01-01 00:00:00 UTC", 101.0, 99.0, "Weakening")]
    csv_text = report.build_csv(rows)
    lines = csv_text.strip().splitlines()
    assert lines[0] == "ticker,run_timestamp,rs_ratio,rs_momentum,quadrant"
    assert lines[1] == "XLK,2026-01-01 00:00:00 UTC,101.0,99.0,Weakening"


def test_build_csv_empty_rows_still_has_header():
    csv_text = report.build_csv([])
    assert csv_text.strip() == "ticker,run_timestamp,rs_ratio,rs_momentum,quadrant"

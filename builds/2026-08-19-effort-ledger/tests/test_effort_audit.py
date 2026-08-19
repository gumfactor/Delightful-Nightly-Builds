from datetime import date

from src.effort_audit import audit_effort
from src.models import AuditConfig, EffortLine


def make_line(person_name="A. Reyes", grant_id="G1", grant_name="Grant One",
              start="2026-01-01", end="2026-12-31", percent=50.0, row_number=2):
    return EffortLine(
        person_name, grant_id, grant_name,
        date.fromisoformat(start), date.fromisoformat(end), percent, row_number,
    )


def test_two_overlapping_grants_above_cap_flagged_with_correct_window():
    lines = [
        make_line(grant_id="G1", grant_name="Grant One", start="2026-01-01", end="2026-12-31", percent=60, row_number=2),
        make_line(grant_id="G2", grant_name="Grant Two", start="2026-01-01", end="2026-12-31", percent=60, row_number=3),
    ]
    config = AuditConfig(far_rate=0.5, effort_cap_percent=100)
    flags, windows = audit_effort(lines, {"G1", "G2"}, config)
    assert len(windows) == 1
    w = windows[0]
    assert w.start == date(2026, 1, 1)
    assert w.end == date(2026, 12, 31)
    assert w.peak_percent == 120
    assert w.grant_ids == ("G1", "G2")
    assert any(f.code == "overcommitment" for f in flags)


def test_exactly_at_cap_not_flagged():
    lines = [
        make_line(grant_id="G1", start="2026-01-01", end="2026-12-31", percent=50, row_number=2),
        make_line(grant_id="G2", start="2026-01-01", end="2026-12-31", percent=50, row_number=3),
    ]
    config = AuditConfig(far_rate=0.5, effort_cap_percent=100)
    flags, windows = audit_effort(lines, {"G1", "G2"}, config)
    assert windows == []
    assert not any(f.code == "overcommitment" for f in flags)


def test_touching_but_not_overlapping_periods_not_flagged():
    lines = [
        make_line(grant_id="G1", start="2026-01-01", end="2026-01-31", percent=60, row_number=2),
        make_line(grant_id="G2", start="2026-02-01", end="2026-02-28", percent=60, row_number=3),
    ]
    config = AuditConfig(far_rate=0.5, effort_cap_percent=100)
    flags, windows = audit_effort(lines, {"G1", "G2"}, config)
    assert windows == []


def test_partial_overlap_flags_only_the_overlapping_subwindow():
    lines = [
        make_line(grant_id="G1", start="2026-01-01", end="2026-01-31", percent=60, row_number=2),
        make_line(grant_id="G2", start="2026-01-15", end="2026-02-15", percent=60, row_number=3),
    ]
    config = AuditConfig(far_rate=0.5, effort_cap_percent=100)
    flags, windows = audit_effort(lines, {"G1", "G2"}, config)
    assert len(windows) == 1
    w = windows[0]
    assert w.start == date(2026, 1, 15)
    assert w.end == date(2026, 1, 31)
    assert w.peak_percent == 120
    assert w.grant_ids == ("G1", "G2")


def test_nested_period_flags_only_the_nested_window():
    lines = [
        make_line(grant_id="G1", start="2026-01-01", end="2026-12-31", percent=60, row_number=2),
        make_line(grant_id="G2", start="2026-03-01", end="2026-03-31", percent=50, row_number=3),
    ]
    config = AuditConfig(far_rate=0.5, effort_cap_percent=100)
    flags, windows = audit_effort(lines, {"G1", "G2"}, config)
    assert len(windows) == 1
    w = windows[0]
    assert w.start == date(2026, 3, 1)
    assert w.end == date(2026, 3, 31)
    assert w.peak_percent == 110


def test_single_line_over_100_percent_flagged_both_ways():
    lines = [make_line(grant_id="G1", start="2026-01-01", end="2026-01-31", percent=150, row_number=2)]
    config = AuditConfig(far_rate=0.5, effort_cap_percent=100)
    flags, windows = audit_effort(lines, {"G1"}, config)
    assert any(f.code == "effort_over_100_single_line" for f in flags)
    assert any(f.code == "overcommitment" for f in flags)
    assert len(windows) == 1
    assert windows[0].peak_percent == 150


def test_zero_or_negative_effort_flagged_and_excluded_from_overlap():
    lines = [make_line(grant_id="G1", percent=0, row_number=2)]
    config = AuditConfig(far_rate=0.5)
    flags, windows = audit_effort(lines, {"G1"}, config)
    assert any(f.code == "zero_or_negative_effort" for f in flags)
    assert windows == []


def test_invalid_period_flagged_and_excluded():
    lines = [make_line(grant_id="G1", start="2026-06-01", end="2026-01-01", percent=50, row_number=2)]
    config = AuditConfig(far_rate=0.5)
    flags, windows = audit_effort(lines, {"G1"}, config)
    assert any(f.code == "invalid_period" for f in flags)
    assert windows == []


def test_orphan_effort_grant_flagged_info():
    lines = [make_line(grant_id="G-UNKNOWN", percent=50, row_number=2)]
    config = AuditConfig(far_rate=0.5)
    flags, windows = audit_effort(lines, {"G1"}, config)
    orphan = [f for f in flags if f.code == "orphan_effort_grant"]
    assert len(orphan) == 1
    assert orphan[0].severity.value == "info"


def test_grant_name_mismatch_flagged():
    lines = [
        make_line(grant_id="G1", grant_name="Grant One", row_number=2),
        make_line(grant_id="G1", grant_name="Grant Uno", row_number=3),
    ]
    config = AuditConfig(far_rate=0.5)
    flags, windows = audit_effort(lines, {"G1"}, config)
    assert any(f.code == "grant_name_mismatch" for f in flags)


def test_independent_people_not_cross_contaminated():
    lines = [
        make_line(person_name="A. Reyes", grant_id="G1", percent=90, row_number=2),
        make_line(person_name="J. Okafor", grant_id="G2", percent=90, row_number=3),
    ]
    config = AuditConfig(far_rate=0.5, effort_cap_percent=100)
    flags, windows = audit_effort(lines, {"G1", "G2"}, config)
    assert windows == []

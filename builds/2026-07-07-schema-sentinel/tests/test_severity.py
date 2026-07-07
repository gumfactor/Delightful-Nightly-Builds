import diff as diff_mod


def make_entries(*severities):
    return [{"severity": s, "field": f"f{i}", "change": "x", "old": None, "new": None, "detail": ""} for i, s in enumerate(severities)]


def test_overall_severity_picks_highest():
    entries = make_entries("safe", "breaking", "risky")
    assert diff_mod.overall_severity(entries) == "breaking"


def test_overall_severity_risky_beats_safe():
    entries = make_entries("safe", "risky")
    assert diff_mod.overall_severity(entries) == "risky"


def test_overall_severity_none_for_empty_list():
    assert diff_mod.overall_severity([]) is None


def test_exceeds_threshold_breaking_true_when_breaking_present():
    entries = make_entries("safe", "breaking")
    assert diff_mod.exceeds_threshold(entries, "breaking") is True


def test_exceeds_threshold_breaking_false_when_only_risky():
    entries = make_entries("safe", "risky")
    assert diff_mod.exceeds_threshold(entries, "breaking") is False


def test_exceeds_threshold_risky_true_when_only_risky():
    entries = make_entries("safe", "risky")
    assert diff_mod.exceeds_threshold(entries, "risky") is True


def test_exceeds_threshold_false_for_empty_entries():
    assert diff_mod.exceeds_threshold([], "risky") is False

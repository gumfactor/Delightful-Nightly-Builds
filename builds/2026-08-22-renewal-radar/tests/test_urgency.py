from src.urgency import classify


def test_negative_days_is_overdue():
    assert classify(-1) == "Overdue"
    assert classify(-100) == "Overdue"


def test_zero_days_is_due_this_week():
    assert classify(0) == "Due This Week"


def test_boundary_seven_days_is_due_this_week():
    assert classify(7) == "Due This Week"


def test_boundary_eight_days_is_due_this_month():
    assert classify(8) == "Due This Month"


def test_boundary_thirty_days_is_due_this_month():
    assert classify(30) == "Due This Month"


def test_boundary_thirty_one_days_is_upcoming():
    assert classify(31) == "Upcoming"


def test_boundary_ninety_days_is_upcoming():
    assert classify(90) == "Upcoming"


def test_boundary_ninety_one_days_is_healthy():
    assert classify(91) == "Healthy"


def test_none_is_unknown():
    assert classify(None) == "Unknown"

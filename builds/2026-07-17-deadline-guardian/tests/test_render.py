from datetime import date, timedelta

from src.render import bucket_deadlines, render_dashboard


def _make(id_, due_date, completed=False, **overrides):
    d = {
        "id": id_,
        "title": f"Deadline {id_}",
        "category": "Other",
        "due_date": due_date.isoformat(),
        "recurrence": "none",
        "recurrence_months": None,
        "notes": None,
        "source_text": None,
        "extraction_method": "manual",
        "completed": completed,
        "completed_at": None,
        "created_at": "2027-01-01T00:00:00+00:00",
    }
    d.update(overrides)
    return d


def test_bucket_overdue():
    today = date(2027, 6, 1)
    d = _make(1, today - timedelta(days=3))
    buckets = bucket_deadlines([d], today)
    assert buckets["overdue"] == [d]


def test_bucket_due_this_week():
    today = date(2027, 6, 1)
    d = _make(2, today + timedelta(days=5))
    buckets = bucket_deadlines([d], today)
    assert buckets["due_this_week"] == [d]


def test_bucket_due_this_month():
    today = date(2027, 6, 1)
    d = _make(3, today + timedelta(days=20))
    buckets = bucket_deadlines([d], today)
    assert buckets["due_this_month"] == [d]


def test_bucket_upcoming():
    today = date(2027, 6, 1)
    d = _make(4, today + timedelta(days=90))
    buckets = bucket_deadlines([d], today)
    assert buckets["upcoming"] == [d]


def test_bucket_completed_regardless_of_due_date():
    today = date(2027, 6, 1)
    # Even though this is overdue by date, completed=True should win.
    d = _make(5, today - timedelta(days=30), completed=True)
    buckets = bucket_deadlines([d], today)
    assert buckets["completed"] == [d]
    assert buckets["overdue"] == []


def test_render_dashboard_escapes_script_breakout():
    hostile_title = 'Nice</script><img src=x onerror="alert(1)">'
    d = _make(1, date(2027, 6, 1), title=hostile_title)
    html = render_dashboard([d], today=date(2027, 6, 1))
    # Exactly our two intentional script tags should close — a third,
    # attacker-controlled "</script>" would break out of the JSON data block.
    assert html.count("</script>") == 2
    assert hostile_title not in html  # only the escaped form should appear
    assert "<\\/script>" in html


def test_render_dashboard_empty_state_has_no_deadlines_message():
    html = render_dashboard([], today=date(2027, 6, 1))
    assert '"deadlines": []' in html.replace(" ", "").replace("\n", "") or '"deadlines":[]' in html.replace(" ", "").replace("\n", "")
    assert "0 deadlines tracked" in html


def test_render_dashboard_total_count_in_subtitle():
    deadlines = [_make(i, date(2027, 6, 1)) for i in range(3)]
    html = render_dashboard(deadlines, today=date(2027, 6, 1))
    assert "3 deadlines tracked" in html


def test_render_dashboard_singular_count_grammar():
    d = _make(1, date(2027, 6, 1))
    html = render_dashboard([d], today=date(2027, 6, 1))
    assert "1 deadline tracked" in html

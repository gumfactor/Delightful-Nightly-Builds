import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import db, render


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test.db")
    connection = db.connect(db_path)
    yield connection
    connection.close()


def test_build_summary_counts_funnel_stages(conn):
    db.add_manuscript(conn, "A", "Doe", "J", "review", "2026-01-01")
    m2 = db.add_manuscript(conn, "B", "Doe", "J", "review", "2026-01-01")
    db.update_status(conn, m2, "under_review")
    manuscripts = db.list_manuscripts(conn)
    summary = render.build_summary(manuscripts, today=date(2026, 3, 1))
    assert summary["funnel"]["submitted"] == 1
    assert summary["funnel"]["under_review"] == 1


def test_build_summary_flags_at_risk_manuscripts(conn):
    db.add_manuscript(conn, "Stale", "Doe", "J", "review", "2026-01-01", expected_review_days=30)
    manuscripts = db.list_manuscripts(conn)
    summary = render.build_summary(manuscripts, today=date(2026, 3, 1))
    assert len(summary["at_risk"]) == 1
    assert summary["at_risk"][0]["title"] == "Stale"


def test_render_terminal_includes_stage_counts(conn):
    db.add_manuscript(conn, "A", "Doe", "J", "review", "2026-01-01")
    manuscripts = db.list_manuscripts(conn)
    output = render.render_terminal(manuscripts, today=date(2026, 3, 1))
    assert "Submitted" in output
    assert "A" in output


def test_render_terminal_shows_none_when_nothing_at_risk(conn):
    db.add_manuscript(conn, "A", "Doe", "J", "review", "2026-03-01")
    manuscripts = db.list_manuscripts(conn)
    output = render.render_terminal(manuscripts, today=date(2026, 3, 1))
    assert "At risk: none" in output


def test_render_html_escapes_script_injection_in_title(conn):
    db.add_manuscript(conn, "<script>alert(1)</script>", "Doe", "J", "review", "2026-01-01")
    manuscripts = db.list_manuscripts(conn)
    output = render.render_html(manuscripts, today=date(2026, 3, 1))
    assert "<script>alert(1)</script>" not in output
    assert "\\u003cscript\\u003ealert(1)\\u003c/script\\u003e" in output


def test_render_html_escapes_img_onerror_payload(conn):
    db.add_manuscript(conn, '<img src=x onerror=alert(1)>', "Doe", "J", "review", "2026-01-01")
    manuscripts = db.list_manuscripts(conn)
    output = render.render_html(manuscripts, today=date(2026, 3, 1))
    assert "<img src=x onerror=alert(1)>" not in output
    assert "\\u003cimg src=x onerror=alert(1)\\u003e" in output


def test_render_html_funnel_counts_match_data(conn):
    db.add_manuscript(conn, "A", "Doe", "J", "review", "2026-01-01")
    db.add_manuscript(conn, "B", "Doe", "J", "review", "2026-01-01")
    manuscripts = db.list_manuscripts(conn)
    output = render.render_html(manuscripts, today=date(2026, 3, 1))
    assert '"submitted": 2' in output


def test_render_html_includes_fallback_path_for_blocked_cdn():
    output = render.render_html([], today=date(2026, 3, 1))
    assert "chart-fallback" in output
    assert "drawFallbackTable" in output


def test_render_html_uses_textcontent_not_innerhtml_for_dynamic_rows():
    output = render.render_html([], today=date(2026, 3, 1))
    assert "innerHTML" not in output

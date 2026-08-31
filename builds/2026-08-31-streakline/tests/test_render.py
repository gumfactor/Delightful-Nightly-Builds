"""Unit tests for src/render.py — dashboard data assembly and HTML output."""

import json
import re
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.coach import CoachNote
from src.db import StreakDB
from src.render import build_dashboard_data, render_html

_HABITS = [
    {"id": "running", "name": "Running", "cadence": "daily", "source": "garmin",
     "garmin_activity_types": ["Running"]},
    {"id": "writing", "name": "Writing", "cadence": "daily", "source": "manual"},
]


@pytest.fixture
def db(tmp_path: Path) -> StreakDB:
    return StreakDB(tmp_path / "test.db")


def _extract_payload(html: str) -> dict:
    match = re.search(
        r'<script type="application/json" id="streakline-data">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match, "JSON payload script tag not found in rendered HTML"
    return json.loads(match.group(1))


def test_build_dashboard_data_includes_streak_numbers(db: StreakDB) -> None:
    db.add_completion("running", date(2026, 8, 20), source="garmin", detail="Morning Run")
    db.add_completion("running", date(2026, 8, 21), source="garmin", detail="Morning Run")
    coach_note = CoachNote(text="Keep it up.", source="deterministic")

    data = build_dashboard_data(_HABITS, db, date(2026, 8, 21), coach_note)

    running = next(h for h in data["habits"] if h["id"] == "running")
    assert running["current_streak"] == 2
    assert running["longest_streak"] == 2
    assert data["coach_note"]["text"] == "Keep it up."


def test_render_html_embeds_valid_json_payload(db: StreakDB) -> None:
    coach_note = CoachNote(text="Note.", source="deterministic")
    data = build_dashboard_data(_HABITS, db, date(2026, 8, 21), coach_note)
    html = render_html(data)
    payload = _extract_payload(html)
    assert payload["as_of"] == "2026-08-21"
    assert len(payload["habits"]) == 2


def test_render_html_contains_habit_names(db: StreakDB) -> None:
    coach_note = CoachNote(text="Note.", source="deterministic")
    data = build_dashboard_data(_HABITS, db, date(2026, 8, 21), coach_note)
    html = render_html(data)
    assert "Streakline" in html
    payload = _extract_payload(html)
    names = {h["name"] for h in payload["habits"]}
    assert names == {"Running", "Writing"}


def test_render_html_escapes_script_injection_in_completion_detail(db: StreakDB) -> None:
    payload_attack = "</script><script>window.__xss=true;</script>"
    db.add_completion("writing", date(2026, 8, 21), source="manual", detail=payload_attack)
    coach_note = CoachNote(text="Note.", source="deterministic")

    data = build_dashboard_data(_HABITS, db, date(2026, 8, 21), coach_note)
    html = render_html(data)

    # The literal closing sequence must never appear unescaped inside the
    # JSON payload script tag (that's what would let it terminate the tag
    # early and inject a real executable <script>).
    assert "</script><script>" not in html
    assert "window.__xss" in html  # the text is present...
    payload = _extract_payload(html)
    writing = next(h for h in payload["habits"] if h["id"] == "writing")
    assert writing["completions"][0]["detail"] == payload_attack  # ...and round-trips intact


def test_render_html_never_uses_innerhtml(db: StreakDB) -> None:
    coach_note = CoachNote(text="Note.", source="deterministic")
    data = build_dashboard_data(_HABITS, db, date(2026, 8, 21), coach_note)
    html = render_html(data)
    assert "innerHTML =" not in html.replace(".innerHTML = ''", "")


def test_dashboard_data_reflects_weekly_cadence(db: StreakDB) -> None:
    habits = [
        {"id": "golf", "name": "Golf", "cadence": "weekly", "source": "garmin",
         "garmin_activity_types": ["Golf"]},
    ]
    db.add_completion("golf", date(2026, 8, 2), source="garmin")
    db.add_completion("golf", date(2026, 8, 9), source="garmin")
    coach_note = CoachNote(text="Note.", source="deterministic")

    data = build_dashboard_data(habits, db, date(2026, 8, 9), coach_note)

    golf = data["habits"][0]
    assert golf["cadence"] == "weekly"
    assert golf["current_streak"] == 2

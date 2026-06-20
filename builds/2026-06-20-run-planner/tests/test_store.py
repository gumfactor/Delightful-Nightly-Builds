"""Tests for store.py — JSON persistence and parsing."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import store


# ---------------------------------------------------------------------------
# parse_duration
# ---------------------------------------------------------------------------

def test_parse_duration_mmss():
    assert store.parse_duration("50:30") == 3030


def test_parse_duration_hhmmss():
    assert store.parse_duration("1:05:30") == 3930


def test_parse_duration_zero_seconds():
    assert store.parse_duration("10:00") == 600


def test_parse_duration_invalid_format():
    with pytest.raises(ValueError, match="Invalid time format"):
        store.parse_duration("blah")


def test_parse_duration_too_many_parts():
    with pytest.raises(ValueError, match="Invalid time format"):
        store.parse_duration("1:2:3:4")


# ---------------------------------------------------------------------------
# format_pace
# ---------------------------------------------------------------------------

def test_format_pace_exact():
    # 10 km in 3600s → 360s/km = 6:00
    assert store.format_pace(10.0, 3600) == "6:00"


def test_format_pace_fractional():
    # 5 km in 1500s → 300s/km = 5:00
    assert store.format_pace(5.0, 1500) == "5:00"


def test_format_pace_zero_distance_returns_placeholder():
    assert store.format_pace(0.0, 600) == "--:--"


# ---------------------------------------------------------------------------
# log_run / list_runs
# ---------------------------------------------------------------------------

def test_log_run_returns_correct_fields(tmp_path):
    run = store.log_run("2026-06-20", 8.5, 3030, "moderate", "test note", _path=tmp_path / "r.json")
    assert run["date"] == "2026-06-20"
    assert run["distance_km"] == 8.5
    assert run["duration_seconds"] == 3030
    assert run["effort"] == "moderate"
    assert run["notes"] == "test note"
    assert "pace" in run
    assert "id" in run


def test_log_run_appears_in_list(tmp_path):
    p = tmp_path / "r.json"
    store.log_run("2026-06-20", 5.0, 1800, _path=p)
    runs = store.list_runs(_path=p)
    assert len(runs) == 1
    assert runs[0]["distance_km"] == 5.0


def test_log_run_invalid_date_raises(tmp_path):
    with pytest.raises(ValueError, match="Invalid date"):
        store.log_run("20-06-2026", 5.0, 1800, _path=tmp_path / "r.json")


def test_log_run_negative_distance_raises(tmp_path):
    with pytest.raises(ValueError, match="positive"):
        store.log_run("2026-06-20", -1.0, 1800, _path=tmp_path / "r.json")


def test_log_run_invalid_effort_raises(tmp_path):
    with pytest.raises(ValueError, match="Effort must be"):
        store.log_run("2026-06-20", 5.0, 1800, effort="sprint", _path=tmp_path / "r.json")


def test_list_runs_sorted_by_date(tmp_path):
    p = tmp_path / "r.json"
    store.log_run("2026-06-20", 8.0, 2700, _path=p)
    store.log_run("2026-06-18", 5.0, 1800, _path=p)
    store.log_run("2026-06-19", 10.0, 3600, _path=p)
    runs = store.list_runs(_path=p)
    dates = [r["date"] for r in runs]
    assert dates == ["2026-06-18", "2026-06-19", "2026-06-20"]


def test_list_runs_empty_store(tmp_path):
    runs = store.list_runs(_path=tmp_path / "r.json")
    assert runs == []


def test_multiple_runs_get_unique_ids(tmp_path):
    p = tmp_path / "r.json"
    r1 = store.log_run("2026-06-20", 5.0, 1500, _path=p)
    r2 = store.log_run("2026-06-20", 8.0, 2400, _path=p)
    assert r1["id"] != r2["id"]

import csv
from datetime import date

import pytest

from src.loader import load_budget_csv, load_effort_csv


def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def test_load_budget_csv_happy_path(tmp_path):
    path = tmp_path / "budget.csv"
    write_csv(
        path,
        ["grant_id", "grant_name", "fiscal_year", "category", "description", "direct_cost"],
        [["G1", "Grant One", "2026", "Personnel", "PI salary", "10000"]],
    )
    lines, flags = load_budget_csv(path)
    assert len(lines) == 1
    assert flags == []
    assert lines[0].grant_id == "G1"
    assert lines[0].direct_cost == 10000.0
    assert lines[0].row_number == 2


def test_load_budget_csv_missing_columns_flags_error(tmp_path):
    path = tmp_path / "budget.csv"
    write_csv(path, ["grant_id", "category"], [["G1", "Personnel"]])
    lines, flags = load_budget_csv(path)
    assert lines == []
    assert len(flags) == 1
    assert flags[0].code == "missing_columns"
    assert flags[0].severity.value == "error"


def test_load_budget_csv_malformed_direct_cost_skips_row_not_crash(tmp_path):
    path = tmp_path / "budget.csv"
    write_csv(
        path,
        ["grant_id", "grant_name", "fiscal_year", "category", "description", "direct_cost"],
        [
            ["G1", "Grant One", "2026", "Personnel", "PI salary", "not-a-number"],
            ["G1", "Grant One", "2026", "Travel", "Conf travel", "500"],
        ],
    )
    lines, flags = load_budget_csv(path)
    assert len(lines) == 1
    assert lines[0].category == "Travel"
    assert any(f.code == "malformed_direct_cost" for f in flags)


def test_load_budget_csv_missing_grant_id_skips_row(tmp_path):
    path = tmp_path / "budget.csv"
    write_csv(
        path,
        ["grant_id", "grant_name", "fiscal_year", "category", "description", "direct_cost"],
        [["", "Grant One", "2026", "Personnel", "PI salary", "1000"]],
    )
    lines, flags = load_budget_csv(path)
    assert lines == []
    assert any(f.code == "missing_grant_id" for f in flags)


def test_load_budget_csv_empty_file(tmp_path):
    path = tmp_path / "budget.csv"
    write_csv(
        path, ["grant_id", "grant_name", "fiscal_year", "category", "description", "direct_cost"], []
    )
    lines, flags = load_budget_csv(path)
    assert lines == []
    assert flags == []


def test_load_effort_csv_happy_path(tmp_path):
    path = tmp_path / "effort.csv"
    write_csv(
        path,
        ["person_name", "grant_id", "grant_name", "period_start", "period_end", "percent_effort"],
        [["A. Reyes", "G1", "Grant One", "2026-01-01", "2026-06-30", "25"]],
    )
    lines, flags = load_effort_csv(path)
    assert len(lines) == 1
    assert flags == []
    assert lines[0].period_start == date(2026, 1, 1)
    assert lines[0].period_end == date(2026, 6, 30)
    assert lines[0].percent_effort == 25.0


def test_load_effort_csv_malformed_date_skips_row(tmp_path):
    path = tmp_path / "effort.csv"
    write_csv(
        path,
        ["person_name", "grant_id", "grant_name", "period_start", "period_end", "percent_effort"],
        [["A. Reyes", "G1", "Grant One", "not-a-date", "2026-06-30", "25"]],
    )
    lines, flags = load_effort_csv(path)
    assert lines == []
    assert any(f.code == "malformed_date" for f in flags)


def test_load_effort_csv_malformed_percent_skips_row(tmp_path):
    path = tmp_path / "effort.csv"
    write_csv(
        path,
        ["person_name", "grant_id", "grant_name", "period_start", "period_end", "percent_effort"],
        [["A. Reyes", "G1", "Grant One", "2026-01-01", "2026-06-30", "twenty-five"]],
    )
    lines, flags = load_effort_csv(path)
    assert lines == []
    assert any(f.code == "malformed_percent_effort" for f in flags)


def test_load_effort_csv_missing_columns_flags_error(tmp_path):
    path = tmp_path / "effort.csv"
    write_csv(path, ["person_name"], [["A. Reyes"]])
    lines, flags = load_effort_csv(path)
    assert lines == []
    assert flags[0].code == "missing_columns"


def test_load_effort_csv_missing_required_field_skips_row(tmp_path):
    path = tmp_path / "effort.csv"
    write_csv(
        path,
        ["person_name", "grant_id", "grant_name", "period_start", "period_end", "percent_effort"],
        [["", "G1", "Grant One", "2026-01-01", "2026-06-30", "25"]],
    )
    lines, flags = load_effort_csv(path)
    assert lines == []
    assert any(f.code == "missing_required_field" for f in flags)

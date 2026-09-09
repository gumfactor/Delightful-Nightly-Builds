from datetime import date

import pytest

from src.csv_import import CSVImportError, import_contributions, import_income


def test_import_contributions_happy_path(tmp_path):
    path = tmp_path / "contribs.csv"
    path.write_text("Date,Amount\n2024-01-15,3000\n2024-06-01,1500.50\n")
    rows = import_contributions(path)
    assert rows == [
        {"date": date(2024, 1, 15), "amount": 3000.0},
        {"date": date(2024, 6, 1), "amount": 1500.50},
    ]


def test_import_contributions_is_case_insensitive_to_headers(tmp_path):
    path = tmp_path / "contribs.csv"
    path.write_text("DATE,AMOUNT\n2024-01-15,3000\n")
    rows = import_contributions(path)
    assert rows[0]["amount"] == 3000.0


def test_import_contributions_missing_column_raises(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("Date,Value\n2024-01-15,3000\n")
    with pytest.raises(CSVImportError, match="amount"):
        import_contributions(path)


def test_import_contributions_bad_date_raises_with_line_number(tmp_path):
    path = tmp_path / "bad_date.csv"
    path.write_text("Date,Amount\nnot-a-date,3000\n")
    with pytest.raises(CSVImportError, match="line 2"):
        import_contributions(path)


def test_import_contributions_empty_file_raises(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("")
    with pytest.raises(CSVImportError):
        import_contributions(path)


def test_import_income_happy_path(tmp_path):
    path = tmp_path / "income.csv"
    path.write_text("Year,Earned_Income,Pension_Adjustment\n2023,90000,0\n2024,95000,500\n")
    rows = import_income(path)
    assert rows == [
        {"year": 2023, "earned_income": 90000.0, "pension_adjustment": 0.0},
        {"year": 2024, "earned_income": 95000.0, "pension_adjustment": 500.0},
    ]


def test_import_income_pension_adjustment_optional(tmp_path):
    path = tmp_path / "income.csv"
    path.write_text("Year,Earned_Income\n2023,90000\n")
    rows = import_income(path)
    assert rows[0]["pension_adjustment"] == 0.0


def test_import_income_missing_column_raises(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("Year,Salary\n2023,90000\n")
    with pytest.raises(CSVImportError, match="earned_income"):
        import_income(path)

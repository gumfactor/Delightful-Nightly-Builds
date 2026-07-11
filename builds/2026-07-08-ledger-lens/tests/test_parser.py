import datetime
import os

import pytest

from src import parser as txn_parser


def _write_csv(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_detects_standard_headers(tmp_path):
    path = _write_csv(
        tmp_path, "standard.csv",
        "Date,Description,Amount\n2026-01-05,Coffee Shop,-4.50\n",
    )
    result = txn_parser.parse_csv(path)
    assert len(result.transactions) == 1
    txn = result.transactions[0]
    assert txn.date == datetime.date(2026, 1, 5)
    assert txn.description == "Coffee Shop"
    assert txn.amount == -4.50


def test_detects_alternate_headers(tmp_path):
    path = _write_csv(
        tmp_path, "alt.csv",
        "Transaction Date,Details,Transaction Amount\n01/15/2026,Grocery Run,-32.10\n",
    )
    result = txn_parser.parse_csv(path)
    assert len(result.transactions) == 1
    assert result.transactions[0].date == datetime.date(2026, 1, 15)


def test_detects_split_debit_credit_columns(tmp_path):
    path = _write_csv(
        tmp_path, "splitdc.csv",
        "Date,Description,Debit,Credit\n2026-02-01,Salary,,3000.00\n2026-02-02,Rent,1500.00,\n",
    )
    result = txn_parser.parse_csv(path)
    assert len(result.transactions) == 2
    salary, rent = result.transactions
    assert salary.amount == 3000.00
    assert rent.amount == -1500.00


def test_parses_multiple_date_formats(tmp_path):
    path = _write_csv(
        tmp_path, "dates.csv",
        "Date,Description,Amount\n"
        "2026-03-01,ISO Format,-10.00\n"
        "03/02/2026,US Format,-11.00\n"
        "03-Mar-2026,Month Abbrev,-12.00\n",
    )
    result = txn_parser.parse_csv(path)
    assert len(result.transactions) == 3
    assert {t.date.day for t in result.transactions} == {1, 2, 3}


def test_skips_malformed_rows_and_reports_count(tmp_path):
    path = _write_csv(
        tmp_path, "malformed.csv",
        "Date,Description,Amount\n"
        "2026-04-01,Good Row,-10.00\n"
        "not-a-date,Bad Row,-10.00\n"
        "2026-04-02,,-10.00\n"
        "2026-04-03,No Amount,\n",
    )
    result = txn_parser.parse_csv(path)
    assert len(result.transactions) == 1
    assert result.skipped_rows == 3
    assert result.total_rows == 4


def test_raises_on_missing_required_columns(tmp_path):
    path = _write_csv(tmp_path, "bad_headers.csv", "Foo,Bar\n1,2\n")
    with pytest.raises(txn_parser.ParseError):
        txn_parser.parse_csv(path)


def test_missing_file_raises_parse_error(tmp_path):
    with pytest.raises(txn_parser.ParseError):
        txn_parser.parse_csv(str(tmp_path / "does_not_exist.csv"))


def test_invert_sign_flag(tmp_path):
    path = _write_csv(
        tmp_path, "inverted.csv",
        "Date,Description,Amount\n2026-05-01,Card Charge,25.00\n",
    )
    normal = txn_parser.parse_csv(path)
    inverted = txn_parser.parse_csv(path, invert_sign=True)
    assert normal.transactions[0].amount == 25.00
    assert inverted.transactions[0].amount == -25.00


def test_existing_category_column_is_preserved(tmp_path):
    path = _write_csv(
        tmp_path, "withcat.csv",
        "Date,Description,Amount,Category\n2026-05-01,Something,-10.00,Custom Cat\n",
    )
    result = txn_parser.parse_csv(path)
    txn = result.transactions[0]
    assert txn.category == "Custom Cat"
    assert txn.category_source == "existing"


def test_sample_csv_parses_cleanly(sample_csv_path):
    result = txn_parser.parse_csv(sample_csv_path)
    assert result.skipped_rows == 0
    assert len(result.transactions) == result.total_rows
    assert len(result.transactions) > 30

import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from csv_io import BudgetCsvError, parse_budget_csv  # noqa: E402


def test_valid_csv_parses_correctly():
    text = (
        "item,category,amount,date,justification\n"
        "Stipend,Personnel,1000.50,2026-05-01,RA salary\n"
    )
    lines = parse_budget_csv(text)
    assert len(lines) == 1
    assert lines[0].item == "Stipend"
    assert lines[0].category == "Personnel"
    assert lines[0].amount == 1000.50
    assert lines[0].item_date == date(2026, 5, 1)
    assert lines[0].justification == "RA salary"


def test_missing_required_column_raises():
    text = "item,category,amount\nStipend,Personnel,1000\n"
    with pytest.raises(BudgetCsvError, match="missing required column"):
        parse_budget_csv(text)


def test_malformed_amount_raises():
    text = "item,category,amount,date\nStipend,Personnel,not-a-number,2026-05-01\n"
    with pytest.raises(BudgetCsvError, match="invalid amount"):
        parse_budget_csv(text)


def test_negative_amount_raises():
    text = "item,category,amount,date\nStipend,Personnel,-100,2026-05-01\n"
    with pytest.raises(BudgetCsvError, match="negative"):
        parse_budget_csv(text)


def test_malformed_date_raises():
    text = "item,category,amount,date\nStipend,Personnel,1000,05/01/2026\n"
    with pytest.raises(BudgetCsvError, match="invalid date"):
        parse_budget_csv(text)


def test_empty_file_raises():
    with pytest.raises(BudgetCsvError, match="empty"):
        parse_budget_csv("")


def test_header_only_no_rows_raises():
    text = "item,category,amount,date\n"
    with pytest.raises(BudgetCsvError, match="no data rows"):
        parse_budget_csv(text)


def test_empty_item_raises():
    text = "item,category,amount,date\n,Personnel,1000,2026-05-01\n"
    with pytest.raises(BudgetCsvError, match="cannot be empty"):
        parse_budget_csv(text)


def test_bom_and_whitespace_are_handled():
    text = (
        "﻿item,category,amount,date,justification\n"
        " Stipend ,  Personnel , 1000 , 2026-05-01 , RA salary \n"
    )
    lines = parse_budget_csv(text)
    assert lines[0].item == "Stipend"
    assert lines[0].amount == 1000.0


def test_amount_with_dollar_sign_and_commas_is_parsed():
    text = "item,category,amount,date\nEquipment,Equipment,\"$1,200.00\",2026-05-01\n"
    lines = parse_budget_csv(text)
    assert lines[0].amount == 1200.00


def test_missing_optional_justification_defaults_to_empty_string():
    text = "item,category,amount,date\nEquipment,Equipment,500,2026-05-01\n"
    lines = parse_budget_csv(text)
    assert lines[0].justification == ""

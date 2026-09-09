import json
from datetime import date
from pathlib import Path

import pytest

from src import storage
from src.rrsp import Contribution, IncomeRecord, OpeningBalance
from src.tfsa import Transaction


SAMPLE_PATH = Path(__file__).parent.parent / "data" / "sample_headroom.json"


def test_load_missing_file_raises(tmp_path):
    with pytest.raises(storage.StorageError):
        storage.load(tmp_path / "does_not_exist.json")


def test_load_invalid_json_raises(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not valid json")
    with pytest.raises(storage.StorageError):
        storage.load(path)


def test_load_missing_birth_year_raises(tmp_path):
    path = tmp_path / "no_birth_year.json"
    path.write_text(json.dumps({"profile": {}}))
    with pytest.raises(storage.StorageError):
        storage.load(path)


def test_save_then_load_round_trips(tmp_path):
    path = tmp_path / "headroom.json"
    data = storage.default_profile()
    data["profile"]["birth_year"] = 1990
    storage.save(path, data)
    loaded = storage.load(path)
    assert loaded["profile"]["birth_year"] == 1990


def test_load_sample_data_file():
    data = storage.load(SAMPLE_PATH)
    assert data["profile"]["birth_year"] == 1990


def test_tfsa_transactions_parses_dates_and_amounts():
    data = storage.load(SAMPLE_PATH)
    contributions, withdrawals = storage.tfsa_transactions(data)
    assert Transaction(date(2020, 6, 1), 6000.0) in contributions
    assert Transaction(date(2023, 11, 1), 3000.0) in withdrawals


def test_rrsp_records_parses_contributions_income_and_opening_balance():
    data = storage.load(SAMPLE_PATH)
    contributions, income, opening = storage.rrsp_records(data)
    assert Contribution(date(2021, 2, 15), 10_000.0, 2020) in contributions
    assert IncomeRecord(2019, 80_000.0, 0.0) in income
    assert opening is None


def test_rrsp_records_parses_opening_balance_when_present():
    data = storage.default_profile()
    data["profile"]["birth_year"] = 1990
    data["rrsp_opening_balance"] = {"year": 2022, "amount": 50000}
    _, _, opening = storage.rrsp_records(data)
    assert opening == OpeningBalance(2022, 50000.0)

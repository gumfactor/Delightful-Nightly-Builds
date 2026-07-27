import json

import pytest
from config import ConfigError, DEFAULT_TICKERS, load_tickers


def test_default_tickers_nonempty_and_well_formed():
    tickers = load_tickers(None)
    assert tickers == DEFAULT_TICKERS
    assert len(tickers) >= 10
    for entry in tickers:
        assert entry["ticker"] and entry["name"] and entry["subsector"]


def test_default_tickers_have_unique_symbols():
    symbols = [t["ticker"] for t in DEFAULT_TICKERS]
    assert len(symbols) == len(set(symbols))


def test_load_tickers_from_json_overrides_default(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps([{"ticker": "abc", "name": "ABC Corp", "subsector": "Custom"}])
    )
    tickers = load_tickers(str(config_file))
    assert tickers == [{"ticker": "ABC", "name": "ABC Corp", "subsector": "Custom"}]


def test_load_tickers_missing_file_raises_config_error(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    with pytest.raises(ConfigError):
        load_tickers(str(missing))


def test_load_tickers_malformed_json_raises_config_error(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{not valid json")
    with pytest.raises(ConfigError):
        load_tickers(str(bad_file))


def test_load_tickers_missing_required_field_raises_config_error(tmp_path):
    bad_file = tmp_path / "incomplete.json"
    bad_file.write_text(json.dumps([{"ticker": "XYZ", "name": "XYZ Inc"}]))
    with pytest.raises(ConfigError):
        load_tickers(str(bad_file))


def test_load_tickers_empty_array_raises_config_error(tmp_path):
    empty_file = tmp_path / "empty.json"
    empty_file.write_text("[]")
    with pytest.raises(ConfigError):
        load_tickers(str(empty_file))

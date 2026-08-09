"""Tests for fetch_data.py. All network access is mocked — a fake
`downloader` callable stands in for yfinance, so these tests never touch
the network (see CLAUDE.md: "Mock all external API calls in tests")."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

import fetch_data


def make_price_history(closes: list[float], start: str = "2023-01-02") -> pd.DataFrame:
    """Build a fake yfinance-shaped history DataFrame (DatetimeIndex, a
    'Close' column) from a plain list of closing prices."""
    index = pd.bdate_range(start=start, periods=len(closes))
    return pd.DataFrame({"Close": closes}, index=index)


def fake_downloader_factory(price_map: dict[str, list[float] | None]):
    """Returns a downloader(ticker, period, interval, auto_adjust) callable
    that serves canned price histories, raising for tickers mapped to the
    string 'raise' and returning empty data for tickers mapped to None."""

    def downloader(ticker, period, interval, auto_adjust):
        closes = price_map.get(ticker)
        if closes == "raise":
            raise RuntimeError("simulated network failure")
        if closes is None:
            return pd.DataFrame()
        return make_price_history(closes)

    return downloader


# ---- fetch_price_series -----------------------------------------------


def test_fetch_price_series_returns_series_on_success():
    downloader = fake_downloader_factory({"AAA": [100.0, 101.0, 102.0] * 15})
    series = fetch_data.fetch_price_series("AAA", 3, downloader)
    assert series is not None
    assert series.name == "AAA"
    assert len(series) == 45


def test_fetch_price_series_returns_none_on_exception():
    downloader = fake_downloader_factory({"BAD": "raise"})
    series = fetch_data.fetch_price_series("BAD", 3, downloader)
    assert series is None


def test_fetch_price_series_returns_none_on_empty_data():
    downloader = fake_downloader_factory({"EMPTY": None})
    series = fetch_data.fetch_price_series("EMPTY", 3, downloader)
    assert series is None


def test_fetch_price_series_returns_none_on_too_few_rows():
    downloader = fake_downloader_factory({"THIN": [100.0, 101.0, 99.0]})
    series = fetch_data.fetch_price_series("THIN", 3, downloader)
    assert series is None


# ---- align_log_returns --------------------------------------------------


def test_align_log_returns_computes_correct_values():
    # Two tickers, deterministic prices, computed by hand.
    a = pd.Series([100.0, 110.0, 121.0], index=pd.bdate_range("2023-01-02", periods=3), name="A")
    b = pd.Series([50.0, 49.0, 50.5], index=pd.bdate_range("2023-01-02", periods=3), name="B")
    returns = fetch_data.align_log_returns({"A": a, "B": b})

    assert list(returns.columns) == ["A", "B"]
    assert len(returns) == 2  # first row dropped (no prior day)

    expected_a1 = math.log(110.0 / 100.0)
    expected_a2 = math.log(121.0 / 110.0)
    expected_b1 = math.log(49.0 / 50.0)
    expected_b2 = math.log(50.5 / 49.0)

    assert returns["A"].iloc[0] == pytest.approx(expected_a1)
    assert returns["A"].iloc[1] == pytest.approx(expected_a2)
    assert returns["B"].iloc[0] == pytest.approx(expected_b1)
    assert returns["B"].iloc[1] == pytest.approx(expected_b2)


def test_align_log_returns_inner_joins_on_common_dates():
    # B is missing the middle date — the aligned frame should only keep
    # dates present in both series.
    dates_a = pd.bdate_range("2023-01-02", periods=4)
    a = pd.Series([100.0, 101.0, 102.0, 103.0], index=dates_a, name="A")
    dates_b = [dates_a[0], dates_a[2], dates_a[3]]
    b = pd.Series([50.0, 51.0, 52.0], index=dates_b, name="B")

    returns = fetch_data.align_log_returns({"A": a, "B": b})
    # Only dates present in both A and B survive the inner join, and the
    # very first surviving date has no prior day within the aligned set
    # so it's dropped as well by the return computation.
    assert len(returns) <= 2


# ---- compute_stats --------------------------------------------------------


def test_compute_stats_matches_hand_calculation():
    # Constant, known daily returns so mean/vol/cov/corr are exactly
    # predictable by hand.
    returns = pd.DataFrame(
        {
            "A": [0.01, -0.01, 0.02, -0.02, 0.01],
            "B": [0.01, -0.01, 0.02, -0.02, 0.01],  # identical to A -> corr = 1
        }
    )
    stats = fetch_data.compute_stats(returns)

    expected_mean_daily = sum([0.01, -0.01, 0.02, -0.02, 0.01]) / 5
    expected_mean_annual = expected_mean_daily * fetch_data.TRADING_DAYS_PER_YEAR

    assert stats["mean_return"]["A"] == pytest.approx(expected_mean_annual)
    assert stats["mean_return"]["B"] == pytest.approx(expected_mean_annual)
    assert stats["volatility"]["A"] == pytest.approx(stats["volatility"]["B"])
    assert stats["corr_matrix"][0][1] == pytest.approx(1.0, abs=1e-9)
    assert stats["cov_matrix"][0][0] == pytest.approx(stats["cov_matrix"][1][1])
    # A perfectly correlated pair's covariance should equal vol_A * vol_B
    assert stats["cov_matrix"][0][1] == pytest.approx(stats["volatility"]["A"] * stats["volatility"]["B"], rel=1e-6)


def test_compute_stats_negative_correlation():
    returns = pd.DataFrame(
        {
            "A": [0.02, -0.01, 0.03, -0.02, 0.01],
            "B": [-0.02, 0.01, -0.03, 0.02, -0.01],  # exact opposite -> corr = -1
        }
    )
    stats = fetch_data.compute_stats(returns)
    assert stats["corr_matrix"][0][1] == pytest.approx(-1.0, abs=1e-9)


# ---- build_dataset --------------------------------------------------------


def test_build_dataset_success_shapes_output():
    price_map = {
        "AAA": [100.0 + i * 0.3 for i in range(200)],
        "BBB": [50.0 - i * 0.05 for i in range(200)],
        "CCC": [200.0 + (i % 7) * 1.1 for i in range(200)],
        "DDD": [10.0 + (i % 5) * 0.2 for i in range(200)],
    }
    ticker_meta = {t: {"name": t, "sector": "Test"} for t in price_map}
    downloader = fake_downloader_factory(price_map)

    fixed_now = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)
    dataset = fetch_data.build_dataset(3, ticker_meta, downloader, now=fixed_now)

    assert dataset["generated_at"] == "2026-08-09T12:00:00Z"
    assert set(dataset["tickers"]) == set(price_map.keys())
    assert dataset["years"] == 3
    n = len(dataset["tickers"])
    assert len(dataset["cov_matrix"]) == n
    assert all(len(row) == n for row in dataset["cov_matrix"])
    assert len(dataset["corr_matrix"]) == n
    # Every diagonal correlation entry must be exactly 1
    for i in range(n):
        assert dataset["corr_matrix"][i][i] == pytest.approx(1.0, abs=1e-9)
    # meta carries through for every surviving ticker
    for t in dataset["tickers"]:
        assert dataset["meta"][t] == ticker_meta[t]


def test_build_dataset_skips_failed_tickers_but_still_succeeds():
    price_map = {
        "AAA": [100.0 + i * 0.3 for i in range(200)],
        "BBB": [50.0 - i * 0.05 for i in range(200)],
        "CCC": [200.0 + (i % 7) * 1.1 for i in range(200)],
        "DDD": [10.0 + (i % 5) * 0.2 for i in range(200)],
        "BAD": "raise",
        "EMPTY": None,
    }
    ticker_meta = {t: {"name": t, "sector": "Test"} for t in price_map}
    downloader = fake_downloader_factory(price_map)

    dataset = fetch_data.build_dataset(3, ticker_meta, downloader)
    assert set(dataset["tickers"]) == {"AAA", "BBB", "CCC", "DDD"}


def test_build_dataset_raises_when_too_few_tickers_survive():
    price_map = {
        "AAA": [100.0 + i * 0.3 for i in range(200)],
        "BBB": "raise",
        "CCC": None,
        "DDD": "raise",
    }
    ticker_meta = {t: {"name": t, "sector": "Test"} for t in price_map}
    downloader = fake_downloader_factory(price_map)

    with pytest.raises(ValueError, match="tickers returned usable data"):
        fetch_data.build_dataset(3, ticker_meta, downloader)


# ---- write_data_js / write_dataset_json -----------------------------------


def test_write_data_js_produces_loadable_json_payload(tmp_path: Path):
    dataset = {
        "generated_at": "2026-08-09T00:00:00Z",
        "years": 3,
        "tickers": ["A", "B"],
        "meta": {"A": {"name": "Asset A", "sector": "Test"}, "B": {"name": "Asset B", "sector": "Test"}},
        "mean_return": {"A": 0.1, "B": 0.05},
        "volatility": {"A": 0.2, "B": 0.1},
        "cov_matrix": [[0.04, 0.01], [0.01, 0.01]],
        "corr_matrix": [[1.0, 0.5], [0.5, 1.0]],
    }
    out_path = tmp_path / "data.js"
    fetch_data.write_data_js(dataset, out_path)

    content = out_path.read_text(encoding="utf-8")
    assert content.startswith("// Generated by fetch_data.py")
    assert "window.PORTFOLIO_DATA = " in content

    # Extract and parse the JSON payload back out to confirm it round-trips.
    json_text = content.split("window.PORTFOLIO_DATA = ", 1)[1].rsplit(";\n", 1)[0]
    parsed = json.loads(json_text)
    assert parsed == dataset


def test_write_dataset_json_round_trips(tmp_path: Path):
    dataset = {"tickers": ["A"], "mean_return": {"A": 0.1}}
    out_path = tmp_path / "dataset.json"
    fetch_data.write_dataset_json(dataset, out_path)
    assert json.loads(out_path.read_text(encoding="utf-8")) == dataset


# ---- CLI (main) -------------------------------------------------------


def test_main_writes_files_and_exits_zero(tmp_path: Path, monkeypatch):
    price_map = {
        t: [100.0 + i * 0.1 * (idx + 1) for i in range(200)]
        for idx, t in enumerate(fetch_data.DEFAULT_TICKERS)
    }
    downloader = fake_downloader_factory(price_map)
    monkeypatch.setattr(fetch_data, "default_downloader", downloader)

    out_path = tmp_path / "data.js"
    exit_code = fetch_data.main(["--years", "3", "--out", str(out_path)])

    assert exit_code == 0
    assert out_path.exists()
    assert "window.PORTFOLIO_DATA" in out_path.read_text(encoding="utf-8")


def test_main_returns_nonzero_on_failure(monkeypatch, capsys):
    def always_raise(ticker, period, interval, auto_adjust):
        raise RuntimeError("no network")

    monkeypatch.setattr(fetch_data, "default_downloader", always_raise)
    exit_code = fetch_data.main(["--years", "1"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "ERROR" in captured.err

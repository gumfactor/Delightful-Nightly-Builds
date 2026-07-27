import json

import pytest

import main
from storage import SiliconWatchDB


FAKE_METRICS = {
    "price": 100.0,
    "market_cap": 500.0,
    "pe_trailing": 30.0,
    "pe_forward": 25.0,
    "peg_ratio": 1.2,
    "profit_margin": 0.4,
    "revenue_growth": 0.3,
    "target_mean_price": 120.0,
    "week52_low": 70.0,
    "week52_high": 130.0,
}
FAKE_HISTORY = [("2026-07-25", 98.0), ("2026-07-26", 99.0), ("2026-07-27", 100.0)]


def patch_fetchers(monkeypatch, metrics=None, history=None):
    monkeypatch.setattr(main, "fetch_snapshot", lambda ticker: dict(metrics or FAKE_METRICS))
    monkeypatch.setattr(main, "fetch_price_history", lambda ticker: list(history or FAKE_HISTORY))


def test_resolve_universe_default_when_no_tickers_arg():
    universe = main.resolve_universe(None, None)
    assert len(universe) >= 10


def test_resolve_universe_filters_to_requested_tickers():
    universe = main.resolve_universe(None, "nvda, amd")
    assert [u["ticker"] for u in universe] == ["NVDA", "AMD"]


def test_resolve_universe_unknown_ticker_gets_custom_metadata():
    universe = main.resolve_universe(None, "ZZZZ")
    assert universe == [{"ticker": "ZZZZ", "name": "ZZZZ", "subsector": "Custom"}]


def test_cli_sync_stores_snapshot_for_each_ticker(tmp_path, monkeypatch):
    patch_fetchers(monkeypatch)
    db_path = str(tmp_path / "sw.db")
    main.main(["sync", "--db", db_path, "--tickers", "NVDA,AMD"])

    db = SiliconWatchDB(db_path)
    latest = db.get_latest_snapshots()
    db.close()
    assert {row["ticker"] for row in latest} == {"NVDA", "AMD"}
    assert all(row["market_cap"] == 500.0 for row in latest)


def test_cli_sync_twice_same_day_does_not_duplicate(tmp_path, monkeypatch):
    patch_fetchers(monkeypatch)
    db_path = str(tmp_path / "sw.db")
    main.main(["sync", "--db", db_path, "--tickers", "NVDA"])
    main.main(["sync", "--db", db_path, "--tickers", "NVDA"])

    db = SiliconWatchDB(db_path)
    rows = db.get_snapshot_history("NVDA")
    db.close()
    assert len(rows) == 1


def test_cli_sync_warns_on_missing_price(tmp_path, monkeypatch, capsys):
    metrics_with_no_price = dict(FAKE_METRICS)
    metrics_with_no_price["price"] = None
    patch_fetchers(monkeypatch, metrics=metrics_with_no_price)
    db_path = str(tmp_path / "sw.db")
    main.main(["sync", "--db", db_path, "--tickers", "NVDA"])
    captured = capsys.readouterr()
    assert "NVDA" in captured.out
    assert "Warning" in captured.out


def test_cli_report_generates_html_file(tmp_path, monkeypatch):
    patch_fetchers(monkeypatch)
    db_path = str(tmp_path / "sw.db")
    output_path = str(tmp_path / "report.html")
    main.main(["sync", "--db", db_path, "--tickers", "NVDA,AMD"])
    main.main(["report", "--db", db_path, "--output", output_path])

    content = open(output_path).read()
    assert content.strip().startswith("<!DOCTYPE html>")
    assert "NVDA" in content


def test_cli_report_without_prior_sync_exits(tmp_path, capsys):
    db_path = str(tmp_path / "empty.db")
    output_path = str(tmp_path / "report.html")
    with pytest.raises(SystemExit):
        main.main(["report", "--db", db_path, "--output", output_path])
    assert "No data yet" in capsys.readouterr().out


def test_cli_report_with_ai_flag_uses_generate_narrative(tmp_path, monkeypatch):
    patch_fetchers(monkeypatch)
    monkeypatch.setattr(main, "generate_narrative", lambda aggregates: ("Custom AI narrative text.", "ai"))
    db_path = str(tmp_path / "sw.db")
    output_path = str(tmp_path / "report.html")
    main.main(["sync", "--db", db_path, "--tickers", "NVDA"])
    main.main(["report", "--db", db_path, "--output", output_path, "--ai"])

    content = open(output_path).read()
    assert "Custom AI narrative text." in content
    assert "AI-generated sector narrative" in content


def test_cli_report_without_ai_flag_never_calls_generate_narrative(tmp_path, monkeypatch):
    patch_fetchers(monkeypatch)

    def should_not_be_called(aggregates):
        raise AssertionError("generate_narrative should not be called without --ai")

    monkeypatch.setattr(main, "generate_narrative", should_not_be_called)
    db_path = str(tmp_path / "sw.db")
    output_path = str(tmp_path / "report.html")
    main.main(["sync", "--db", db_path, "--tickers", "NVDA"])
    main.main(["report", "--db", db_path, "--output", output_path])
    assert "Deterministic sector summary" in open(output_path).read()


def test_cli_list_prints_default_tickers(capsys):
    main.main(["list"])
    captured = capsys.readouterr()
    assert "NVDA" in captured.out
    assert "GPU / AI Accelerators" in captured.out


def test_cli_list_with_custom_config(tmp_path, capsys):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps([{"ticker": "ZETA", "name": "Zeta Corp", "subsector": "Custom"}]))
    main.main(["list", "--config", str(config_file)])
    captured = capsys.readouterr()
    assert "ZETA" in captured.out
    assert "Zeta Corp" in captured.out


def test_cli_list_with_missing_config_prints_error(tmp_path, capsys):
    missing = str(tmp_path / "nope.json")
    with pytest.raises(SystemExit):
        main.main(["list", "--config", missing])
    assert "Config error" in capsys.readouterr().err


def test_cli_invalid_command_exits_nonzero(capsys):
    with pytest.raises(SystemExit):
        main.main(["bogus-command"])


def test_cli_no_command_exits_nonzero():
    with pytest.raises(SystemExit):
        main.main([])

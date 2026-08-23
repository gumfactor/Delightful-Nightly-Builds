"""Tests for main.py — CLI wiring, isolated from the real DB/dashboard paths."""

import pytest

import main
from src import storage
from src.ibkr_client import IBKRConnectionError


@pytest.fixture(autouse=True)
def isolated_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(main, "DASHBOARD_PATH", tmp_path / "dashboard.html")
    yield


def fake_snapshot(net_liq=1.0, positions=None):
    return {
        "account_id": "U123",
        "net_liquidation": net_liq,
        "total_cash": 1.0,
        "gross_position_value": 1.0,
        "unrealized_pnl": 1.0,
        "realized_pnl": 1.0,
        "buying_power": 1.0,
        "positions": positions or [],
    }


def test_sync_success_prints_account_and_position_count(monkeypatch, capsys):
    monkeypatch.setattr(main, "fetch_snapshot", lambda **kwargs: fake_snapshot())

    exit_code = main.main(["sync"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "U123" in out
    assert "0 positions" in out


def test_sync_connection_failure_prints_friendly_error_and_returns_nonzero(monkeypatch, capsys):
    def raise_error(**kwargs):
        raise IBKRConnectionError("TWS not running on 127.0.0.1:7497")

    monkeypatch.setattr(main, "fetch_snapshot", raise_error)

    exit_code = main.main(["sync"])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "TWS not running" in err


def test_sync_passes_cli_flags_through_to_fetch_snapshot(monkeypatch):
    captured = {}

    def fake_fetch(**kwargs):
        captured.update(kwargs)
        return fake_snapshot()

    monkeypatch.setattr(main, "fetch_snapshot", fake_fetch)

    main.main(["sync", "--host", "10.0.0.5", "--port", "4001", "--client-id", "9", "--timeout", "3"])

    assert captured == {"host": "10.0.0.5", "port": 4001, "client_id": 9, "timeout": 3.0}


def test_show_with_no_prior_sync_prints_placeholder(capsys):
    exit_code = main.main(["show"])
    assert exit_code == 0
    assert "No snapshot yet" in capsys.readouterr().out


def test_show_prints_latest_snapshot_fields(monkeypatch, capsys):
    conn = storage.connect(str(main.DB_PATH))
    storage.init_db(conn)
    storage.sync_snapshot(conn, fake_snapshot(net_liq=12345.67), snapshot_date="2026-08-20")
    conn.close()

    exit_code = main.main(["show"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "12,345.67" in out


def test_history_with_days_limits_output_rows(capsys):
    conn = storage.connect(str(main.DB_PATH))
    storage.init_db(conn)
    for day in ["2026-08-18", "2026-08-19", "2026-08-20"]:
        storage.sync_snapshot(conn, fake_snapshot(), snapshot_date=day)
    conn.close()

    exit_code = main.main(["history", "--days", "2"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "2026-08-19" in out and "2026-08-20" in out
    assert "2026-08-18" not in out


def test_history_with_no_data_prints_placeholder(capsys):
    exit_code = main.main(["history"])
    assert exit_code == 0
    assert "No history yet" in capsys.readouterr().out


def test_render_with_no_prior_sync_still_writes_dashboard_file():
    exit_code = main.main(["render"])

    assert exit_code == 0
    assert main.DASHBOARD_PATH.exists()
    assert "No snapshot yet" in main.DASHBOARD_PATH.read_text(encoding="utf-8")


def test_render_with_ai_briefing_flag_embeds_the_returned_note(monkeypatch):
    conn = storage.connect(str(main.DB_PATH))
    storage.init_db(conn)
    storage.sync_snapshot(conn, fake_snapshot(), snapshot_date="2026-08-20")
    conn.close()

    monkeypatch.setattr(main.ai_briefing, "build_briefing", lambda summary, **kw: "AI note here")

    exit_code = main.main(["render", "--ai-briefing"])

    assert exit_code == 0
    assert "AI note here" in main.DASHBOARD_PATH.read_text(encoding="utf-8")


def test_render_without_ai_briefing_flag_never_calls_ai_briefing(monkeypatch):
    conn = storage.connect(str(main.DB_PATH))
    storage.init_db(conn)
    storage.sync_snapshot(conn, fake_snapshot(), snapshot_date="2026-08-20")
    conn.close()

    called = []
    monkeypatch.setattr(main.ai_briefing, "build_briefing", lambda summary, **kw: called.append(1) or "x")

    main.main(["render"])

    assert called == []


def test_parser_requires_a_subcommand():
    with pytest.raises(SystemExit):
        main.main([])

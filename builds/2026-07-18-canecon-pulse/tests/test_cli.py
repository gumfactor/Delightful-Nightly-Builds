from datetime import date

import canecon_pulse
from src.indicators import Indicator
from src.models import Observation
from src.storage import connect, get_history


def fake_indicator_with_data():
    return Indicator(
        series_id="FXUSDCAD",
        label="USD/CAD Exchange Rate",
        unit="CAD per USD",
        source="Bank of Canada Valet",
        fetch=lambda recent: [
            Observation(
                series_id="FXUSDCAD",
                series_label="USD/CAD Exchange Rate",
                unit="CAD per USD",
                source="Bank of Canada Valet",
                obs_date=date(2026, 7, 1),
                value=1.32,
            )
        ],
    )


def fake_indicator_that_fails():
    return Indicator(
        series_id="STATCAN_V41690973",
        label="Canada All-Items CPI",
        unit="index (2002=100)",
        source="Statistics Canada WDS",
        fetch=lambda recent: [],
    )


def test_sync_stores_data_from_working_indicator_and_skips_failing_one(tmp_path, monkeypatch, capsys):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(
        canecon_pulse, "INDICATORS", [fake_indicator_with_data(), fake_indicator_that_fails()]
    )

    canecon_pulse.cmd_sync(db_path, recent=10)

    conn = connect(db_path)
    assert get_history(conn, "FXUSDCAD") == [(date(2026, 7, 1), 1.32)]
    assert get_history(conn, "STATCAN_V41690973") == []
    conn.close()

    captured = capsys.readouterr()
    assert "[skip]" in captured.out
    assert "[ok]" in captured.out


def test_sync_never_raises_when_every_indicator_fails(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(canecon_pulse, "INDICATORS", [fake_indicator_that_fails()])

    canecon_pulse.cmd_sync(db_path, recent=10)  # must not raise

    conn = connect(db_path)
    assert get_history(conn, "STATCAN_V41690973") == []
    conn.close()


def test_show_on_empty_database_prints_helpful_message(tmp_path, monkeypatch, capsys):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(canecon_pulse, "INDICATORS", [fake_indicator_with_data()])

    canecon_pulse.cmd_show(db_path)

    captured = capsys.readouterr()
    assert "No indicators have any history yet" in captured.out


def test_render_on_empty_database_produces_valid_html(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    out_path = str(tmp_path / "dashboard.html")
    monkeypatch.setattr(canecon_pulse, "INDICATORS", [fake_indicator_with_data()])

    canecon_pulse.cmd_render(db_path, out_path, use_ai=False)

    content = open(out_path, encoding="utf-8").read()
    assert content.startswith("<!doctype html")
    assert "No data yet" in content


def test_run_chains_sync_and_render(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    out_path = str(tmp_path / "dashboard.html")
    monkeypatch.setattr(canecon_pulse, "INDICATORS", [fake_indicator_with_data()])

    canecon_pulse.cmd_run(db_path, out_path, recent=10, use_ai=False)

    content = open(out_path, encoding="utf-8").read()
    assert "USD/CAD Exchange Rate" in content
    assert "1.32" in content


def test_main_show_command_returns_zero_on_empty_db(tmp_path, monkeypatch):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(canecon_pulse, "INDICATORS", [fake_indicator_with_data()])

    exit_code = canecon_pulse.main(["show", "--db", db_path])

    assert exit_code == 0

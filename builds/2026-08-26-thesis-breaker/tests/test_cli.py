import json
import os

import pytest

from src.cli import main


@pytest.fixture
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_demo_runs_with_no_network_and_no_api_key(workdir, monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    exit_code = main(["--db", "test.db", "demo", "--out", "report.html"])
    assert exit_code == 0
    assert (workdir / "report.html").exists()
    out = capsys.readouterr().out
    assert "AAPL" in out
    assert "no network used" in out


def test_demo_report_contains_expected_sections(workdir):
    main(["--db", "test.db", "demo", "--out", "report.html"])
    html = (workdir / "report.html").read_text()
    assert "Value Skeptic" in html
    assert "Macro Bear" in html
    assert "Governance Hawk" in html
    assert "Triggered-Checklist Matrix" in html


def test_demo_twice_creates_two_history_rows(workdir, capsys):
    main(["--db", "test.db", "demo", "--out", "report1.html"])
    main(["--db", "test.db", "demo", "--out", "report2.html"])
    capsys.readouterr()
    main(["--db", "test.db", "history", "AAPL"])
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if line.startswith("#")]
    assert len(lines) == 2


def test_history_reports_no_checks_for_unknown_ticker(workdir, capsys):
    main(["--db", "test.db", "demo", "--out", "report.html"])
    capsys.readouterr()
    main(["--db", "test.db", "history", "ZZZZ"])
    out = capsys.readouterr().out
    assert "No saved checks for ZZZZ" in out


def test_list_shows_all_saved_checks(workdir, capsys):
    main(["--db", "test.db", "demo", "--out", "report.html"])
    capsys.readouterr()
    main(["--db", "test.db", "list"])
    out = capsys.readouterr().out
    assert "AAPL" in out


def test_render_regenerates_report_for_saved_id(workdir, capsys):
    main(["--db", "test.db", "demo", "--out", "report.html"])
    capsys.readouterr()
    main(["--db", "test.db", "render", "--id", "1", "--out", "rerendered.html"])
    assert (workdir / "rerendered.html").exists()
    html = (workdir / "rerendered.html").read_text()
    assert "AAPL" in html


def test_render_unknown_id_returns_error_exit_code(workdir):
    main(["--db", "test.db", "demo", "--out", "report.html"])
    exit_code = main(["--db", "test.db", "render", "--id", "999", "--out", "x.html"])
    assert exit_code == 1


def test_demo_with_custom_thesis_text(workdir):
    main(["--db", "test.db", "demo", "--thesis", "Undervalued and safe.", "--out", "report.html"])
    html = (workdir / "report.html").read_text()
    assert "Undervalued and safe." in html


def test_demo_ai_polish_flag_falls_back_without_key(workdir, monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    exit_code = main(["--db", "test.db", "demo", "--ai-polish", "--out", "report.html"])
    assert exit_code == 0  # falls back silently, never crashes

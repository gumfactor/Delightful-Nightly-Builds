import json
from unittest.mock import MagicMock, patch

import pytest

from src import cli
from tests.conftest import make_forecast_payload


def _mock_urlopen_for_payload(payload: dict):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    return mock_response


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "cli_test.db")


@pytest.fixture
def calm_payload():
    return make_forecast_payload(
        ["2026-10-04", "2026-10-05"],
        wind_knots=8.0, gust_knots=10.0, temp_c=20.0, precip_probability=5.0, cloud_cover=20.0,
    )


def test_forecast_command_prints_table(db_path, calm_payload, capsys):
    with patch("src.openmeteo.urllib.request.urlopen", return_value=_mock_urlopen_for_payload(calm_payload)):
        exit_code = cli.main(["--db", db_path, "forecast", "--lat", "44.5", "--lon", "-78.2"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "afternoon" in out
    assert "<-- best" in out


def test_generate_command_saves_and_prints_entry(db_path, calm_payload, capsys):
    with patch("src.openmeteo.urllib.request.urlopen", return_value=_mock_urlopen_for_payload(calm_payload)):
        exit_code = cli.main(["--db", db_path, "generate", "--location-name", "Stony Lake"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Saved entry #1" in out

    exit_code = cli.main(["--db", db_path, "list"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "#1" in out
    assert "Stony Lake" in out


def test_generate_with_explicit_date_and_window(db_path, calm_payload, capsys):
    with patch("src.openmeteo.urllib.request.urlopen", return_value=_mock_urlopen_for_payload(calm_payload)):
        exit_code = cli.main([
            "--db", db_path, "generate",
            "--location-name", "Stony Lake",
            "--date", "2026-10-05", "--window", "morning",
        ])
    assert exit_code == 0

    with patch("src.openmeteo.urllib.request.urlopen", return_value=_mock_urlopen_for_payload(calm_payload)):
        cli.main(["--db", db_path, "show", "1"])
    out = capsys.readouterr().out
    assert "2026-10-05" in out
    assert "morning" in out


def test_generate_with_invalid_date_returns_error(db_path, calm_payload, capsys):
    with patch("src.openmeteo.urllib.request.urlopen", return_value=_mock_urlopen_for_payload(calm_payload)):
        exit_code = cli.main([
            "--db", db_path, "generate",
            "--location-name", "Stony Lake",
            "--date", "2099-01-01",
        ])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "Error" in err


def test_generate_with_ai_polish_flag_falls_back_without_key(db_path, calm_payload, capsys, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # src.openmeteo and src.ai_polish both do `import urllib.request`, so they
    # share the exact same global urlopen attribute -- patching it once here
    # covers both call sites. ai_polish.polish() must short-circuit before
    # ever touching it when no API key is set, so it should be called exactly
    # once (by the Open-Meteo fetch), never twice.
    with patch("src.openmeteo.urllib.request.urlopen", return_value=_mock_urlopen_for_payload(calm_payload)) as mock_urlopen:
        exit_code = cli.main([
            "--db", db_path, "generate",
            "--location-name", "Stony Lake",
            "--ai-polish",
        ])
    assert exit_code == 0
    assert mock_urlopen.call_count == 1


def test_list_command_with_no_entries(db_path, capsys):
    exit_code = cli.main(["--db", db_path, "list"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "No entries" in out


def test_show_command_missing_id_returns_error(db_path, capsys):
    exit_code = cli.main(["--db", db_path, "show", "42"])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "Error" in err


def test_search_command_finds_saved_entry(db_path, calm_payload, capsys):
    with patch("src.openmeteo.urllib.request.urlopen", return_value=_mock_urlopen_for_payload(calm_payload)):
        cli.main(["--db", db_path, "generate", "--location-name", "Stony Lake"])
    capsys.readouterr()

    exit_code = cli.main(["--db", db_path, "search", "Stony"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "#1" in out


def test_search_command_no_match(db_path, capsys):
    exit_code = cli.main(["--db", db_path, "search", "nonexistent-xyz"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "No matching entries" in out


def test_render_command_offline_writes_file(db_path, calm_payload, tmp_path):
    output_path = str(tmp_path / "out.html")
    with patch("src.openmeteo.urllib.request.urlopen", return_value=_mock_urlopen_for_payload(calm_payload)):
        cli.main(["--db", db_path, "generate", "--location-name", "Stony Lake"])

    exit_code = cli.main(["--db", db_path, "render", "--offline", "--output", output_path])
    assert exit_code == 0
    with open(output_path, encoding="utf-8") as f:
        content = f.read()
    assert "<!DOCTYPE html>" in content
    assert "Stony Lake" in content


def test_render_command_handles_forecast_fetch_failure_gracefully(db_path, tmp_path, capsys):
    import urllib.error

    output_path = str(tmp_path / "out.html")
    with patch("src.openmeteo.urllib.request.urlopen", side_effect=urllib.error.URLError("blocked")):
        exit_code = cli.main(["--db", db_path, "render", "--output", output_path])
    assert exit_code == 0
    err = capsys.readouterr().err
    assert "Warning" in err


def test_invalid_subcommand_exits_nonzero(db_path):
    with pytest.raises(SystemExit):
        cli.main(["--db", db_path, "not-a-real-command"])

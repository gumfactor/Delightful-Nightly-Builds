import json
import os
from pathlib import Path

import pytest

import main as parity_main

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def config_path(tmp_path):
    config = {
        "teamwork": {"project_ids": [1]},
        "coda": {
            "doc_id": "doc1",
            "table_id": "table1",
            "title_column": "Name",
            "status_column": "Status",
            "done_values": ["Done"],
        },
        "match_threshold": 0.5,
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    return str(path)


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "parity.db")


def test_demo_sync_runs_end_to_end_with_no_network(config_path, db_path, monkeypatch):
    # Ensure no live-credential path is ever reachable during --demo.
    monkeypatch.delenv("TEAMWORK_DOMAIN", raising=False)
    monkeypatch.delenv("TEAMWORK_API_KEY", raising=False)
    monkeypatch.delenv("CODA_API_KEY", raising=False)

    exit_code = parity_main.main(["--db", db_path, "sync", "--config", config_path, "--demo"])
    assert exit_code == 0
    assert os.path.exists(db_path)


def test_demo_sync_classifies_fixture_items_correctly(config_path, db_path):
    parity_main.main(["--db", db_path, "sync", "--config", config_path, "--demo"])

    from store import connect, latest_run_items

    conn = connect(db_path)
    run, items = latest_run_items(conn)
    conn.close()

    assert run.matched_ok == 1
    assert run.status_conflict == 1
    assert run.teamwork_only == 1
    assert run.coda_only == 1

    conflict_item = next(i for i in items if i["bucket"] == "status_conflict")
    assert conflict_item["teamwork_title"] == "Renew lab safety certification"
    assert "done in Teamwork" in conflict_item["detail"]


def test_two_syncs_persist_two_runs_for_drift_history(config_path, db_path):
    parity_main.main(["--db", db_path, "sync", "--config", config_path, "--demo"])
    parity_main.main(["--db", db_path, "sync", "--config", config_path, "--demo"])

    from store import connect, history

    conn = connect(db_path)
    runs = history(conn)
    conn.close()

    assert len(runs) == 2
    assert runs[0].matched_ok == runs[1].matched_ok == 1


def test_render_produces_html_file(config_path, db_path, tmp_path):
    parity_main.main(["--db", db_path, "sync", "--config", config_path, "--demo"])
    out_path = tmp_path / "dashboard.html"
    exit_code = parity_main.main(["--db", db_path, "render", "--out", str(out_path)])

    assert exit_code == 0
    assert out_path.exists()
    assert "<!doctype html>" in out_path.read_text()


def test_teamwork_api_error_produces_clean_message_not_traceback(config_path, db_path, monkeypatch, capsys):
    from teamwork_client import TeamworkAPIError

    def raising_fetch_live(config):
        raise TeamworkAPIError("Teamwork API returned status 401 for project 1")

    monkeypatch.setattr(parity_main, "fetch_live", raising_fetch_live)
    exit_code = parity_main.main(["--db", db_path, "sync", "--config", config_path])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Teamwork API returned status 401" in captured.err


def test_coda_api_error_produces_clean_message_not_traceback(config_path, db_path, monkeypatch, capsys):
    from coda_client import CodaAPIError

    def raising_fetch_live(config):
        raise CodaAPIError("Coda API returned status 403 for table table1")

    monkeypatch.setattr(parity_main, "fetch_live", raising_fetch_live)
    exit_code = parity_main.main(["--db", db_path, "sync", "--config", config_path])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Coda API returned status 403" in captured.err


def test_render_without_prior_sync_returns_error_not_crash(db_path, tmp_path, capsys):
    out_path = tmp_path / "dashboard.html"
    exit_code = parity_main.main(["--db", db_path, "render", "--out", str(out_path)])
    assert exit_code == 1
    assert not out_path.exists()


def test_missing_config_file_produces_clear_error_not_traceback(db_path, tmp_path, capsys):
    missing_path = str(tmp_path / "does_not_exist.json")
    exit_code = parity_main.main(["--db", db_path, "sync", "--config", missing_path, "--demo"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "not found" in captured.err.lower()


def test_live_sync_without_credentials_gives_clear_error(config_path, db_path, monkeypatch):
    monkeypatch.delenv("TEAMWORK_DOMAIN", raising=False)
    monkeypatch.delenv("TEAMWORK_API_KEY", raising=False)
    monkeypatch.delenv("CODA_API_KEY", raising=False)

    exit_code = parity_main.main(["--db", db_path, "sync", "--config", config_path])
    assert exit_code == 1


def test_history_with_no_runs_prints_helpful_message(db_path, capsys):
    exit_code = parity_main.main(["--db", db_path, "history"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "no sync runs" in captured.out.lower()


def test_briefing_command_prints_deterministic_summary(config_path, db_path, monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    parity_main.main(["--db", db_path, "sync", "--config", config_path, "--demo"])
    exit_code = parity_main.main(["--db", db_path, "briefing"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Parity found" in captured.out

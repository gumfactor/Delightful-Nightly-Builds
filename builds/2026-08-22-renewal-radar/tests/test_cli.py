from pathlib import Path

import pytest

import renewal_radar


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "cli_test.db")


def test_add_domain_then_list_shows_unknown_bucket(db_path, capsys):
    assert renewal_radar.main(["--db", db_path, "add-domain", "--domain", "example.com", "--project", "Test"]) == 0
    assert renewal_radar.main(["--db", db_path, "list"]) == 0
    out = capsys.readouterr().out
    assert "Unknown" in out
    assert "example.com" in out


def test_add_duplicate_domain_returns_error_exit_code(db_path, capsys):
    renewal_radar.main(["--db", db_path, "add-domain", "--domain", "example.com"])
    exit_code = renewal_radar.main(["--db", db_path, "add-domain", "--domain", "example.com"])
    assert exit_code == 1
    assert "Error" in capsys.readouterr().err


def test_invalid_category_rejected_at_parse_time(db_path):
    with pytest.raises(SystemExit):
        renewal_radar.main(
            ["--db", db_path, "add-renewal", "--title", "X", "--category", "not-real",
             "--due-date", "2027-01-01", "--recurrence", "annual"]
        )


def test_sync_uses_mocked_rdap_and_tls_and_updates_list(db_path, capsys, monkeypatch):
    renewal_radar.main(["--db", db_path, "add-domain", "--domain", "example.com"])

    call_log = {"rdap": 0, "tls": 0}

    def fake_lookup_domain(domain, **kwargs):
        call_log["rdap"] += 1
        return {"status": "ok", "expiration": "2027-06-15", "registrar": "Example Registrar", "error": None}

    def fake_check_certificate(hostname, **kwargs):
        call_log["tls"] += 1
        return {"status": "ok", "expiration": "2026-09-01", "days_remaining": 10, "error": None}

    monkeypatch.setattr(renewal_radar.rdap, "lookup_domain", fake_lookup_domain)
    monkeypatch.setattr(renewal_radar.tls, "check_certificate", fake_check_certificate)

    exit_code = renewal_radar.main(["--db", db_path, "sync"])
    assert exit_code == 0
    assert call_log["rdap"] == 1
    assert call_log["tls"] == 1

    renewal_radar.main(["--db", db_path, "list"])
    out = capsys.readouterr().out
    assert "Due This Month" in out  # 10 days remaining -> Due This Month bucket


def test_add_renewal_and_complete_schedules_next_occurrence(db_path, capsys):
    renewal_radar.main(
        ["--db", db_path, "add-renewal", "--title", "Business License", "--category", "license",
         "--due-date", "2026-09-01", "--recurrence", "annual"]
    )
    exit_code = renewal_radar.main(["--db", db_path, "complete", "--id", "1"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Next occurrence scheduled 2027-09-01" in out

    renewal_radar.main(["--db", db_path, "list"])
    out = capsys.readouterr().out
    assert "Business License" in out  # the newly-scheduled occurrence is pending and listed


def test_complete_one_time_renewal_creates_no_next_occurrence(db_path, capsys):
    renewal_radar.main(
        ["--db", db_path, "add-renewal", "--title", "One-off filing", "--category", "other",
         "--due-date", "2026-09-01", "--recurrence", "one-time"]
    )
    renewal_radar.main(["--db", db_path, "complete", "--id", "1"])
    out = capsys.readouterr().out
    assert "no further occurrence" in out

    renewal_radar.main(["--db", db_path, "list"])
    out = capsys.readouterr().out
    assert "One-off filing" not in out  # completed one-time item is not pending, so not listed


def test_complete_unknown_id_returns_error(db_path, capsys):
    exit_code = renewal_radar.main(["--db", db_path, "complete", "--id", "999"])
    assert exit_code == 1
    assert "Error" in capsys.readouterr().err


def test_render_writes_dashboard_html(db_path, tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    renewal_radar.main(["--db", db_path, "add-domain", "--domain", "example.com"])
    renewal_radar.main(
        ["--db", db_path, "add-renewal", "--title", "Business License", "--category", "license",
         "--due-date", "2026-09-01", "--recurrence", "annual"]
    )
    output_path = tmp_path / "dashboard.html"
    exit_code = renewal_radar.main(["--db", db_path, "render", "--output", str(output_path)])
    assert exit_code == 0
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "<!doctype html>" in content
    assert "example.com" in content
    assert "Business License" in content


def test_list_with_nothing_tracked_does_not_error(db_path, capsys):
    exit_code = renewal_radar.main(["--db", db_path, "list"])
    assert exit_code == 0
    assert "Nothing tracked yet" in capsys.readouterr().out


def test_sync_with_no_domains_does_not_error(db_path, capsys):
    exit_code = renewal_radar.main(["--db", db_path, "sync"])
    assert exit_code == 0
    assert "No domains registered" in capsys.readouterr().out

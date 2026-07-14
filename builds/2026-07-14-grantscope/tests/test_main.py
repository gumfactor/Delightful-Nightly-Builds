from unittest.mock import patch

import api_client
import db
import main


def test_list_topics_prints_all_default_topics(capsys):
    main.main(["list-topics"])
    out = capsys.readouterr().out
    assert "empathy" in out
    assert "psychopathy" in out
    assert "affective_neuroscience" in out


def test_sync_stores_projects_from_mocked_api(tmp_path, capsys):
    db_path = tmp_path / "test.db"
    fake_projects = [
        {
            "project_num": "P1",
            "topic": "empathy",
            "title": "Empathy study",
            "abstract": "",
            "pi_name": "Jane Smith",
            "org_name": "Big State University",
            "org_city": None,
            "org_state": None,
            "ic_admin": "NIMH",
            "activity_code": "R01",
            "award_amount": 100000,
            "fiscal_year": 2024,
            "project_start": None,
            "project_end": None,
        }
    ]
    with patch("main.api_client.fetch_projects", return_value=fake_projects):
        exit_code = main.main(["--db", str(db_path), "sync", "--topics", "empathy"])
    assert exit_code == 0

    conn = db.connect(str(db_path))
    rows = db.all_projects(conn)
    assert len(rows) == 1
    assert rows[0]["project_num"] == "P1"
    conn.close()


def test_sync_reports_error_for_unknown_topic(tmp_path, capsys):
    db_path = tmp_path / "test.db"
    exit_code = main.main(["--db", str(db_path), "sync", "--topics", "not-a-real-topic"])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "unknown topic" in err.lower()


def test_sync_handles_api_error_gracefully(tmp_path, capsys):
    db_path = tmp_path / "test.db"
    with patch("main.api_client.fetch_projects", side_effect=api_client.ApiClientError("network down")):
        exit_code = main.main(["--db", str(db_path), "sync", "--topics", "empathy"])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "failed to sync" in err.lower()


def test_build_renders_dashboard_from_local_data(tmp_path):
    db_path = tmp_path / "test.db"
    out_path = tmp_path / "dashboard.html"
    conn = db.connect(str(db_path))
    db.upsert_project(conn, {
        "project_num": "P1",
        "topic": "empathy",
        "title": "Empathy study",
        "abstract": "abstract",
        "pi_name": "Jane Smith",
        "org_name": "Big State University",
        "org_city": None,
        "org_state": None,
        "ic_admin": "NIMH",
        "activity_code": "R01",
        "award_amount": 100000,
        "fiscal_year": 2024,
        "project_start": None,
        "project_end": None,
    })
    conn.close()

    exit_code = main.main(["--db", str(db_path), "build", "--out", str(out_path), "--no-ai"])
    assert exit_code == 0
    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "Empathy study" in content
    assert "GrantScope" in content


def test_build_with_no_data_still_produces_valid_dashboard(tmp_path):
    db_path = tmp_path / "empty.db"
    out_path = tmp_path / "dashboard.html"
    exit_code = main.main(["--db", str(db_path), "build", "--out", str(out_path), "--no-ai"])
    assert exit_code == 0
    content = out_path.read_text(encoding="utf-8")
    assert "GrantScope" in content


def test_stats_prints_summary(tmp_path, capsys):
    db_path = tmp_path / "test.db"
    conn = db.connect(str(db_path))
    db.upsert_project(conn, {
        "project_num": "P1", "topic": "empathy", "title": "T", "abstract": "",
        "pi_name": None, "org_name": "Org", "org_city": None, "org_state": None,
        "ic_admin": "NIMH", "activity_code": "R01", "award_amount": 200000,
        "fiscal_year": 2024, "project_start": None, "project_end": None,
    })
    conn.close()

    exit_code = main.main(["--db", str(db_path), "stats"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Projects: 1" in out
    assert "$200,000" in out


def test_search_finds_matching_project(tmp_path, capsys):
    db_path = tmp_path / "test.db"
    conn = db.connect(str(db_path))
    db.upsert_project(conn, {
        "project_num": "P1", "topic": "empathy", "title": "Amygdala reactivity", "abstract": "",
        "pi_name": None, "org_name": "Org", "org_city": None, "org_state": None,
        "ic_admin": "NIMH", "activity_code": "R01", "award_amount": 100,
        "fiscal_year": 2024, "project_start": None, "project_end": None,
    })
    conn.close()

    exit_code = main.main(["--db", str(db_path), "search", "amygdala"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Amygdala reactivity" in out


def test_search_reports_no_results(tmp_path, capsys):
    db_path = tmp_path / "empty.db"
    exit_code = main.main(["--db", str(db_path), "search", "nothing"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "No projects found" in out


def test_briefing_uses_template_fallback_without_api_key(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    db_path = tmp_path / "test.db"
    conn = db.connect(str(db_path))
    db.upsert_project(conn, {
        "project_num": "P1", "topic": "empathy", "title": "Empathy study", "abstract": "",
        "pi_name": None, "org_name": "Org", "org_city": None, "org_state": None,
        "ic_admin": "NIMH", "activity_code": "R01", "award_amount": 100000,
        "fiscal_year": 2024, "project_start": None, "project_end": None,
    })
    conn.close()

    exit_code = main.main(["--db", str(db_path), "briefing", "--topic", "empathy"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "template" in out

    conn = db.connect(str(db_path))
    briefing = db.get_briefing(conn, "empathy")
    assert briefing is not None
    conn.close()

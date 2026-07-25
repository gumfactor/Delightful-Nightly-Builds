import json
import subprocess

import pytest

from src import cli
from src import store


@pytest.fixture
def temp_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*args):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "test@example.com")
    git("config", "user.name", "Test User")

    (repo / "a.py").write_text("x = 1\n")
    git("add", "a.py")
    git("commit", "-q", "-m", "Add initial file")

    (repo / "a.py").write_text("x = 1  # fix TypeError when comparing values\n")
    git("add", "a.py")
    git("commit", "-q", "-m", "fix TypeError when comparing values")

    (repo / "b.py").write_text("y = 2\n")
    git("add", "b.py")
    git("commit", "-q", "-m", "fix typo in variable name")

    return repo


def test_build_parser_requires_subcommand():
    parser = cli.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_sync_requires_at_least_one_target(tmp_path):
    db = tmp_path / "bugtrace.db"
    with pytest.raises(SystemExit):
        cli.main(["sync", "--db", str(db)])


def test_end_to_end_local_sync_and_text_report(temp_repo, tmp_path, capsys):
    db = tmp_path / "bugtrace.db"
    cli.main(["sync", "--repo-path", str(temp_repo), "--db", str(db)])
    out = capsys.readouterr().out
    assert "Synced 2 new fix commit(s)" in out

    cli.main(["report", "--db", str(db), "--format", "text"])
    out = capsys.readouterr().out
    assert "2 classified fix commit(s)" in out


def test_sync_dedupes_on_second_run(temp_repo, tmp_path, capsys):
    db = tmp_path / "bugtrace.db"
    cli.main(["sync", "--repo-path", str(temp_repo), "--db", str(db)])
    capsys.readouterr()
    cli.main(["sync", "--repo-path", str(temp_repo), "--db", str(db)])
    out = capsys.readouterr().out
    assert "Synced 0 new fix commit(s)" in out


def test_show_command_lists_matching_category(temp_repo, tmp_path, capsys):
    db = tmp_path / "bugtrace.db"
    cli.main(["sync", "--repo-path", str(temp_repo), "--db", str(db)])
    capsys.readouterr()
    cli.main(["show", "typo_naming", "--db", str(db)])
    out = capsys.readouterr().out
    assert "fix typo in variable name" in out


def test_show_command_reports_no_matches(tmp_path, capsys):
    db = tmp_path / "bugtrace.db"
    store.init_db(str(db))
    cli.main(["show", "async_race_condition", "--db", str(db)])
    out = capsys.readouterr().out
    assert "No fix commits found" in out


def test_report_json_writes_expected_structure(temp_repo, tmp_path, capsys):
    db = tmp_path / "bugtrace.db"
    out_json = tmp_path / "report.json"
    cli.main(["sync", "--repo-path", str(temp_repo), "--db", str(db)])
    capsys.readouterr()
    cli.main(["report", "--db", str(db), "--format", "json", "--out", str(out_json)])

    data = json.loads(out_json.read_text())
    assert "counts" in data and "fixes" in data
    assert len(data["fixes"]) == 2


def test_report_html_writes_file(temp_repo, tmp_path, capsys):
    db = tmp_path / "bugtrace.db"
    out_html = tmp_path / "report.html"
    cli.main(["sync", "--repo-path", str(temp_repo), "--db", str(db)])
    capsys.readouterr()
    cli.main(["report", "--db", str(db), "--format", "html", "--out", str(out_html)])
    content = out_html.read_text()
    assert "<title>BugTrace" in content


def test_sync_github_target_without_token_is_skipped_not_crashed(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    db = tmp_path / "bugtrace.db"
    cli.main(["sync", "--repos", "someone/somerepo", "--db", str(db)])
    out = capsys.readouterr().out
    assert "Synced 0 new fix commit(s)" in out


def test_sync_with_ai_flag_uses_classifier(monkeypatch, temp_repo, tmp_path, capsys):
    db = tmp_path / "bugtrace.db"
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key")

    def fake_classify_batch(api_key, items, request_fn=None):
        return {item["sha"]: {"category": "other", "explanation": "ai says other", "source": "ai"} for item in items}

    monkeypatch.setattr(cli, "classify_batch", fake_classify_batch)
    cli.main(["sync", "--repo-path", str(temp_repo), "--db", str(db), "--ai"])
    capsys.readouterr()

    conn = store.init_db(str(db))
    fixes = store.get_all_fixes(conn)
    assert all(f["source"] == "ai" for f in fixes)
    assert all(f["category"] == "other" for f in fixes)

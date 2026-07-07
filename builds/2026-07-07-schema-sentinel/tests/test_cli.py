import json
import subprocess
import sys
from pathlib import Path

import pytest

MAIN = Path(__file__).resolve().parent.parent / "src" / "main.py"


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(MAIN), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_diff_exits_zero_when_only_safe_changes(tmp_path):
    old = write(tmp_path / "old.json", '{"id": 1}')
    new = write(tmp_path / "new.json", '{"id": 1, "email": "a@example.com"}')
    result = run_cli("diff", str(old), str(new))
    assert result.returncode == 0
    assert "email" in result.stdout


def test_diff_exits_nonzero_when_breaking_change_present(tmp_path):
    old = write(tmp_path / "old.json", '{"id": 1}')
    new = write(tmp_path / "new.json", '{}')
    result = run_cli("diff", str(old), str(new))
    assert result.returncode == 1
    assert "BREAKING" in result.stdout


def test_diff_json_output_is_valid_json(tmp_path):
    old = write(tmp_path / "old.json", '{"id": 1}')
    new = write(tmp_path / "new.json", '{"id": 1, "email": "a@example.com"}')
    result = run_cli("diff", str(old), str(new), "--json")
    payload = json.loads(result.stdout)
    assert payload["mode"] == "diff"
    assert payload["entries"][0]["field"] == "email"


def test_diff_ignore_fields_suppresses_change(tmp_path):
    old = write(tmp_path / "old.json", '{"id": 1, "last_synced_at": "x"}')
    new = write(tmp_path / "new.json", '{"id": 1}')
    result = run_cli("diff", str(old), str(new), "--ignore-fields", "last_synced_at")
    assert result.returncode == 0
    assert "No structural changes detected" in result.stdout


def test_diff_html_report_written(tmp_path):
    old = write(tmp_path / "old.json", '{"id": 1}')
    new = write(tmp_path / "new.json", '{"id": 1, "email": "a@example.com"}')
    report_path = tmp_path / "report.html"
    result = run_cli("diff", str(old), str(new), "--html", str(report_path))
    assert result.returncode == 0
    assert report_path.exists()
    assert "<html" in report_path.read_text()


def test_diff_fail_on_risky_catches_risky_only_change(tmp_path):
    old = write(tmp_path / "old.json", '[{"id": 1}, {"id": 2}]')
    new = write(tmp_path / "new.json", '[{"id": 1}, {}]')
    result_default = run_cli("diff", str(old), str(new))
    result_risky = run_cli("diff", str(old), str(new), "--fail-on", "risky")
    assert result_default.returncode == 0
    assert result_risky.returncode == 1


def test_diff_missing_file_exits_with_error_code(tmp_path):
    new = write(tmp_path / "new.json", '{"id": 1}')
    result = run_cli("diff", str(tmp_path / "missing.json"), str(new))
    assert result.returncode == 2
    assert "Error" in result.stderr


def test_history_end_to_end_json_output(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    def git(*args):
        subprocess.run(
            ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", *args],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )

    git("init", "-q")
    data_file = repo_dir / "data.json"
    data_file.write_text('{"id": 1}')
    git("add", "data.json")
    git("commit", "-q", "-m", "v1")
    data_file.write_text('{"id": 1, "email": "a@example.com"}')
    git("add", "data.json")
    git("commit", "-q", "-m", "v2")

    result = run_cli("history", "data.json", "--repo", str(repo_dir), "--json")
    payload = json.loads(result.stdout)
    assert payload["mode"] == "history"
    assert len(payload["timeline"]) == 1
    assert payload["timeline"][0]["entries"][0]["field"] == "email"


def test_history_on_non_git_directory_errors(tmp_path):
    plain_dir = tmp_path / "not_a_repo"
    plain_dir.mkdir()
    result = run_cli("history", "data.json", "--repo", str(plain_dir))
    assert result.returncode == 2
    assert "not a git repository" in result.stderr


def test_no_subcommand_shows_usage_error():
    result = run_cli()
    assert result.returncode != 0

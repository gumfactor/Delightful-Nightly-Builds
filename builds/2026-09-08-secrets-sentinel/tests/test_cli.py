import subprocess
from pathlib import Path

from src.main import main, resolve_repos, run_scan


def _run(repo_path: Path, args: list[str]) -> None:
    subprocess.run(["git", "-C", str(repo_path), *args], check=True, capture_output=True, text=True)


def _init_repo(repo_path: Path) -> None:
    repo_path.mkdir(parents=True, exist_ok=True)
    _run(repo_path, ["init", "-q"])
    _run(repo_path, ["config", "user.email", "test@example.com"])
    _run(repo_path, ["config", "user.name", "Test User"])


def _commit_file(repo_path: Path, filename: str, content: str, message: str) -> None:
    (repo_path / filename).write_text(content, encoding="utf-8")
    _run(repo_path, ["add", filename])
    _run(repo_path, ["commit", "-q", "-m", message])


def test_resolve_repos_treats_explicit_repo_path_as_single_repo(tmp_path):
    _init_repo(tmp_path)
    repos = resolve_repos([str(tmp_path)])
    assert repos == [tmp_path]


def test_resolve_repos_deduplicates_overlapping_paths(tmp_path):
    _init_repo(tmp_path)
    repos = resolve_repos([str(tmp_path), str(tmp_path)])
    assert len(repos) == 1


def test_run_scan_finds_secret_in_temp_repo_without_ai(tmp_path):
    _init_repo(tmp_path)
    _commit_file(tmp_path, "config.py", 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n', "add secret")
    findings = run_scan([str(tmp_path)], use_ai=False)
    assert len(findings) == 1
    assert findings[0].tier == "high"
    assert findings[0].ai_verdict is None


def test_run_scan_returns_empty_list_for_clean_repo(tmp_path):
    _init_repo(tmp_path)
    _commit_file(tmp_path, "readme.md", "# Hello\nThis is a clean repo.\n", "init")
    findings = run_scan([str(tmp_path)], use_ai=False)
    assert findings == []


def test_main_returns_zero_exit_code_for_clean_repo(tmp_path, capsys):
    _init_repo(tmp_path)
    _commit_file(tmp_path, "readme.md", "# Hello\n", "init")
    exit_code = main([str(tmp_path), "--no-ai"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "No findings." in captured.out


def test_main_fail_on_high_returns_nonzero_when_high_finding_present(tmp_path):
    _init_repo(tmp_path)
    _commit_file(tmp_path, "config.py", 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n', "add secret")
    exit_code = main([str(tmp_path), "--no-ai", "--fail-on-high"])
    assert exit_code == 1


def test_main_writes_html_and_json_reports(tmp_path):
    _init_repo(tmp_path)
    _commit_file(tmp_path, "config.py", 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n', "add secret")
    html_out = tmp_path / "out.html"
    json_out = tmp_path / "out.json"
    main([str(tmp_path), "--no-ai", "--html-out", str(html_out), "--json-out", str(json_out)])
    assert html_out.exists()
    assert json_out.exists()

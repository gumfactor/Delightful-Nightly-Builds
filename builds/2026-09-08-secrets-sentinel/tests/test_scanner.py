import subprocess
from pathlib import Path

from src.scanner import (
    discover_repos,
    file_still_at_head,
    list_commits,
    scan_repo,
)


def _run(repo_path: Path, args: list[str]) -> None:
    subprocess.run(["git", "-C", str(repo_path), *args], check=True, capture_output=True, text=True)


def _init_repo(repo_path: Path) -> None:
    repo_path.mkdir(parents=True, exist_ok=True)
    _run(repo_path, ["init", "-q"])
    _run(repo_path, ["config", "user.email", "test@example.com"])
    _run(repo_path, ["config", "user.name", "Test User"])


def _commit_file(repo_path: Path, filename: str, content: str, message: str) -> None:
    file_path = repo_path / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    _run(repo_path, ["add", filename])
    _run(repo_path, ["commit", "-q", "-m", message])


def _commit_binary_file(repo_path: Path, filename: str, message: str) -> None:
    file_path = repo_path / filename
    file_path.write_bytes(b"\x00\x01\x02\xff\xfe" * 20)
    _run(repo_path, ["add", filename])
    _run(repo_path, ["commit", "-q", "-m", message])


def test_discover_repos_finds_single_repo_at_root(tmp_path):
    _init_repo(tmp_path)
    found = discover_repos(tmp_path)
    assert found == [tmp_path]


def test_discover_repos_finds_multiple_repos_under_directory(tmp_path):
    repo_a = tmp_path / "repo-a"
    repo_b = tmp_path / "repo-b"
    _init_repo(repo_a)
    _init_repo(repo_b)
    found = {p.name for p in discover_repos(tmp_path)}
    assert found == {"repo-a", "repo-b"}


def test_discover_repos_skips_node_modules_directory(tmp_path):
    (tmp_path / "node_modules" / "some-package").mkdir(parents=True)
    _init_repo(tmp_path / "node_modules" / "some-package")
    real_repo = tmp_path / "my-app"
    _init_repo(real_repo)
    found = {p.name for p in discover_repos(tmp_path)}
    assert found == {"my-app"}


def test_list_commits_returns_all_commits_newest_first(tmp_path):
    _init_repo(tmp_path)
    _commit_file(tmp_path, "a.txt", "one", "first commit")
    _commit_file(tmp_path, "a.txt", "two", "second commit")
    commits = list_commits(tmp_path)
    assert len(commits) == 2
    log_output = subprocess.run(
        ["git", "-C", str(tmp_path), "log", "--format=%H"], capture_output=True, text=True, check=True
    ).stdout.splitlines()
    assert commits == log_output


def test_list_commits_respects_max_commits_cap(tmp_path):
    _init_repo(tmp_path)
    for i in range(5):
        _commit_file(tmp_path, "a.txt", str(i), f"commit {i}")
    commits = list_commits(tmp_path, max_commits=2)
    assert len(commits) == 2


def test_list_commits_returns_empty_for_nonexistent_repo(tmp_path):
    assert list_commits(tmp_path / "does-not-exist") == []


def test_scan_repo_finds_vendor_secret_still_present_in_head(tmp_path):
    _init_repo(tmp_path)
    _commit_file(tmp_path, "config.py", 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n', "add aws key")
    findings_hits = scan_repo(tmp_path)
    assert any(h.matched_text == "AKIAIOSFODNN7EXAMPLE" for h in findings_hits)
    match = next(h for h in findings_hits if h.matched_text == "AKIAIOSFODNN7EXAMPLE")
    assert match.is_vendor_pattern is True
    assert file_still_at_head(tmp_path, "config.py", "AKIAIOSFODNN7EXAMPLE") is True


def test_scan_repo_finds_secret_removed_from_head_but_present_in_history(tmp_path):
    _init_repo(tmp_path)
    _commit_file(tmp_path, "config.py", 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n', "add aws key")
    _commit_file(tmp_path, "config.py", 'AWS_KEY = os.environ["AWS_KEY"]\n', "remove hardcoded key")
    hits = scan_repo(tmp_path)
    match = next(h for h in hits if h.matched_text == "AKIAIOSFODNN7EXAMPLE")
    assert file_still_at_head(tmp_path, "config.py", "AKIAIOSFODNN7EXAMPLE") is False
    assert match.file == "config.py"


def test_scan_repo_skips_binary_files_without_crashing(tmp_path):
    _init_repo(tmp_path)
    _commit_binary_file(tmp_path, "image.bin", "add binary file")
    hits = scan_repo(tmp_path)
    assert hits == []


def test_file_still_at_head_false_for_deleted_file(tmp_path):
    _init_repo(tmp_path)
    _commit_file(tmp_path, "secret.txt", "AKIAIOSFODNN7EXAMPLE", "add")
    _run(tmp_path, ["rm", "-q", "secret.txt"])
    _run(tmp_path, ["commit", "-q", "-m", "remove file"])
    assert file_still_at_head(tmp_path, "secret.txt", "AKIAIOSFODNN7EXAMPLE") is False

import subprocess
from pathlib import Path

import pytest

from git_log import GitLogError, fetch_commits
from shiplog import build_changelog, main


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _commit(repo: Path, message: str) -> None:
    # Each commit touches its own file so a later `git revert` of an earlier
    # commit never hits a merge conflict against unrelated commits.
    slug = "".join(c if c.isalnum() else "_" for c in message)[:40]
    path = repo / f"{slug}.txt"
    path.write_text(message)
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", message)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    repo_path = tmp_path / "sample-repo"
    repo_path.mkdir()
    _git(repo_path, "init", "-q")
    _git(repo_path, "config", "user.email", "test@example.com")
    _git(repo_path, "config", "user.name", "Test User")
    _commit(repo_path, "chore: initial commit")
    return repo_path


def test_fetch_commits_full_history_when_no_since(repo: Path):
    _commit(repo, "feat: add search")
    _commit(repo, "fix: correct typo")
    commits, range_label = fetch_commits(str(repo), since=None, until="HEAD")
    assert len(commits) == 3
    assert range_label.startswith("start..")


def test_fetch_commits_invalid_until_raises():
    with pytest.raises(GitLogError):
        fetch_commits(".", since=None, until="not-a-real-ref-xyz")


def test_fetch_commits_non_git_directory_raises(tmp_path: Path):
    empty = tmp_path / "not-a-repo"
    empty.mkdir()
    with pytest.raises(GitLogError):
        fetch_commits(str(empty), since=None, until="HEAD")


def test_build_changelog_end_to_end_with_revert_pair(repo: Path):
    _commit(repo, "feat: add risky experiment")
    _commit(repo, "fix: correct null check")
    _git(repo, "revert", "--no-edit", "HEAD~1")  # reverts "feat: add risky experiment"

    result = build_changelog(
        repo_path=str(repo), since=None, until="HEAD",
        github_repo=None, github_token=None, ai_api_key=None,
    )

    assert len(result.cancelled_pairs) == 1
    all_subjects = [c.subject for commits in result.sections.values() for c in commits]
    assert not any("risky experiment" in s for s in all_subjects)
    assert any("null check" in s for s in all_subjects)
    assert result.suggested_bump == "patch"


def test_build_changelog_empty_range_has_no_commits(repo: Path):
    _git(repo, "tag", "v1.0.0")
    result = build_changelog(
        repo_path=str(repo), since="v1.0.0", until="HEAD",
        github_repo=None, github_token=None, ai_api_key=None,
    )
    assert result.total_commits == 0
    assert result.suggested_bump == "none"


def test_cli_generate_writes_both_files(repo: Path, tmp_path: Path):
    _commit(repo, "feat: add export button")
    out_dir = tmp_path / "out"
    exit_code = main([
        "generate", str(repo), "--format", "both", "--out", str(out_dir),
    ])
    assert exit_code == 0
    written = list(out_dir.glob("*"))
    names = [f.name for f in written]
    assert any(name.startswith("CHANGELOG_") and name.endswith(".md") for name in names)
    assert any(name.startswith("report_") and name.endswith(".html") for name in names)


def test_cli_generate_invalid_repo_path_returns_nonzero(tmp_path: Path, capsys):
    empty = tmp_path / "not-a-repo"
    empty.mkdir()
    exit_code = main(["generate", str(empty)])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "error" in captured.err

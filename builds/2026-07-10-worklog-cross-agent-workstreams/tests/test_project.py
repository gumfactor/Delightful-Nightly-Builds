import pytest

from worklog.project import (
    NotAGitRepoError,
    discover_project,
    parse_github_remote,
)


def test_discover_project_basic(git_repo):
    state = discover_project(str(git_repo))
    assert state.repo_root == str(git_repo.resolve())
    assert state.branch == "main"
    assert len(state.head_sha) == 40
    assert state.github_owner_repo is None
    assert state.project_id.startswith("local:")


def test_discover_project_with_github_remote(git_repo_with_remote):
    state = discover_project(str(git_repo_with_remote))
    assert state.github_owner_repo == ("example-owner", "example-repo")
    assert state.project_id == "github:example-owner/example-repo"


def test_discover_project_not_a_repo(tmp_path):
    plain_dir = tmp_path / "not_a_repo"
    plain_dir.mkdir()
    with pytest.raises(NotAGitRepoError):
        discover_project(str(plain_dir))


def test_discover_project_dirty_and_untracked_files(git_repo):
    (git_repo / "README.md").write_text("modified\n")
    (git_repo / "new_file.txt").write_text("new\n")
    state = discover_project(str(git_repo))
    assert "README.md" in state.dirty_files
    assert "new_file.txt" in state.untracked_files


def test_discover_project_dirty_file_first_in_status_keeps_full_filename(git_repo):
    # Regression: a leading-space status code (" M path") on the *first* porcelain line is
    # easy to mis-slice if the raw git output is ever whitespace-stripped upstream.
    (git_repo / "README.md").write_text("modified again\n")
    state = discover_project(str(git_repo))
    assert state.dirty_files == ["README.md"]
    assert not any(f.startswith("EADME") for f in state.dirty_files)


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/owner/repo.git", ("owner", "repo")),
        ("https://github.com/owner/repo", ("owner", "repo")),
        ("git@github.com:owner/repo.git", ("owner", "repo")),
        ("https://gitlab.com/owner/repo.git", None),
        ("", None),
    ],
)
def test_parse_github_remote(url, expected):
    assert parse_github_remote(url) == expected

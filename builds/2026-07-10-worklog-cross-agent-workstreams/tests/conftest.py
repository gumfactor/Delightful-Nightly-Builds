import subprocess
import sys
from pathlib import Path

import pytest

BUILD_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BUILD_ROOT))


def _run(args, cwd):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    assert result.returncode == 0, f"{args} failed: {result.stderr}"
    return result.stdout.strip()


@pytest.fixture
def git_repo(tmp_path):
    """A real, minimal git repository with two commits on 'main'."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init", "-q", "-b", "main"], cwd=repo)
    _run(["git", "config", "user.email", "tester@example.com"], cwd=repo)
    _run(["git", "config", "user.name", "Tester"], cwd=repo)

    (repo / "README.md").write_text("hello\n")
    _run(["git", "add", "README.md"], cwd=repo)
    _run(["git", "commit", "-q", "-m", "Initial commit"], cwd=repo)

    (repo / "app.py").write_text("print('hi')\n")
    _run(["git", "add", "app.py"], cwd=repo)
    _run(["git", "commit", "-q", "-m", "Add app.py"], cwd=repo)

    return repo


@pytest.fixture
def git_repo_with_remote(git_repo):
    """Same as git_repo but with a GitHub origin remote configured."""
    _run(
        ["git", "remote", "add", "origin", "https://github.com/example-owner/example-repo.git"],
        cwd=git_repo,
    )
    return git_repo


def commit(repo, filename, content, message):
    path = repo / filename
    path.write_text(content)
    _run(["git", "add", filename], cwd=repo)
    _run(["git", "commit", "-q", "-m", message], cwd=repo)
    return _run(["git", "rev-parse", "HEAD"], cwd=repo)


def current_head(repo):
    return _run(["git", "rev-parse", "HEAD"], cwd=repo)


def checkout_new_branch(repo, name):
    _run(["git", "checkout", "-q", "-b", name], cwd=repo)

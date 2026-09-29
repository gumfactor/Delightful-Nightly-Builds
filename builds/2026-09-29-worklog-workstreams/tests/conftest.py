import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from worklog.ledger import Ledger  # noqa: E402
from worklog.project import discover  # noqa: E402

ENV = {"GIT_AUTHOR_NAME": "Dev One", "GIT_AUTHOR_EMAIL": "dev@example.invalid",
       "GIT_COMMITTER_NAME": "Dev One", "GIT_COMMITTER_EMAIL": "dev@example.invalid"}


class Repo:
    """Throwaway git repository with deterministic commit dates."""

    def __init__(self, root: Path):
        self.root = root
        self.git("init", "-q", "-b", "main")
        self.git("config", "commit.gpgsign", "false")

    def git(self, *args: str, date: str = "2026-09-01T10:00:00+00:00") -> str:
        env = {**os.environ, **ENV, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
        proc = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True, env=env)
        assert proc.returncode == 0, proc.stderr
        return proc.stdout.strip()

    def commit(self, message: str, files: dict[str, str], date: str = "2026-09-01T10:00:00+00:00") -> str:
        for name, content in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            self.git("add", name, date=date)
        self.git("commit", "-q", "-m", message, date=date)
        return self.git("rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Repo:
    root = tmp_path / "proj"
    root.mkdir()
    return Repo(root)


@pytest.fixture
def scenario(repo: Repo) -> Repo:
    """main: base commit; feature/41-csv-validation: two commits referencing #41; one unrelated main commit."""
    repo.commit("Initial commit", {"README.md": "hello\n"}, date="2026-09-01T09:00:00+00:00")
    repo.git("checkout", "-q", "-b", "feature/41-csv-validation")
    repo.commit("Add schema checks before ingestion", {"src/validation.py": "a = 1\n"}, date="2026-09-02T10:00:00+00:00")
    repo.commit("Reject blank identifiers (#41)", {"src/validation.py": "a = 2\n", "tests/test_validation.py": "t\n"},
                date="2026-09-02T12:00:00+00:00")
    repo.git("checkout", "-q", "main")
    repo.commit("Update docs", {"docs/guide.md": "guide\n"}, date="2026-09-05T09:00:00+00:00")
    return repo


@pytest.fixture
def project(scenario: Repo):
    return discover(scenario.root)


@pytest.fixture
def ledger(tmp_path: Path):
    db = Ledger(tmp_path / "ledger.db")
    yield db
    db.close()


def make_fake_github(head_sha: str, *, merged: bool, ci_conclusion: str = "failure", changes_requested: bool = False):
    """Return a fetch(url) stub that mimics the GitHub REST API for one issue + one PR."""
    def fetch(url: str):
        path = url.split("?")[0]
        if path.endswith("/issues"):
            return [{"number": 41, "title": "Add CSV validation", "created_at": "2026-09-01T08:00:00Z",
                     "closed_at": "2026-09-04T12:00:00Z" if merged else None, "body": "Need schema checks",
                     "html_url": "https://github.com/acme/lab/issues/41", "user": {"login": "dev1", "type": "User"},
                     "labels": [{"name": "data"}]},
                    {"number": 52, "title": "PR shows in issues feed", "pull_request": {}, "created_at": "2026-09-02T13:00:00Z",
                     "user": {"login": "dev1", "type": "User"}, "labels": []}]
        if path.endswith("/pulls"):
            return [{"number": 52, "title": "Add CSV validation", "created_at": "2026-09-02T13:00:00Z",
                     "merged_at": "2026-09-04T12:00:00Z" if merged else None, "closed_at": "2026-09-04T12:00:00Z" if merged else None,
                     "body": "Closes #41", "html_url": "https://github.com/acme/lab/pull/52",
                     "user": {"login": "dev1", "type": "User"}, "draft": False,
                     "head": {"ref": "feature/41-csv-validation", "sha": head_sha}, "base": {"ref": "main"},
                     "merge_commit_sha": "f" * 40}]
        if path.endswith("/reviews"):
            state = "CHANGES_REQUESTED" if changes_requested else "APPROVED"
            return [{"id": 9001, "state": state, "submitted_at": "2026-09-03T09:00:00Z", "user": {"login": "rev", "type": "User"},
                     "html_url": "https://github.com/acme/lab/pull/52#r9001"}]
        if path.endswith("/check-runs"):
            return {"check_runs": [{"id": 777, "name": "pytest", "status": "completed", "conclusion": ci_conclusion,
                                    "completed_at": "2026-09-03T10:00:00Z", "started_at": "2026-09-03T09:55:00Z",
                                    "html_url": "https://github.com/acme/lab/runs/777"}]}
        raise AssertionError(f"unexpected URL {url}")
    return fetch


@pytest.fixture
def gh_repo(scenario: Repo) -> Repo:
    scenario.git("remote", "add", "origin", "https://ghp_" + "a" * 30 + "@github.com/acme/lab.git")
    return scenario

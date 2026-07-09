import pytest

import git_inspector as gi


class FakeResult:
    def __init__(self, stdout="", returncode=0, stderr=""):
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr


def make_runner(responses):
    """responses: list of FakeResult, consumed in call order."""
    calls = []

    def runner(args, cwd, capture_output, text, check):
        calls.append((args, cwd))
        return responses[len(calls) - 1]

    runner.calls = calls
    return runner


def test_find_repo_root_returns_stripped_path():
    runner = make_runner([FakeResult(stdout="/home/user/repo\n")])
    assert gi.find_repo_root("/home/user/repo/sub", runner=runner) == "/home/user/repo"


def test_find_repo_root_raises_on_empty_output():
    runner = make_runner([FakeResult(stdout="\n")])
    with pytest.raises(gi.GitError):
        gi.find_repo_root("/not/a/repo", runner=runner)


def test_run_raises_gitError_on_real_failure():
    runner = make_runner([FakeResult(stdout="", returncode=128, stderr="fatal: bad revision")])
    with pytest.raises(gi.GitError):
        gi._run(["rev-parse", "HEAD"], cwd=".", runner=runner)


def test_detect_default_branch_prefers_main():
    def runner(args, cwd, capture_output, text, check):
        if args[-1] == "origin/main":
            return FakeResult(returncode=0)
        return FakeResult(returncode=1)

    assert gi.detect_default_branch(".", runner=runner) == "main"


def test_detect_default_branch_falls_back_to_master():
    def runner(args, cwd, capture_output, text, check):
        if args[-1] == "origin/master":
            return FakeResult(returncode=0)
        return FakeResult(returncode=1)

    assert gi.detect_default_branch(".", runner=runner) == "master"


def test_detect_default_branch_raises_when_neither_exists():
    runner = make_runner([FakeResult(returncode=1), FakeResult(returncode=1)])
    with pytest.raises(gi.GitError):
        gi.detect_default_branch(".", runner=runner)


def test_detect_owner_repo_parses_https_url():
    runner = make_runner([FakeResult(stdout="https://github.com/gumfactor/delightful-nightly-builds.git\n")])
    assert gi.detect_owner_repo(".", runner=runner) == ("gumfactor", "delightful-nightly-builds")


def test_detect_owner_repo_parses_ssh_url():
    runner = make_runner([FakeResult(stdout="git@github.com:gumfactor/delightful-nightly-builds.git\n")])
    assert gi.detect_owner_repo(".", runner=runner) == ("gumfactor", "delightful-nightly-builds")


def test_detect_owner_repo_returns_none_for_unparseable_url():
    runner = make_runner([FakeResult(stdout="\n")])
    assert gi.detect_owner_repo(".", runner=runner) is None


def test_list_remote_branches_excludes_head_and_default():
    runner = make_runner(
        [
            FakeResult(
                stdout="origin/HEAD\norigin/main\norigin/claude/cool-sagan-abc123\n"
            )
        ]
    )
    branches = gi.list_remote_branches(".", "main", runner=runner)
    assert branches == ["origin/claude/cool-sagan-abc123"]


def test_list_build_folders_at_ref_excludes_non_folder_files():
    runner = make_runner(
        [FakeResult(stdout="2026-06-06-first\n2026-06-07-second\nindex.md\nideas.md\nidea-briefs\n")]
    )
    folders = gi.list_build_folders_at_ref(".", "origin/main", runner=runner)
    assert folders == {"2026-06-06-first", "2026-06-07-second"}


def test_folder_added_by_branch_extracts_top_level_folder():
    runner = make_runner(
        [
            FakeResult(
                stdout=(
                    "builds/2026-07-09-pipeline-pulse/PRD.md\n"
                    "builds/2026-07-09-pipeline-pulse/src/main.py\n"
                    "builds/index.md\n"
                )
            )
        ]
    )
    folders = gi.folder_added_by_branch(".", "main", "origin/claude/xyz", runner=runner)
    assert folders == {"2026-07-09-pipeline-pulse"}


def test_folder_added_by_branch_returns_empty_when_no_builds_paths():
    runner = make_runner([FakeResult(stdout="")])
    assert gi.folder_added_by_branch(".", "main", "origin/claude/xyz", runner=runner) == set()


def test_build_folder_branch_map_first_branch_wins():
    call_index = []

    def runner(args, cwd, capture_output, text, check):
        idx = len(call_index)
        call_index.append(args)
        if idx == 0:
            return FakeResult(stdout="builds/2026-07-01-alpha/PRD.md\n")
        return FakeResult(stdout="builds/2026-07-01-alpha/PRD.md\nbuilds/2026-07-02-beta/PRD.md\n")

    mapping = gi.build_folder_branch_map(
        ".", "main", ["origin/branch-a", "origin/branch-b"], runner=runner
    )
    assert mapping["2026-07-01-alpha"] == "origin/branch-a"
    assert mapping["2026-07-02-beta"] == "origin/branch-b"

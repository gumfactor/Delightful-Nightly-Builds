import json

from worklog import gitcollect
from worklog.project import discover, refs_from_branch, refs_from_text


def _by_summary(events):
    return {e["summary"]: e for e in events}


def test_commits_carry_sha_issue_ref_and_branch_keys(project):
    events = _by_summary(gitcollect.collect_commits(project))
    fix = events["Reject blank identifiers (#41)"]
    assert f"sha:{fix['ref']}" in fix["keys"]
    assert "gh:41" in fix["keys"]
    assert "branch:feature/41-csv-validation" in fix["keys"]


def test_default_branch_commits_get_no_branch_key(project):
    events = _by_summary(gitcollect.collect_commits(project))
    assert not [k for k in events["Update docs"]["keys"] if k.startswith("branch:")]


def test_commit_records_files_diffstat_and_reproduce_command(project):
    fix = _by_summary(gitcollect.collect_commits(project))["Reject blank identifiers (#41)"]
    assert fix["files"] == ["src/validation.py", "tests/test_validation.py"]
    assert fix["metadata"]["insertions"] == 2 and fix["metadata"]["deletions"] == 1
    assert fix["metadata"]["reproduce"] == f"git show {fix['ref']}"
    assert "diff" not in json.dumps(fix["metadata"]).lower().replace("diffstat", "")


def test_agent_coauthor_trailer_marks_actor_as_agent(repo):
    repo.commit("Initial", {"a.txt": "1"})
    repo.git("commit", "-q", "--allow-empty", "-m", "Refactor\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
    events = gitcollect.collect_commits(discover(repo.root))
    refactor = next(e for e in events if e["summary"] == "Refactor")
    assert (refactor["actor_kind"], refactor["actor_name"]) == ("agent", "claude")


def test_excluded_paths_are_dropped_from_file_lists(repo):
    (repo.root / ".worklog.json").write_text(json.dumps({"exclude_paths": ["*.lock", "secrets/*"]}))
    repo.commit("Add stuff", {"a.py": "1", "poetry.lock": "x", "secrets/k.txt": "y"})
    events = gitcollect.collect_commits(discover(repo.root))
    assert events[0]["files"] == ["a.py"]


def test_excluded_branches_do_not_create_branch_keys(scenario):
    (scenario.root / ".worklog.json").write_text(json.dumps({"exclude_branches": ["feature/*"]}))
    events = _by_summary(gitcollect.collect_commits(discover(scenario.root)))
    assert not [k for k in events["Add schema checks before ingestion"]["keys"] if k.startswith("branch:")]


def test_tags_become_events_keyed_to_the_tagged_commit(scenario):
    scenario.git("tag", "-a", "v1.0", "-m", "release", date="2026-09-06T00:00:00+00:00")
    tags = gitcollect.collect_tags(discover(scenario.root))
    head = scenario.git("rev-parse", "HEAD")
    assert tags[0]["summary"] == "Tag v1.0" and f"sha:{head}" in tags[0]["keys"]


def test_working_state_reports_dirty_and_untracked_files(scenario):
    (scenario.root / "README.md").write_text("changed\n")
    (scenario.root / "new.txt").write_text("n\n")
    state = gitcollect.working_state(discover(scenario.root))
    assert state["dirty"] == ["README.md"] and state["untracked"] == ["new.txt"]
    assert state["branch"] == "main" and state["head"] == scenario.git("rev-parse", "HEAD")


def test_branch_upstream_relationships_recorded(scenario):
    state = gitcollect.working_state(discover(scenario.root))
    assert "feature/41-csv-validation" in state["branches"]
    assert state["branches"]["main"]["upstream"] is None


def test_project_identity_is_stable_and_independent_of_folder_name(scenario, tmp_path):
    scenario.git("remote", "add", "origin", "git@github.com:acme/lab.git")
    first = discover(scenario.root).project_id
    clone = tmp_path / "renamed-clone"
    scenario.git("worktree", "add", "-q", str(clone), "-b", "wt")
    assert discover(clone).project_id == first and first.startswith("lab-")


def test_reference_extraction_helpers():
    assert refs_from_text("Fix parser (#12), see #7 and org/repo#9") == ["gh:12", "gh:7"]
    assert refs_from_branch("feature/41-csv-validation") == ["gh:41"]
    assert refs_from_branch("issue-8-thing") == ["gh:8"]
    assert refs_from_branch("release-2024") == []

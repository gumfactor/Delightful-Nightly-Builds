from worklog.git_collector import collect_branches, collect_commits, collect_tags
from worklog.project import run_git


def test_collect_commits_returns_all_commits(git_repo):
    commits = collect_commits(str(git_repo), "main")
    assert len(commits) == 2
    subjects = {c.subject for c in commits}
    assert subjects == {"Initial commit", "Add app.py"}


def test_collect_commits_includes_changed_files(git_repo):
    commits = collect_commits(str(git_repo), "main")
    by_subject = {c.subject: c for c in commits}
    assert "app.py" in by_subject["Add app.py"].files
    assert "README.md" in by_subject["Initial commit"].files


def test_collect_commits_has_full_sha(git_repo):
    commits = collect_commits(str(git_repo), "main")
    for commit in commits:
        assert len(commit.sha) == 40


def test_collect_commits_oldest_first(git_repo):
    commits = collect_commits(str(git_repo), "main")
    assert [c.subject for c in commits] == ["Initial commit", "Add app.py"]


def test_collect_branches(git_repo):
    run_git(["checkout", "-q", "-b", "feature/x"], cwd=str(git_repo))
    branches = collect_branches(str(git_repo))
    names = {b.name for b in branches}
    assert "main" in names
    assert "feature/x" in names


def test_collect_tags(git_repo):
    run_git(["tag", "v1.0.0"], cwd=str(git_repo))
    tags = collect_tags(str(git_repo))
    assert any(t.name == "v1.0.0" for t in tags)


def test_collect_tags_empty_when_none(git_repo):
    assert collect_tags(str(git_repo)) == []


def test_collect_commits_on_feature_branch_excludes_shared_main_history(git_repo):
    from conftest import checkout_new_branch, commit as make_commit

    checkout_new_branch(git_repo, "feature/x")
    make_commit(git_repo, "feature.txt", "content\n", "Feature-only commit")

    feature_commits = collect_commits(str(git_repo), "feature/x")
    subjects = {c.subject for c in feature_commits}
    assert subjects == {"Feature-only commit"}
    assert "Initial commit" not in subjects


def test_collect_commits_on_default_branch_returns_full_history(git_repo):
    from conftest import checkout_new_branch, commit as make_commit

    checkout_new_branch(git_repo, "feature/x")
    make_commit(git_repo, "feature.txt", "content\n", "Feature-only commit")

    main_commits = collect_commits(str(git_repo), "main")
    subjects = {c.subject for c in main_commits}
    assert subjects == {"Initial commit", "Add app.py"}

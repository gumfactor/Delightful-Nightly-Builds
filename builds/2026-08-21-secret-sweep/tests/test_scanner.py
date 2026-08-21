from src import scanner

AWS_KEY = "AKIAABCDEFGHIJKLMNOP"


def test_working_tree_scan_finds_secret_in_tracked_file(git_repo):
    git_repo.write("config.py", f'AWS_KEY = "{AWS_KEY}"\n')
    git_repo.commit_all("add config")

    findings = scanner.scan_working_tree(git_repo.as_posix())

    assert len(findings) == 1
    f = findings[0]
    assert f["pattern_name"] == "AWS Access Key ID"
    assert f["severity"] == "critical"
    assert f["scope"] == "working-tree"
    assert AWS_KEY not in f["masked_preview"]


def test_working_tree_scan_respects_gitignore(git_repo):
    git_repo.write(".gitignore", "ignored.py\n")
    git_repo.write("ignored.py", f'AWS_KEY = "{AWS_KEY}"\n')
    git_repo.commit_all("add gitignore")

    findings = scanner.scan_working_tree(git_repo.as_posix())

    assert findings == []


def test_history_scan_flags_removed_secret_as_high_severity(git_repo):
    git_repo.write("config.py", f'AWS_KEY = "{AWS_KEY}"\n')
    git_repo.commit_all("oops, committed a key")
    git_repo.remove("config.py")
    git_repo.write("config.py", "AWS_KEY = os.environ['AWS_KEY']\n")
    git_repo.commit_all("remove hardcoded key")

    history_findings = scanner.scan_history(git_repo.as_posix())
    tree_findings = scanner.scan_working_tree(git_repo.as_posix())

    assert tree_findings == []  # no longer in the working tree
    assert len(history_findings) == 1
    assert history_findings[0]["severity"] == "high"
    assert history_findings[0]["scope"] == "history"


def test_history_scan_flags_still_present_secret_as_critical(git_repo):
    git_repo.write("config.py", f'AWS_KEY = "{AWS_KEY}"\n')
    git_repo.commit_all("add key")
    git_repo.write("readme.md", "unrelated change\n")
    git_repo.commit_all("unrelated commit")

    history_findings = scanner.scan_history(git_repo.as_posix())

    assert len(history_findings) == 1
    assert history_findings[0]["severity"] == "critical"


def test_history_scan_on_repo_with_no_commits_returns_empty(empty_git_repo):
    assert scanner.scan_history(empty_git_repo.as_posix()) == []


def test_scan_multiple_aggregates_across_repos_and_skips_non_git_dir(git_repo, tmp_path):
    git_repo.write("secrets.py", f'AWS_KEY = "{AWS_KEY}"\n')
    git_repo.commit_all("add key")

    non_git_dir = tmp_path / "not_a_repo"
    non_git_dir.mkdir()

    findings = scanner.scan_multiple([git_repo.as_posix(), str(non_git_dir)])

    assert len(findings) == 1
    assert findings[0]["repo_name"] == git_repo.path.name

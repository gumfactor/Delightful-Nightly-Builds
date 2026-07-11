import json

import pytest

from worklog.cli import main
from worklog.ledger import Ledger
from worklog.project import discover_project

from conftest import commit as make_commit


def test_sync_twice_produces_no_duplicates(git_repo, tmp_path, capsys):
    data_dir = str(tmp_path / "data")
    exit_code = main(["--repo", str(git_repo), "--data-dir", data_dir, "sync", "--no-github"])
    assert exit_code == 0
    project = discover_project(str(git_repo))
    ledger = Ledger(data_dir)
    first_count = len(ledger.events_for_project(project.project_id))

    exit_code = main(["--repo", str(git_repo), "--data-dir", data_dir, "sync", "--no-github"])
    assert exit_code == 0
    second_count = len(ledger.events_for_project(project.project_id))
    assert first_count == second_count
    assert first_count > 0


def test_sync_on_non_git_directory_fails_cleanly(tmp_path, capsys):
    plain_dir = tmp_path / "plain"
    plain_dir.mkdir()
    exit_code = main(["--repo", str(plain_dir), "sync", "--no-github"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "error" in captured.err.lower()


def test_checkpoint_ingestion_end_to_end(git_repo, tmp_path, capsys):
    data_dir = str(tmp_path / "data")
    main(["--repo", str(git_repo), "--data-dir", data_dir, "sync", "--no-github"])

    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "provider": "claude",
                "objective": "Investigate flaky test",
                "decisions": [{"summary": "Retry is not the fix", "reason": "masks a real race condition"}],
                "next_steps": ["Add a deterministic repro"],
            }
        )
    )

    exit_code = main(
        ["--repo", str(git_repo), "--data-dir", data_dir, "checkpoint", "--from-file", str(checkpoint_path)]
    )
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "ingested" in captured.out.lower()

    exit_code = main(["--repo", str(git_repo), "--data-dir", data_dir, "why", "race condition"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Retry is not the fix" in captured.out


def test_checkpoint_rejects_malformed_file(git_repo, tmp_path, capsys):
    data_dir = str(tmp_path / "data")
    main(["--repo", str(git_repo), "--data-dir", data_dir, "sync", "--no-github"])

    bad_checkpoint = tmp_path / "bad.json"
    bad_checkpoint.write_text(json.dumps({"schema_version": 1}))  # missing provider/objective

    exit_code = main(
        ["--repo", str(git_repo), "--data-dir", data_dir, "checkpoint", "--from-file", str(bad_checkpoint)]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "invalid checkpoint" in captured.err.lower()


def test_checkpoint_rejects_missing_file(git_repo, tmp_path, capsys):
    data_dir = str(tmp_path / "data")
    main(["--repo", str(git_repo), "--data-dir", data_dir, "sync", "--no-github"])
    exit_code = main(
        ["--repo", str(git_repo), "--data-dir", data_dir, "checkpoint", "--from-file", str(tmp_path / "nope.json")]
    )
    assert exit_code == 1


def test_workstreams_command_lists_output(git_repo, tmp_path, capsys):
    data_dir = str(tmp_path / "data")
    main(["--repo", str(git_repo), "--data-dir", data_dir, "sync", "--no-github"])
    exit_code = main(["--repo", str(git_repo), "--data-dir", data_dir, "workstreams"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "events]" in captured.out


def test_standup_command_runs(git_repo, tmp_path, capsys):
    data_dir = str(tmp_path / "data")
    main(["--repo", str(git_repo), "--data-dir", data_dir, "sync", "--no-github"])
    exit_code = main(["--repo", str(git_repo), "--data-dir", data_dir, "standup", "--since", "7d"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Standup" in captured.out


def test_resume_command_runs_without_workstream_arg(git_repo, tmp_path, capsys):
    data_dir = str(tmp_path / "data")
    main(["--repo", str(git_repo), "--data-dir", data_dir, "sync", "--no-github"])
    exit_code = main(["--repo", str(git_repo), "--data-dir", data_dir, "resume"])
    assert exit_code == 0


def test_show_event_missing_returns_error(git_repo, tmp_path, capsys):
    data_dir = str(tmp_path / "data")
    main(["--repo", str(git_repo), "--data-dir", data_dir, "sync", "--no-github"])
    exit_code = main(["--repo", str(git_repo), "--data-dir", data_dir, "show-event", "nonexistent"])
    assert exit_code == 1


def test_search_command_finds_commit(git_repo, tmp_path, capsys):
    data_dir = str(tmp_path / "data")
    main(["--repo", str(git_repo), "--data-dir", data_dir, "sync", "--no-github"])
    exit_code = main(["--repo", str(git_repo), "--data-dir", data_dir, "search", "app.py"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Add app.py" in captured.out


def test_sync_correlates_branch_commits_to_earlier_issue_reference(git_repo, tmp_path, capsys):
    # Regression: an issue-referencing commit followed by a plain commit on the same branch
    # must end up in the same workstream, regardless of git log's newest-first order.
    from conftest import checkout_new_branch

    checkout_new_branch(git_repo, "feature/csv-validation")
    make_commit(git_repo, "issue.txt", "a\n", "Start work on validation (#41)")
    make_commit(git_repo, "more.txt", "b\n", "Follow-up commit, no issue ref")

    data_dir = str(tmp_path / "data")
    main(["--repo", str(git_repo), "--data-dir", data_dir, "sync", "--no-github"])

    exit_code = main(["--repo", str(git_repo), "--data-dir", data_dir, "workstreams"])
    assert exit_code == 0
    captured = capsys.readouterr()
    # Both commits should land in one workstream (3 events: 2 pre-existing + follow-up on the
    # issue-anchored workstream), not split into a second branch-only workstream.
    assert "Issue #41" in captured.out
    assert "branch-feature-csv-validation" not in captured.out


def test_sync_reports_github_skipped_without_remote(git_repo, tmp_path, capsys):
    data_dir = str(tmp_path / "data")
    exit_code = main(["--repo", str(git_repo), "--data-dir", data_dir, "sync"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "GitHub: skipped" in captured.out

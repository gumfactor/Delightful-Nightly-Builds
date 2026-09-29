import json

import pytest

from conftest import make_fake_github
from worklog import cli, ghcollect


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("WORKLOG_DB", str(tmp_path / "ledger.db"))


def run(repo, *args, capsys):
    code = cli.main(["-C", str(repo.root), *args])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def fake_gh(monkeypatch, repo, **kw):
    head = repo.git("rev-parse", "feature/41-csv-validation")
    monkeypatch.setattr(ghcollect, "make_fetch", lambda token: make_fake_github(head, **kw))


def test_sync_is_idempotent_in_git_only_mode(scenario, capsys):
    _, out1, _ = run(scenario, "sync", "--no-github", capsys=capsys)
    _, out2, _ = run(scenario, "sync", "--no-github", capsys=capsys)
    assert "git: 4 new" in out1 and "git: 0 new, 4 unchanged" in out2 and "Git-only" in out2


def test_github_failure_degrades_to_git_only(gh_repo, monkeypatch, capsys):
    def broken(token):
        def fetch(url):
            raise ghcollect.GitHubUnavailable("GitHub returned HTTP 403")
        return fetch
    monkeypatch.setattr(ghcollect, "make_fetch", broken)
    code, out, _ = run(gh_repo, "sync", capsys=capsys)
    assert code == 0 and "github: skipped" in out and "Git-only" in out
    assert "feature/41-csv-validation" in run(gh_repo, "workstreams", capsys=capsys)[1]


def test_full_flow_groups_git_github_and_agent_into_one_workstream(gh_repo, monkeypatch, capsys, tmp_path):
    fake_gh(monkeypatch, gh_repo, merged=False)
    run(gh_repo, "sync", capsys=capsys)
    cp = tmp_path / "cp.json"
    cp.write_text(json.dumps({"provider": "codex", "session_id": "s1", "timestamp": "2026-09-03T14:00:00Z",
                              "objective": "Add CSV validation", "source_refs": [{"pr": "52"}],
                              "next_steps": ["Add malformed-row fixtures"],
                              "decisions": [{"summary": "Reject automatic type coercion", "reason": "Corrupts ids"}]}))
    assert run(gh_repo, "checkpoint", "--from-file", str(cp), capsys=capsys)[0] == 0
    _, out, _ = run(gh_repo, "--json", "workstreams", capsys=capsys)
    csv_ws = [w for w in json.loads(out) if w["title"] == "Add CSV validation"]
    assert len(csv_ws) == 1 and csv_ws[0]["events"] >= 8 and csv_ws[0]["status"] == "blocked"  # failing CI
    _, tl, _ = run(gh_repo, "timeline", csv_ws[0]["id"], capsys=capsys)
    for expected in ("commit", "pr ", "issue", "checkpoint", "ci", "review", "shared gh:41"):
        assert expected in tl


def test_resync_after_full_flow_adds_nothing(gh_repo, monkeypatch, capsys):
    fake_gh(monkeypatch, gh_repo, merged=True)
    run(gh_repo, "sync", capsys=capsys)
    _, out, _ = run(gh_repo, "sync", capsys=capsys)
    assert "git: 0 new" in out and "github: 0 new" in out


def test_merged_pr_marks_workstream_completed_and_standup_lists_it(gh_repo, monkeypatch, capsys):
    fake_gh(monkeypatch, gh_repo, merged=True, ci_conclusion="success")
    run(gh_repo, "sync", capsys=capsys)
    _, out, _ = run(gh_repo, "standup", "--since", "2026-09-01", capsys=capsys)
    completed = out.split("## Completed")[1].split("## In progress")[0]
    assert "CSV" in completed or "csv" in completed


def test_note_blocker_then_resolve_changes_status(scenario, capsys):
    run(scenario, "sync", "--no-github", capsys=capsys)
    _, out, _ = run(scenario, "--json", "workstreams", capsys=capsys)
    ws_id = next(w["id"] for w in json.loads(out) if "41" in w["title"])
    _, out, _ = run(scenario, "--json", "note", "--type", "blocker", "--text", "Waiting on lab data",
                    "--workstream", ws_id, capsys=capsys)
    blocker_id = json.loads(out)["id"]
    assert "blocked" in run(scenario, "workstreams", "--status", "blocked", capsys=capsys)[1]
    run(scenario, "resolve", blocker_id, capsys=capsys)
    assert "blocked" not in run(scenario, "workstreams", "--status", "blocked", capsys=capsys)[1].split("\n", 1)[1]


def test_rename_split_and_show_event(scenario, capsys):
    run(scenario, "sync", "--no-github", capsys=capsys)
    run(scenario, "rename", "csv-validation", "CSV validation rollout", capsys=capsys)
    assert "CSV validation rollout" in run(scenario, "workstreams", capsys=capsys)[1]
    sha = scenario.git("rev-parse", "feature/41-csv-validation")
    _, shown, _ = run(scenario, "show-event", sha[:10], capsys=capsys)
    assert json.loads(shown)["ref"] == sha
    run(scenario, "split", sha[:10], capsys=capsys)
    assert run(scenario, "--json", "workstreams", capsys=capsys)[1].count('"id"') == 4


def test_search_finds_events_by_file_and_summary(scenario, capsys):
    run(scenario, "sync", "--no-github", capsys=capsys)
    assert "Update docs" in run(scenario, "search", "docs/guide", capsys=capsys)[1]
    assert run(scenario, "search", "zzz-none", capsys=capsys)[1].strip() == "no matches"


def test_purge_requires_confirmation_and_rebuilds_from_sync(scenario, capsys):
    run(scenario, "sync", "--no-github", capsys=capsys)
    code, _, err = run(scenario, "purge", capsys=capsys)
    assert code == 2 and "--yes" in err
    run(scenario, "purge", "--yes", capsys=capsys)
    assert "No workstreams" in run(scenario, "workstreams", capsys=capsys)[1]
    run(scenario, "sync", "--no-github", capsys=capsys)
    assert "feature/41" in run(scenario, "workstreams", capsys=capsys)[1]


def test_errors_are_clean_messages_with_exit_code_2(tmp_path, capsys):
    code = cli.main(["-C", str(tmp_path), "sync"])
    assert code == 2 and "not inside a git repository" in capsys.readouterr().err


def test_resume_without_data_and_unknown_workstream_error_cleanly(scenario, capsys):
    assert run(scenario, "resume", capsys=capsys)[0] == 2
    run(scenario, "sync", "--no-github", capsys=capsys)
    code, _, err = run(scenario, "resume", "nonexistent-thing", capsys=capsys)
    assert code == 2 and "no unique workstream" in err


def test_ledger_lives_inside_git_dir_by_default_and_leaves_tree_clean(scenario, monkeypatch, capsys):
    monkeypatch.delenv("WORKLOG_DB")
    run(scenario, "sync", "--no-github", capsys=capsys)
    assert (scenario.root / ".git" / "worklog" / "ledger.db").exists()
    assert scenario.git("status", "--porcelain") == ""


def test_hook_end_to_end_via_cli(scenario, monkeypatch, capsys, tmp_path):
    import io
    transcript = tmp_path / "s.jsonl"
    transcript.write_text(json.dumps({"type": "user", "timestamp": "2026-09-02T09:00:00Z",
                                      "message": {"content": "Add CSV validation"}}) + "\n")
    payload = {"session_id": "abc", "transcript_path": str(transcript), "cwd": str(scenario.root)}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    assert cli.main(["hook"]) == 0
    assert "updated" in capsys.readouterr().out
    run(scenario, "sync", "--no-github", capsys=capsys)
    assert "Add CSV validation" in run(scenario, "workstreams", capsys=capsys)[1]

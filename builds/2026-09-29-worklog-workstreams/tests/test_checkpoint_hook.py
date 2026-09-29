import json

import pytest

from worklog import checkpoint, hook
from worklog.cli import cmd_hook
from worklog.project import WorklogError, discover


def _cp(**over):
    base = {"provider": "Codex", "session_id": "s1", "timestamp": "2026-09-03T14:30:00Z",
            "objective": "Add CSV validation", "accomplished": ["Added schema checks"],
            "decisions": [{"summary": "Reject automatic type coercion", "reason": "Can corrupt identifiers",
                           "rejected": ["Coerce to int"]}],
            "unresolved": ["Blank optional columns?"], "next_steps": ["Add malformed-row fixtures"],
            "validation": [{"command": "pytest", "result": "passed"}], "files": ["src/validation.py"]}
    base.update(over)
    return base


def test_valid_checkpoint_is_normalised(project):
    cp = checkpoint.normalise(_cp())
    assert cp["provider"] == "codex" and cp["decisions"][0]["rejected"] == ["Coerce to int"]


@pytest.mark.parametrize("bad, message", [
    ({"provider": ""}, "provider"), ({"objective": " "}, "objective"), ({"timestamp": "yesterday-ish"}, "timestamp"),
    ({"schema_version": 9}, "schema_version"), ({"decisions": [{"reason": "x"}]}, "summary"),
    ({"source_refs": ["abc"]}, "mapping"), ({"status": "weird"}, "status")])
def test_invalid_checkpoints_are_rejected_with_clear_errors(bad, message):
    with pytest.raises(WorklogError, match=message):
        checkpoint.normalise(_cp(**bad))


def test_capture_creates_checkpoint_and_decision_events_with_shared_keys(project, ledger):
    result = checkpoint.capture(project, ledger, _cp())
    events = ledger.events(project.project_id)
    assert result["decisions"] == 1 and {e["type"] for e in events} == {"checkpoint", "decision"}
    assert events[0]["keys"] == events[1]["keys"] and "obj:add-csv-validation" in events[0]["keys"]


def test_capture_resolves_short_commit_refs_and_fills_git_state(project, ledger, scenario):
    short = scenario.git("rev-parse", "--short", "feature/41-csv-validation")
    full = scenario.git("rev-parse", "feature/41-csv-validation")
    checkpoint.capture(project, ledger, _cp(source_refs=[{"commit": short}, {"issue": "#41"}]))
    cp = ledger.events(project.project_id, etype="checkpoint")[0]
    assert f"sha:{full}" in cp["keys"] and "gh:41" in cp["keys"]
    assert cp["metadata"]["branch"] == "main" and cp["metadata"]["head"] == scenario.git("rev-parse", "main")


def test_recapturing_a_session_updates_in_place_and_drops_removed_decisions(project, ledger):
    checkpoint.capture(project, ledger, _cp())
    checkpoint.capture(project, ledger, _cp(decisions=[], accomplished=["More"]))
    events = ledger.events(project.project_id)
    assert [e["type"] for e in events] == ["checkpoint"]


def test_secrets_in_checkpoints_are_redacted(project, ledger):
    checkpoint.capture(project, ledger, _cp(accomplished=["used token=abcdef123456 to call API"]))
    assert "abcdef123456" not in json.dumps(ledger.events(project.project_id))


def test_blockers_make_checkpoint_blocked(project, ledger):
    result = checkpoint.capture(project, ledger, _cp(blockers=["Waiting on data access"]))
    assert result["status"] == "blocked"


def test_yaml_and_json_files_load(tmp_path):
    yaml = pytest.importorskip("yaml")
    path = tmp_path / "cp.yaml"
    path.write_text(yaml.safe_dump(_cp()))
    assert checkpoint.load_file(path)["objective"] == "Add CSV validation"
    bad = tmp_path / "cp.json"
    bad.write_text("{nope")
    with pytest.raises(WorklogError, match="invalid JSON"):
        checkpoint.load_file(bad)


def _transcript(tmp_path, root):
    lines = [
        {"type": "user", "timestamp": "2026-09-02T09:00:00Z", "message": {"role": "user", "content": [
            {"type": "text", "text": "<system-reminder>ignore</system-reminder>"}]}},
        {"type": "user", "timestamp": "2026-09-02T09:01:00Z", "message": {"role": "user",
         "content": "Add CSV validation\nplease be careful with ids"}},
        {"type": "assistant", "timestamp": "2026-09-02T09:02:00Z", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "Edit", "input": {"file_path": str(root / "src/validation.py")}},
            {"type": "tool_use", "id": "t2", "name": "Edit", "input": {"file_path": "/etc/passwd"}},
            {"type": "tool_use", "id": "t3", "name": "Bash", "input": {"command": "python -m pytest tests/ -q"}},
            {"type": "tool_use", "id": "t4", "name": "Bash", "input": {"command": "ls"}}]}},
        {"type": "user", "timestamp": "2026-09-02T09:05:00Z", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t3", "is_error": True, "content": "1 failed"}]}},
    ]
    path = tmp_path / "sess.jsonl"
    path.write_text("\n".join(json.dumps(x) for x in lines) + "\nnot json\n")
    return path


def test_transcript_parsing_extracts_metadata_only(project, tmp_path):
    parsed = hook.parse_transcript(_transcript(tmp_path, project.root), project.root)
    assert parsed["objective"] == "Add CSV validation"
    assert parsed["files"] == ["src/validation.py"]
    assert parsed["validation"] == [{"command": "python -m pytest tests/ -q", "result": "failed"}]
    assert parsed["last_ts"] == "2026-09-02T09:05:00Z"


def test_hook_records_in_progress_checkpoint_with_session_commits(project, ledger, tmp_path):
    payload = {"session_id": "sess-9", "transcript_path": str(_transcript(tmp_path, project.root)),
               "cwd": str(project.root)}
    hook.run_hook(project, ledger, json.dumps(payload))
    cp = ledger.events(project.project_id, etype="checkpoint")[0]
    assert cp["provider"] == "claude-code" and cp["status"] == "in_progress" and cp["metadata"]["auto"] is True
    assert any(k.startswith("sha:") for k in cp["keys"])  # commits made since the session started
    hook.run_hook(project, ledger, json.dumps(payload))  # Stop fires every turn: must not duplicate
    assert len(ledger.events(project.project_id, etype="checkpoint")) == 1


def test_hook_rejects_bad_payloads(project, ledger, tmp_path):
    with pytest.raises(WorklogError):
        hook.run_hook(project, ledger, "not json")
    with pytest.raises(WorklogError, match="transcript"):
        hook.run_hook(project, ledger, json.dumps({"transcript_path": str(tmp_path / "missing.jsonl")}))


def test_hook_command_never_fails_the_agent(monkeypatch, capsys, tmp_path):
    import io
    import argparse
    monkeypatch.setattr("sys.stdin", io.StringIO("garbage"))
    assert cmd_hook(argparse.Namespace(C=str(tmp_path))) == 0
    assert "skipped" in capsys.readouterr().err

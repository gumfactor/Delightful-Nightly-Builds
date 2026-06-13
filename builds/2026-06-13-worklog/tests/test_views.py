"""Tests for standup, resume, why, and workstream view renderers."""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.ledger import (
    init_schema,
    insert_event,
    insert_decision,
    upsert_workstream,
    assign_workstream,
    make_event_id,
)
from src.views import render_standup, render_why, render_workstreams, render_events


@pytest.fixture
def populated_db(tmp_path):
    """A DB with commits, a checkpoint, a decision, and workstream assignments."""
    db_path = tmp_path / "test.db"
    init_schema(db_path)

    # Insert a commit event
    commit_evt = {
        "id": make_event_id("git", "abc123def456", "commit"),
        "timestamp": "2026-06-13T08:00:00Z",
        "project_id": "test-proj",
        "type": "commit",
        "actor_kind": "human",
        "actor_name": "dev",
        "summary": "Add CSV validation feature",
        "status": "completed",
        "workstream_id": "ws_csv",
        "provider": "git",
        "source_ref": "abc123def456",
        "source_url": None,
        "metadata": {"sha": "abc123def456", "files_changed": ["src/validate.py"]},
    }
    insert_event(db_path, commit_evt)

    # Insert a checkpoint event
    ckpt_evt = {
        "id": "evt_ckpt_test001",
        "timestamp": "2026-06-13T09:00:00Z",
        "project_id": "test-proj",
        "type": "checkpoint",
        "actor_kind": "agent",
        "actor_name": "claude",
        "summary": "Add CSV validation",
        "status": "open",
        "workstream_id": "ws_csv",
        "provider": "agent",
        "source_ref": "claude:sess-1:abcdef",
        "source_url": None,
        "metadata": {
            "session_id": "sess-1",
            "accomplished": ["Added schema checks"],
            "unresolved": ["Blank column handling"],
            "next_steps": ["Add fixtures", "Write edge case tests"],
            "files": ["src/validate.py", "tests/test_validate.py"],
            "source_refs": [{"commit": "abc123def456"}],
        },
    }
    insert_event(db_path, ckpt_evt)

    # Insert a decision
    decision = {
        "id": "dec_coercion_001",
        "event_id": "evt_ckpt_test001",
        "workstream_id": "ws_csv",
        "summary": "Reject automatic type coercion",
        "reason": "Silent data corruption risk",
        "alternatives": json.dumps(["Auto-coerce to inferred type"]),
        "timestamp": "2026-06-13T09:00:00Z",
    }
    insert_decision(db_path, decision)

    # Create the workstream
    upsert_workstream(db_path, {
        "id": "ws_csv",
        "title": "CSV validation",
        "status": "active",
        "evidence": [{"signal": "issue_ref", "value": "issue:10", "confidence": "high"}],
    })

    return db_path, "test-proj"


@pytest.fixture
def git_repo(tmp_path):
    """Minimal git repo for freshness checks (signing disabled for isolation)."""
    subprocess.run(["git", "init", "--initial-branch=main"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=tmp_path, capture_output=True)
    (tmp_path / "f.txt").write_text("x")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "-c", "commit.gpgsign=false", "commit", "-m", "init"],
                   cwd=tmp_path, capture_output=True)
    return tmp_path


class TestStandupView:
    def test_standup_contains_done_section(self, populated_db):
        db_path, project_id = populated_db
        output = render_standup(db_path, project_id, since_days=30)
        assert "Done" in output or "In Progress" in output or "Blocked" in output

    def test_standup_includes_commit_summary(self, populated_db):
        db_path, project_id = populated_db
        output = render_standup(db_path, project_id, since_days=30)
        assert "CSV validation" in output

    def test_standup_includes_next_steps_from_checkpoint(self, populated_db):
        db_path, project_id = populated_db
        output = render_standup(db_path, project_id, since_days=30)
        assert "Add fixtures" in output or "Next" in output

    def test_standup_empty_db_returns_no_events_message(self, tmp_path):
        db_path = tmp_path / "empty.db"
        init_schema(db_path)
        output = render_standup(db_path, "no-events-proj", since_days=1)
        assert "No events" in output


class TestWhyView:
    def test_why_finds_matching_decision(self, populated_db):
        db_path, project_id = populated_db
        output = render_why(db_path, project_id, "coercion")
        assert "coercion" in output.lower()
        assert "Silent data corruption" in output

    def test_why_shows_alternatives(self, populated_db):
        db_path, project_id = populated_db
        output = render_why(db_path, project_id, "coercion")
        assert "Auto-coerce" in output or "rejected" in output.lower() or "Rejected" in output

    def test_why_no_match_returns_not_found_message(self, populated_db):
        db_path, project_id = populated_db
        output = render_why(db_path, project_id, "nonexistent_term_xyz")
        assert "No decisions found" in output


class TestWorkstreamsView:
    def test_workstreams_lists_all_workstreams(self, populated_db):
        db_path, project_id = populated_db
        output = render_workstreams(db_path, project_id)
        assert "CSV validation" in output or "ws_csv" in output

    def test_workstreams_empty_db_shows_message(self, tmp_path):
        db_path = tmp_path / "empty.db"
        init_schema(db_path)
        output = render_workstreams(db_path, "empty-proj")
        assert "No workstreams" in output


class TestEventsView:
    def test_events_shows_events(self, populated_db):
        db_path, project_id = populated_db
        output = render_events(db_path, project_id, since_days=None, event_type=None, workstream_id=None)
        assert "commit" in output or "checkpoint" in output

    def test_events_filters_by_type(self, populated_db):
        db_path, project_id = populated_db
        output = render_events(db_path, project_id, since_days=None, event_type="commit", workstream_id=None)
        assert "checkpoint" not in output
        assert "commit" in output

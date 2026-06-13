"""Tests for agent checkpoint ingestion."""

import pytest
from src.checkpoint import parse_checkpoint, checkpoint_to_events, CheckpointError


VALID_YAML = """
schema_version: 1
timestamp: 2026-06-13T14:30:00Z
project_id: my-project
provider: claude
session_id: sess-abc123
objective: Add CSV validation
accomplished:
  - Added schema checks before ingestion
decisions:
  - summary: Reject automatic type coercion
    reason: Can silently corrupt identifiers
    alternatives:
      - Coerce to inferred type (rejected)
unresolved:
  - Decide whether blank optional columns are warnings
next_steps:
  - Add malformed-row fixtures
validation:
  - command: python -m pytest tests/ -v
    result: passed
files:
  - src/validation.py
source_refs:
  - commit: abc123def456
"""


class TestParseCheckpoint:
    def test_valid_checkpoint_parses_correctly(self):
        data = parse_checkpoint(VALID_YAML)
        assert data["objective"] == "Add CSV validation"
        assert data["provider"] == "claude"
        assert len(data["decisions"]) == 1

    def test_invalid_schema_version_raises(self):
        bad = VALID_YAML.replace("schema_version: 1", "schema_version: 99")
        with pytest.raises(CheckpointError, match="Unsupported schema_version"):
            parse_checkpoint(bad)

    def test_missing_objective_raises(self):
        bad = VALID_YAML.replace("objective: Add CSV validation", "")
        with pytest.raises(CheckpointError, match="objective"):
            parse_checkpoint(bad)

    def test_missing_provider_raises(self):
        bad = VALID_YAML.replace("provider: claude", "")
        with pytest.raises(CheckpointError, match="provider"):
            parse_checkpoint(bad)

    def test_invalid_yaml_raises(self):
        with pytest.raises(CheckpointError, match="Invalid YAML"):
            parse_checkpoint(":\tnot: valid: yaml: {{{")

    def test_non_mapping_raises(self):
        with pytest.raises(CheckpointError, match="mapping"):
            parse_checkpoint("- item1\n- item2")


class TestCheckpointToEvents:
    def test_produces_one_event_per_checkpoint(self):
        data = parse_checkpoint(VALID_YAML)
        events, decisions = checkpoint_to_events(data, "test-proj")
        assert len(events) == 1
        assert events[0]["type"] == "checkpoint"
        assert events[0]["project_id"] == "test-proj"

    def test_extracts_decisions(self):
        data = parse_checkpoint(VALID_YAML)
        events, decisions = checkpoint_to_events(data, "test-proj")
        assert len(decisions) == 1
        assert decisions[0]["summary"] == "Reject automatic type coercion"
        assert "identifiers" in decisions[0]["reason"]

    def test_decision_alternatives_stored(self):
        data = parse_checkpoint(VALID_YAML)
        _, decisions = checkpoint_to_events(data, "test-proj")
        assert len(decisions[0]["alternatives"]) == 1

    def test_deterministic_event_id(self):
        data = parse_checkpoint(VALID_YAML)
        events1, _ = checkpoint_to_events(data, "proj")
        events2, _ = checkpoint_to_events(data, "proj")
        assert events1[0]["id"] == events2[0]["id"]

    def test_status_is_open_when_unresolved(self):
        data = parse_checkpoint(VALID_YAML)
        events, _ = checkpoint_to_events(data, "test-proj")
        assert events[0]["status"] == "open"

    def test_status_is_completed_when_no_unresolved(self):
        no_unresolved = VALID_YAML.replace(
            "unresolved:\n  - Decide whether blank optional columns are warnings",
            ""
        )
        data = parse_checkpoint(no_unresolved)
        events, _ = checkpoint_to_events(data, "test-proj")
        assert events[0]["status"] == "completed"

    def test_failed_validation_sets_failed_status(self):
        failed_yaml = VALID_YAML.replace("result: passed", "result: failed")
        data = parse_checkpoint(failed_yaml)
        events, _ = checkpoint_to_events(data, "test-proj")
        assert events[0]["status"] == "failed"

    def test_no_decisions_in_checkpoint_produces_empty_list(self):
        no_decs = VALID_YAML.replace(
            "decisions:\n  - summary: Reject automatic type coercion\n    reason: Can silently corrupt identifiers\n    alternatives:\n      - Coerce to inferred type (rejected)",
            ""
        )
        data = parse_checkpoint(no_decs)
        _, decisions = checkpoint_to_events(data, "test-proj")
        assert decisions == []

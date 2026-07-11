import pytest

from worklog.checkpoint import CheckpointValidationError, validate_checkpoint

VALID = {
    "schema_version": 1,
    "provider": "codex",
    "objective": "Add CSV validation",
    "accomplished": ["Added schema checks"],
    "decisions": [{"summary": "Reject coercion", "reason": "Can corrupt identifiers"}],
    "unresolved": ["Blank columns policy"],
    "next_steps": ["Add fixtures"],
    "validation": [{"command": "pytest", "result": "passed"}],
    "files": ["src/validation.py"],
    "source_refs": [{"commit": "abc123"}],
}


def test_validate_checkpoint_happy_path():
    checkpoint = validate_checkpoint(VALID)
    assert checkpoint.provider == "codex"
    assert checkpoint.objective == "Add CSV validation"
    assert len(checkpoint.decisions) == 1


def test_validate_checkpoint_missing_required_field():
    data = dict(VALID)
    del data["objective"]
    with pytest.raises(CheckpointValidationError):
        validate_checkpoint(data)


def test_validate_checkpoint_wrong_schema_version():
    data = dict(VALID, schema_version=2)
    with pytest.raises(CheckpointValidationError):
        validate_checkpoint(data)


def test_validate_checkpoint_empty_provider():
    data = dict(VALID, provider="   ")
    with pytest.raises(CheckpointValidationError):
        validate_checkpoint(data)


def test_validate_checkpoint_not_a_dict():
    with pytest.raises(CheckpointValidationError):
        validate_checkpoint(["not", "a", "dict"])


def test_validate_checkpoint_bad_decision_shape():
    data = dict(VALID, decisions=[{"reason": "no summary"}])
    with pytest.raises(CheckpointValidationError):
        validate_checkpoint(data)


def test_validate_checkpoint_bad_validation_shape():
    data = dict(VALID, validation=[{"command": "pytest"}])  # missing 'result'
    with pytest.raises(CheckpointValidationError):
        validate_checkpoint(data)


def test_validate_checkpoint_defaults_fill_in():
    minimal = {"schema_version": 1, "provider": "claude", "objective": "Do a thing"}
    checkpoint = validate_checkpoint(minimal)
    assert checkpoint.accomplished == []
    assert checkpoint.decisions == []
    assert checkpoint.timestamp  # auto-filled


def test_validate_checkpoint_redacts_secrets_in_objective():
    data = dict(VALID, objective="Use key sk-abcdefghijklmnopqrstuvwx to authenticate")
    checkpoint = validate_checkpoint(data)
    assert "sk-abcdefghijklmnopqrstuvwx" not in checkpoint.objective
    assert "[REDACTED]" in checkpoint.objective


def test_validate_checkpoint_redacts_secrets_in_decision_reason():
    data = dict(VALID)
    data["decisions"] = [{"summary": "ok", "reason": "token ghp_1234567890abcdefghijklmnop leaked"}]
    checkpoint = validate_checkpoint(data)
    assert "ghp_1234567890abcdefghijklmnop" not in checkpoint.decisions[0]["reason"]


def test_validate_checkpoint_invalid_timestamp():
    data = dict(VALID, timestamp="not-a-date")
    with pytest.raises(CheckpointValidationError):
        validate_checkpoint(data)

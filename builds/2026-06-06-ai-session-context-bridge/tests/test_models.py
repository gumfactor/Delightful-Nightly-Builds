"""Tests for Session model creation, serialization, and defaults."""

from src.models import Session


def test_session_create_generates_nonempty_id():
    s = Session.create(project="proj", summary="test summary")
    assert s.id
    assert len(s.id) == 8


def test_session_create_sets_utc_timestamp():
    s = Session.create(project="proj", summary="test summary")
    # ISO 8601 UTC: contains "T" separator and ends with "Z"
    assert "T" in s.timestamp
    assert s.timestamp.endswith("Z")
    # Year should be present
    assert s.timestamp[:4].isdigit()


def test_session_to_dict_from_dict_roundtrip():
    original = Session.create(
        project="neuroscience-lab",
        summary="Ran second-level GLM analysis on fMRI data",
        context="Used FSL for preprocessing; 42 subjects passed QC",
        next_steps=["Run ROI analysis", "Write up methods"],
        files=["scripts/glm_level2.py", "data/subject_list.txt"],
        tags=["fmri", "glm", "analysis"],
    )
    restored = Session.from_dict(original.to_dict())

    assert restored.id == original.id
    assert restored.timestamp == original.timestamp
    assert restored.project == original.project
    assert restored.summary == original.summary
    assert restored.context == original.context
    assert restored.next_steps == original.next_steps
    assert restored.files == original.files
    assert restored.tags == original.tags


def test_session_create_defaults_to_empty_collections():
    s = Session.create(project="proj", summary="minimal entry")
    assert s.next_steps == []
    assert s.files == []
    assert s.tags == []
    assert s.context == ""


def test_session_from_dict_handles_missing_optional_fields():
    """from_dict should tolerate storage records written before optional fields existed."""
    minimal = {
        "id": "abcd1234",
        "timestamp": "2026-06-06T08:00:00Z",
        "project": "test",
        "summary": "bare minimum record",
    }
    s = Session.from_dict(minimal)
    assert s.context == ""
    assert s.next_steps == []
    assert s.files == []
    assert s.tags == []

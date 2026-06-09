"""Tests for handoff document generation."""

from src.models import Session
from src.handoff import generate_handoff


def make_session(
    project: str = "test-proj",
    summary: str = "test summary",
    context: str = "",
    next_steps: list | None = None,
    files: list | None = None,
    tags: list | None = None,
    timestamp: str | None = None,
) -> Session:
    s = Session.create(
        project=project,
        summary=summary,
        context=context,
        next_steps=next_steps or [],
        files=files or [],
        tags=tags or [],
    )
    if timestamp:
        # Replace the auto-generated timestamp with a known value for ordering tests
        return Session(
            id=s.id,
            timestamp=timestamp,
            project=s.project,
            summary=s.summary,
            context=s.context,
            next_steps=s.next_steps,
            files=s.files,
            tags=s.tags,
        )
    return s


def test_handoff_contains_project_name():
    sessions = [make_session(project="canada-list")]
    output = generate_handoff(sessions)
    assert "canada-list" in output


def test_handoff_contains_session_summary():
    sessions = [make_session(summary="Rebuilding the CSV ingestion pipeline from scratch")]
    output = generate_handoff(sessions)
    assert "Rebuilding the CSV ingestion pipeline from scratch" in output


def test_handoff_empty_session_list_is_graceful():
    output = generate_handoff([])
    assert "No sessions recorded" in output
    assert "# AI Session Handoff" in output


def test_handoff_empty_for_specific_project_is_graceful():
    sessions = [make_session(project="other-project")]
    output = generate_handoff(sessions, project="missing-project")
    assert "No sessions recorded" in output
    assert "missing-project" in output


def test_handoff_n_sessions_limits_included_sessions():
    """With n_sessions=2, a 5-session list should produce shorter output than n_sessions=5."""
    sessions = [
        make_session(summary=f"entry {i}", timestamp=f"2026-06-0{i+1}T10:00:00Z")
        for i in range(5)
    ]
    output_2 = generate_handoff(sessions, n_sessions=2)
    output_5 = generate_handoff(sessions, n_sessions=5)
    assert len(output_2) < len(output_5)


def test_handoff_includes_next_steps():
    sessions = [make_session(next_steps=["Implement refresh token rotation", "Write integration tests"])]
    output = generate_handoff(sessions)
    assert "Implement refresh token rotation" in output


def test_handoff_includes_files():
    sessions = [make_session(files=["src/auth.py", "tests/test_auth.py"])]
    output = generate_handoff(sessions)
    assert "src/auth.py" in output
    assert "tests/test_auth.py" in output


def test_handoff_includes_context():
    sessions = [make_session(context="Redis cache is invalidated on every upload trigger")]
    output = generate_handoff(sessions)
    assert "Redis cache is invalidated on every upload trigger" in output


def test_handoff_filters_to_project():
    sessions = [
        make_session(project="canada-list", summary="CSV work"),
        make_session(project="lab-admin", summary="Grant deadline"),
    ]
    output = generate_handoff(sessions, project="canada-list")
    assert "CSV work" in output
    assert "Grant deadline" not in output


def test_handoff_shows_recent_history_for_multiple_sessions():
    sessions = [
        make_session(summary="oldest work", timestamp="2026-06-04T10:00:00Z"),
        make_session(summary="middle work", timestamp="2026-06-05T10:00:00Z"),
        make_session(summary="latest work", timestamp="2026-06-06T10:00:00Z"),
    ]
    output = generate_handoff(sessions, n_sessions=3)
    # All three summaries should appear somewhere in the output
    assert "latest work" in output
    assert "middle work" in output
    assert "oldest work" in output


def test_handoff_has_expected_header():
    sessions = [make_session()]
    output = generate_handoff(sessions)
    assert output.startswith("# AI Session Handoff")

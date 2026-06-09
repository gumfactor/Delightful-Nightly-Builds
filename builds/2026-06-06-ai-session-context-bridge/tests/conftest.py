"""Shared pytest fixtures for ctxlog tests."""

import sys
from pathlib import Path

# Ensure the build root is on sys.path so `from src.X import Y` works
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.storage import Storage
from src.journal import Journal
from src.models import Session


@pytest.fixture
def tmp_storage(tmp_path: Path) -> Storage:
    return Storage(tmp_path / "sessions.json")


@pytest.fixture
def journal(tmp_storage: Storage) -> Journal:
    return Journal(tmp_storage)


@pytest.fixture
def sample_session() -> Session:
    """A pre-built session with realistic content for reuse in tests."""
    return Session.create(
        project="canada-list",
        summary="Rewrote the CSV ingestion pipeline to handle quoted commas",
        context="Parser now handles RFC 4180 edge cases. Redis cache invalidated on upload.",
        next_steps=["Add column validation", "Write integration tests", "Update docs"],
        files=["src/ingest.py", "src/parser.py", "tests/test_ingest.py"],
        tags=["pipeline", "csv", "backend"],
    )

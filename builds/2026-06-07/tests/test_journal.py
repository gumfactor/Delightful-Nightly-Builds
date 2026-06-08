"""Tests for journal.append_entry — writes JSONL to a temp file."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.journal import append_entry


def test_append_creates_file(tmp_path):
    """append_entry creates the journal file if it doesn't exist."""
    journal = tmp_path / "journal.jsonl"
    append_entry(str(journal), {}, 24, "Nothing committed.\n")
    assert journal.exists()


def test_append_writes_valid_json(tmp_path):
    """Each line written is valid JSON with expected keys."""
    journal = tmp_path / "journal.jsonl"
    append_entry(str(journal), {}, 24, "Nothing committed.\n")
    line = journal.read_text().strip()
    data = json.loads(line)
    assert "timestamp" in data
    assert data["hours"] == 24
    assert data["commit_count"] == 0


def test_append_records_commits(tmp_path):
    """Commits are serialised correctly into the journal entry."""
    journal = tmp_path / "journal.jsonl"
    commits = {"my-repo": [{"hash": "abc12345", "message": "Fix bug", "source": "github"}]}
    append_entry(str(journal), commits, 24, "## Standup\n")
    data = json.loads(journal.read_text().strip())
    assert data["commit_count"] == 1
    assert "my-repo" in data["repos"]


def test_append_multiple_entries(tmp_path):
    """Multiple calls produce multiple lines (valid JSONL)."""
    journal = tmp_path / "journal.jsonl"
    append_entry(str(journal), {}, 24, "Nothing.\n")
    append_entry(str(journal), {}, 24, "Nothing.\n")
    lines = [l for l in journal.read_text().splitlines() if l.strip()]
    assert len(lines) == 2
    for line in lines:
        json.loads(line)  # must not raise


def test_append_creates_parent_directories(tmp_path):
    """append_entry creates missing parent directories."""
    journal = tmp_path / "deep" / "path" / "journal.jsonl"
    append_entry(str(journal), {}, 24, "Nothing.\n")
    assert journal.exists()

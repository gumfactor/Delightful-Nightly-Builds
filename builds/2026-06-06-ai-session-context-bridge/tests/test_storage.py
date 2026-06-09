"""Tests for Storage: loading, saving, appending, and directory creation."""

import json
from pathlib import Path

from src.storage import Storage
from src.models import Session


def test_load_empty_storage_returns_empty_list(tmp_path: Path):
    storage = Storage(tmp_path / "sessions.json")
    assert storage.load_all() == []


def test_empty_storage_creates_file(tmp_path: Path):
    path = tmp_path / "sessions.json"
    storage = Storage(path)
    storage.load_all()
    assert path.exists()


def test_append_then_load_roundtrip(tmp_path: Path):
    storage = Storage(tmp_path / "sessions.json")
    session = Session.create(project="myproj", summary="first entry")
    storage.append(session)

    loaded = storage.load_all()
    assert len(loaded) == 1
    assert loaded[0].id == session.id
    assert loaded[0].summary == session.summary
    assert loaded[0].project == session.project


def test_save_all_then_load_preserves_multiple_sessions(tmp_path: Path):
    storage = Storage(tmp_path / "sessions.json")
    s1 = Session.create(project="proj-a", summary="session one")
    s2 = Session.create(project="proj-b", summary="session two")
    storage.save_all([s1, s2])

    loaded = storage.load_all()
    assert len(loaded) == 2
    ids = {s.id for s in loaded}
    assert s1.id in ids
    assert s2.id in ids


def test_storage_creates_nested_parent_directories(tmp_path: Path):
    """Storage should auto-create any missing parent directories."""
    nested = tmp_path / "deep" / "nested" / "dir" / "sessions.json"
    storage = Storage(nested)
    storage.load_all()
    assert nested.exists()


def test_append_multiple_accumulates(tmp_path: Path):
    storage = Storage(tmp_path / "sessions.json")
    for i in range(3):
        storage.append(Session.create(project="proj", summary=f"entry {i}"))
    assert len(storage.load_all()) == 3


def test_save_all_overwrites_existing_data(tmp_path: Path):
    storage = Storage(tmp_path / "sessions.json")
    storage.append(Session.create(project="old", summary="old entry"))
    new_session = Session.create(project="new", summary="replacement")
    storage.save_all([new_session])

    loaded = storage.load_all()
    assert len(loaded) == 1
    assert loaded[0].project == "new"

import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from database import (
    add_project,
    get_all_recent_activity,
    get_last_activity_date,
    get_project,
    get_recent_activity,
    init_db,
    list_projects,
    log_activity,
    slugify,
    update_project_status,
)


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


def test_init_creates_tables(db_path):
    conn = sqlite3.connect(db_path)
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()
    assert "projects" in tables
    assert "activity_log" in tables


def test_add_project_returns_id(db_path):
    proj_id = add_project(db_path, "Canada List", "Canadian products", "business", [])
    assert isinstance(proj_id, int)
    assert proj_id > 0


def test_add_project_duplicate_raises(db_path):
    add_project(db_path, "Canada List", "desc", "business", [])
    with pytest.raises(Exception):
        add_project(db_path, "Canada List", "different desc", "code", [])


def test_get_project_by_slug(db_path):
    add_project(db_path, "My Lab", "neuroscience research", "lab", ["owner/repo1"])
    project = get_project(db_path, "my-lab")
    assert project is not None
    assert project["name"] == "My Lab"
    assert project["type"] == "lab"
    assert project["github_repos"] == ["owner/repo1"]
    assert project["status"] == "active"


def test_get_project_not_found(db_path):
    result = get_project(db_path, "nonexistent-slug")
    assert result is None


def test_list_projects_active_by_default(db_path):
    add_project(db_path, "Project A", "desc", "code", [])
    add_project(db_path, "Project B", "desc", "lab", [])
    projects = list_projects(db_path, status="active")
    assert len(projects) == 2


def test_list_projects_by_status(db_path):
    add_project(db_path, "Active One", "desc", "code", [])
    add_project(db_path, "Paused One", "desc", "writing", [])
    update_project_status(db_path, "paused-one", "paused")

    active = list_projects(db_path, status="active")
    paused = list_projects(db_path, status="paused")

    assert len(active) == 1
    assert active[0]["name"] == "Active One"
    assert len(paused) == 1
    assert paused[0]["name"] == "Paused One"


def test_list_all_projects(db_path):
    add_project(db_path, "P1", "desc", "code", [])
    add_project(db_path, "P2", "desc", "lab", [])
    update_project_status(db_path, "p1", "archived")

    all_projects = list_projects(db_path, status="all")
    assert len(all_projects) == 2


def test_log_activity_returns_id(db_path):
    proj_id = add_project(db_path, "Test Project", "desc", "code", [])
    result = log_activity(db_path, proj_id, "manual", "note", "Started feature X")
    assert result is not None
    assert isinstance(result, int)
    assert result > 0


def test_log_activity_duplicate_returns_none(db_path):
    proj_id = add_project(db_path, "Test Project", "desc", "code", [])
    log_activity(db_path, proj_id, "manual", "note", "Same note text")
    duplicate = log_activity(db_path, proj_id, "manual", "note", "Same note text")
    assert duplicate is None


def test_get_recent_activity_returns_entries(db_path):
    proj_id = add_project(db_path, "Test Project", "desc", "code", [])
    log_activity(db_path, proj_id, "manual", "note", "Note 1")
    log_activity(db_path, proj_id, "github", "commit", "Fix bug")
    acts = get_recent_activity(db_path, proj_id, days=30)
    assert len(acts) == 2


def test_get_last_activity_date_none_when_empty(db_path):
    proj_id = add_project(db_path, "Test Project", "desc", "code", [])
    assert get_last_activity_date(db_path, proj_id) is None


def test_get_last_activity_date_after_log(db_path):
    proj_id = add_project(db_path, "Test Project", "desc", "code", [])
    log_activity(db_path, proj_id, "manual", "note", "First note")
    last = get_last_activity_date(db_path, proj_id)
    assert last is not None
    assert "T" in last  # ISO timestamp


def test_get_all_recent_activity_joins_project_name(db_path):
    proj_id = add_project(db_path, "My Project", "desc", "code", [])
    log_activity(db_path, proj_id, "manual", "note", "Test note")
    acts = get_all_recent_activity(db_path, days=30)
    assert len(acts) == 1
    assert acts[0]["project_name"] == "My Project"
    assert acts[0]["project_slug"] == "my-project"


def test_update_project_status_returns_true(db_path):
    add_project(db_path, "Target", "desc", "code", [])
    result = update_project_status(db_path, "target", "paused")
    assert result is True
    p = get_project(db_path, "target")
    assert p["status"] == "paused"


def test_update_project_status_missing_slug(db_path):
    result = update_project_status(db_path, "no-such-slug", "archived")
    assert result is False


def test_slugify_basic():
    assert slugify("Canada List") == "canada-list"


def test_slugify_special_chars():
    assert slugify("My Project (v2)") == "my-project-v2"


def test_slugify_leading_trailing_hyphens():
    assert not slugify("  spaces  ").startswith("-")
    assert not slugify("  spaces  ").endswith("-")

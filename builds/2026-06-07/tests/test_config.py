"""Tests for config loading — no file I/O beyond temp files."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_config


def test_missing_config_returns_defaults(tmp_path):
    """A non-existent config file returns the default values."""
    cfg = load_config(tmp_path / "nonexistent.toml")
    assert cfg["hours"] == 24
    assert cfg["github_username"] == ""
    assert cfg["local_roots"] == []
    assert cfg["exclude_repos"] == []


def test_config_overrides_defaults(tmp_path):
    """Values in the config file override defaults."""
    cfg_file = tmp_path / "standup.toml"
    cfg_file.write_text('[standup]\ngithub_username = "gumfactor"\nhours = 48\n')
    cfg = load_config(cfg_file)
    assert cfg["github_username"] == "gumfactor"
    assert cfg["hours"] == 48


def test_unset_keys_keep_defaults(tmp_path):
    """Keys absent from the config file retain their default values."""
    cfg_file = tmp_path / "standup.toml"
    cfg_file.write_text('[standup]\ngithub_username = "gumfactor"\n')
    cfg = load_config(cfg_file)
    assert cfg["hours"] == 24
    assert cfg["format"] == "text"


def test_local_roots_parsed_as_list(tmp_path):
    """local_roots is parsed as a list of strings."""
    cfg_file = tmp_path / "standup.toml"
    cfg_file.write_text('[standup]\nlocal_roots = ["C:/Dev", "C:/Work"]\n')
    cfg = load_config(cfg_file)
    assert cfg["local_roots"] == ["C:/Dev", "C:/Work"]


def test_exclude_repos_parsed_as_list(tmp_path):
    """exclude_repos is parsed as a list of strings."""
    cfg_file = tmp_path / "standup.toml"
    cfg_file.write_text('[standup]\nexclude_repos = ["old-repo"]\n')
    cfg = load_config(cfg_file)
    assert cfg["exclude_repos"] == ["old-repo"]

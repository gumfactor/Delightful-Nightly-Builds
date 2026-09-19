import json
from pathlib import Path

import pytest

import main


@pytest.fixture
def config_path(tmp_path: Path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "topics": ["psychopathy", "stress cortisol"],
        "fiscal_year_start": 2020,
        "fiscal_year_end": 2024,
    }))
    return path


def test_parse_args_requires_a_subcommand():
    with pytest.raises(SystemExit):
        main.parse_args([])


def test_parse_args_sync_defaults():
    args = main.parse_args(["sync"])
    assert args.command == "sync"
    assert args.topics is None


def test_parse_args_report_with_ai_flag():
    args = main.parse_args(["report", "--ai"])
    assert args.command == "report"
    assert args.ai is True


def test_parse_args_report_without_ai_flag_defaults_false():
    args = main.parse_args(["report"])
    assert args.ai is False


def test_parse_args_rejects_fy_start_after_fy_end():
    with pytest.raises(ValueError):
        main.parse_args(["sync", "--fy-start", "2025", "--fy-end", "2020"])


def test_resolve_topics_and_years_reads_from_config(config_path):
    args = main.parse_args(["sync", "--config", str(config_path)])
    topics, fy_start, fy_end = main.resolve_topics_and_years(args)
    assert topics == ["psychopathy", "stress cortisol"]
    assert (fy_start, fy_end) == (2020, 2024)


def test_resolve_topics_and_years_topics_override_splits_and_strips(config_path):
    args = main.parse_args(["sync", "--config", str(config_path), "--topics", " empathy , grief "])
    topics, _, _ = main.resolve_topics_and_years(args)
    assert topics == ["empathy", "grief"]


def test_resolve_topics_and_years_fy_override(config_path):
    args = main.parse_args(["sync", "--config", str(config_path), "--fy-start", "2022"])
    _, fy_start, fy_end = main.resolve_topics_and_years(args)
    assert (fy_start, fy_end) == (2022, 2024)


def test_resolve_topics_and_years_raises_when_merged_range_invalid(tmp_path):
    bad_config = tmp_path / "config.json"
    bad_config.write_text(json.dumps({
        "topics": ["x"], "fiscal_year_start": 2020, "fiscal_year_end": 2021,
    }))
    args = main.parse_args(["sync", "--config", str(bad_config), "--fy-start", "2025"])
    with pytest.raises(ValueError):
        main.resolve_topics_and_years(args)

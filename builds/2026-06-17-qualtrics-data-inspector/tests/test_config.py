"""Tests for src/config.py — config file loading and merging."""

import argparse
import tempfile
import textwrap
from pathlib import Path

import pytest
from src.config import (
    load_config,
    apply_config_defaults,
    get_scales_from_config,
    get_attention_answers_from_config,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_toml(content: str) -> Path:
    """Write a TOML string to a temp file and return its path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".toml", delete=False, mode="w", encoding="utf-8")
    tmp.write(textwrap.dedent(content))
    tmp.flush()
    return Path(tmp.name)


def _make_parser():
    """Return a minimal argparse parser with all expected shared flags."""
    p = argparse.ArgumentParser()
    p.add_argument("--threshold", type=int, default=60)
    p.add_argument("--missing-warn", dest="missing_warn", type=float, default=0.05)
    p.add_argument("--missing-flag", dest="missing_flag", type=float, default=0.20)
    p.add_argument("--missing-respondent", dest="missing_respondent", type=float, default=0.20)
    p.add_argument("--outlier-z", dest="outlier_z", type=float, default=3.0)
    p.add_argument("--low-r", dest="low_r", type=float, default=0.20)
    p.add_argument("--no-conditions", dest="no_conditions", action="store_true", default=False)
    p.add_argument("--keep-incomplete", dest="keep_incomplete", action="store_true", default=False)
    p.add_argument("--keep-fast", dest="keep_fast", action="store_true", default=False)
    p.add_argument("--keep-straight-liners", dest="keep_straight_liners", action="store_true", default=False)
    p.add_argument("--exclude-high-missing", dest="exclude_high_missing", action="store_true", default=False)
    return p


# ── load_config ───────────────────────────────────────────────────────────────

class TestLoadConfig:
    def test_missing_file_returns_empty_dict(self, tmp_path):
        result = load_config(str(tmp_path / "nonexistent.toml"))
        assert result == {}

    def test_default_name_missing_returns_empty(self, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        result = load_config()
        assert result == {}

    def test_valid_toml_loaded(self):
        path = _write_toml("""
            [thresholds]
            fast_response_seconds = 90
        """)
        result = load_config(str(path))
        assert result["thresholds"]["fast_response_seconds"] == 90

    def test_invalid_toml_raises_value_error(self):
        path = _write_toml("this is not valid toml ===")
        with pytest.raises(ValueError, match="invalid TOML"):
            load_config(str(path))

    def test_empty_toml_returns_empty_dict(self):
        path = _write_toml("")
        result = load_config(str(path))
        assert result == {}

    def test_all_sections_parsed(self):
        path = _write_toml("""
            [thresholds]
            fast_response_seconds = 120

            [scales]
            PSS10 = ["Q1_1", "Q1_2"]

            [attention]
            ATTN1 = "4"

            [inspect]
            no_conditions = true

            [clean]
            keep_incomplete = true
        """)
        cfg = load_config(str(path))
        assert cfg["thresholds"]["fast_response_seconds"] == 120
        assert cfg["scales"]["PSS10"] == ["Q1_1", "Q1_2"]
        assert cfg["attention"]["ATTN1"] == "4"
        assert cfg["inspect"]["no_conditions"] is True
        assert cfg["clean"]["keep_incomplete"] is True


# ── apply_config_defaults ─────────────────────────────────────────────────────

class TestApplyConfigDefaults:
    def test_threshold_set_from_config(self):
        path = _write_toml("""
            [thresholds]
            fast_response_seconds = 90
        """)
        config = load_config(str(path))
        parser = _make_parser()
        apply_config_defaults(parser, config)
        args = parser.parse_args([])
        assert args.threshold == 90

    def test_missing_warn_set_from_config(self):
        path = _write_toml("""
            [thresholds]
            missing_column_warn = 0.10
        """)
        config = load_config(str(path))
        parser = _make_parser()
        apply_config_defaults(parser, config)
        args = parser.parse_args([])
        assert abs(args.missing_warn - 0.10) < 0.001

    def test_cli_flag_overrides_config(self):
        path = _write_toml("""
            [thresholds]
            fast_response_seconds = 90
        """)
        config = load_config(str(path))
        parser = _make_parser()
        apply_config_defaults(parser, config)
        args = parser.parse_args(["--threshold", "45"])
        assert args.threshold == 45

    def test_empty_config_leaves_defaults_unchanged(self):
        parser = _make_parser()
        apply_config_defaults(parser, {})
        args = parser.parse_args([])
        assert args.threshold == 60
        assert abs(args.missing_warn - 0.05) < 0.001

    def test_no_conditions_set_from_config(self):
        path = _write_toml("""
            [inspect]
            no_conditions = true
        """)
        config = load_config(str(path))
        parser = _make_parser()
        apply_config_defaults(parser, config)
        args = parser.parse_args([])
        assert args.no_conditions is True

    def test_clean_flags_set_from_config(self):
        path = _write_toml("""
            [clean]
            keep_incomplete = true
            exclude_high_missing = true
        """)
        config = load_config(str(path))
        parser = _make_parser()
        apply_config_defaults(parser, config)
        args = parser.parse_args([])
        assert args.keep_incomplete is True
        assert args.exclude_high_missing is True

    def test_partial_config_only_sets_present_keys(self):
        path = _write_toml("""
            [thresholds]
            fast_response_seconds = 45
        """)
        config = load_config(str(path))
        parser = _make_parser()
        apply_config_defaults(parser, config)
        args = parser.parse_args([])
        assert args.threshold == 45
        assert abs(args.missing_warn - 0.05) < 0.001  # unchanged


# ── get_scales_from_config ────────────────────────────────────────────────────

class TestGetScalesFromConfig:
    def test_returns_scales_dict(self):
        config = {"scales": {"PSS10": ["Q1_1", "Q1_2", "Q1_3"]}}
        result = get_scales_from_config(config)
        assert result == {"PSS10": ["Q1_1", "Q1_2", "Q1_3"]}

    def test_no_scales_section_returns_none(self):
        assert get_scales_from_config({}) is None

    def test_empty_scales_section_returns_none(self):
        assert get_scales_from_config({"scales": {}}) is None

    def test_filters_out_invalid_entries(self):
        config = {"scales": {"valid": ["Q1", "Q2"], "invalid": "not a list"}}
        result = get_scales_from_config(config)
        assert "valid" in result
        assert "invalid" not in result

    def test_multiple_scales(self):
        config = {
            "scales": {
                "PSS10": ["Q1_1", "Q1_2"],
                "STAI": ["Q2_1", "Q2_2"],
            }
        }
        result = get_scales_from_config(config)
        assert set(result.keys()) == {"PSS10", "STAI"}


# ── get_attention_answers_from_config ─────────────────────────────────────────

class TestGetAttentionAnswersFromConfig:
    def test_returns_string_dict(self):
        config = {"attention": {"ATTN1": "4", "ATTN2": "Strongly Agree"}}
        result = get_attention_answers_from_config(config)
        assert result == {"ATTN1": "4", "ATTN2": "Strongly Agree"}

    def test_no_attention_section_returns_none(self):
        assert get_attention_answers_from_config({}) is None

    def test_empty_attention_section_returns_none(self):
        assert get_attention_answers_from_config({"attention": {}}) is None

    def test_numeric_values_converted_to_strings(self):
        config = {"attention": {"ATTN1": 4}}
        result = get_attention_answers_from_config(config)
        assert result["ATTN1"] == "4"
        assert isinstance(result["ATTN1"], str)

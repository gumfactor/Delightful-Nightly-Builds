"""Tests for main.py — CLI argument parsing and validation."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import parse_args, validate_args
from parser import make_slug


def test_parse_args_all_required():
    args = parse_args([
        "--topic", "cortisol",
        "--course", "Stress and Coping",
        "--level", "undergrad",
        "--duration", "75",
    ])
    assert args.topic == "cortisol"
    assert args.course == "Stress and Coping"
    assert args.level == "undergrad"
    assert args.duration == 75


def test_parse_args_default_duration():
    args = parse_args([
        "--topic", "memory",
        "--course", "Cognitive Neuro",
        "--level", "graduate",
    ])
    assert args.duration == 75


def test_parse_args_default_output():
    args = parse_args([
        "--topic", "stress",
        "--course", "Coping",
        "--level", "undergrad",
    ])
    assert args.output == "output"


def test_parse_args_missing_topic_exits():
    with pytest.raises(SystemExit):
        parse_args(["--course", "Course", "--level", "undergrad"])


def test_parse_args_missing_course_exits():
    with pytest.raises(SystemExit):
        parse_args(["--topic", "Topic", "--level", "undergrad"])


def test_parse_args_missing_level_exits():
    with pytest.raises(SystemExit):
        parse_args(["--topic", "Topic", "--course", "Course"])


def test_parse_args_invalid_level_exits():
    with pytest.raises(SystemExit):
        parse_args([
            "--topic", "Topic",
            "--course", "Course",
            "--level", "phd",
        ])


def test_validate_args_empty_topic_raises():
    args = parse_args([
        "--topic", "   ",
        "--course", "Course",
        "--level", "undergrad",
    ])
    with pytest.raises(ValueError, match="topic"):
        validate_args(args)


def test_validate_args_empty_course_raises():
    args = parse_args([
        "--topic", "Stress",
        "--course", "   ",
        "--level", "undergrad",
    ])
    with pytest.raises(ValueError, match="course"):
        validate_args(args)


def test_validate_args_zero_duration_raises():
    args = parse_args([
        "--topic", "Stress",
        "--course", "Course",
        "--level", "undergrad",
        "--duration", "0",
    ])
    with pytest.raises(ValueError, match="duration"):
        validate_args(args)


def test_validate_args_too_long_duration_raises():
    args = parse_args([
        "--topic", "Stress",
        "--course", "Course",
        "--level", "undergrad",
        "--duration", "999",
    ])
    with pytest.raises(ValueError, match="duration"):
        validate_args(args)


def test_validate_args_valid_passes():
    args = parse_args([
        "--topic", "Stress",
        "--course", "Coping",
        "--level", "mixed",
        "--duration", "90",
    ])
    validate_args(args)


def test_slug_used_in_output_filename():
    slug = make_slug("Cortisol and the Stress Response")
    assert slug == "cortisol-and-the-stress-response"


def test_all_three_levels_accepted():
    for level in ("undergrad", "graduate", "mixed"):
        args = parse_args([
            "--topic", "Topic",
            "--course", "Course",
            "--level", level,
        ])
        assert args.level == level

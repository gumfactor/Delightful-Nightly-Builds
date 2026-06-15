"""Tests for markdown output formatting."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generator import generate_vignettes
from src.formatter import format_participant, format_researcher, format_stdout


@pytest.fixture
def stress_vignettes():
    return generate_vignettes("stress", count=3, seed=10)


@pytest.fixture
def single_vignette():
    return generate_vignettes("moral", count=1, seed=5)


class TestFormatParticipant:
    def test_contains_vignette_headers(self, stress_vignettes):
        output = format_participant(stress_vignettes)
        assert "## Vignette 1" in output
        assert "## Vignette 2" in output
        assert "## Vignette 3" in output

    def test_does_not_contain_manipulation_checks(self, stress_vignettes):
        output = format_participant(stress_vignettes)
        assert "Manipulation Checks" not in output
        assert "manipulation check" not in output.lower()

    def test_does_not_contain_researcher_note(self, stress_vignettes):
        output = format_participant(stress_vignettes)
        assert "researcher_note" not in output
        assert "Theme note:" not in output

    def test_contains_character_narrative(self, single_vignette):
        output = format_participant(single_vignette)
        char_name = single_vignette[0].character["name"]
        assert char_name in output

    def test_empty_list_returns_placeholder(self):
        output = format_participant([])
        assert "No vignettes" in output

    def test_contains_theme_in_header(self, stress_vignettes):
        output = format_participant(stress_vignettes)
        assert "Stress" in output or "stress" in output


class TestFormatResearcher:
    def test_contains_manipulation_checks_section(self, stress_vignettes):
        output = format_researcher(stress_vignettes)
        assert "Manipulation Checks" in output

    def test_contains_theme_note(self, stress_vignettes):
        output = format_researcher(stress_vignettes)
        assert "Theme note:" in output

    def test_contains_character_metadata(self, single_vignette):
        output = format_researcher(single_vignette)
        char = single_vignette[0].character
        assert char["name"] in output
        assert str(char["age"]) in output
        assert char["role"] in output

    def test_check_questions_are_numbered(self, single_vignette):
        output = format_researcher(single_vignette)
        assert "1." in output
        assert "2." in output

    def test_researcher_version_longer_than_participant(self, stress_vignettes):
        participant = format_participant(stress_vignettes)
        researcher = format_researcher(stress_vignettes)
        assert len(researcher) > len(participant)

    def test_empty_list_returns_placeholder(self):
        output = format_researcher([])
        assert "No vignettes" in output


class TestFormatStdout:
    def test_default_is_participant_format(self, stress_vignettes):
        default_out = format_stdout(stress_vignettes, researcher=False)
        participant_out = format_participant(stress_vignettes)
        assert default_out == participant_out

    def test_researcher_flag_uses_researcher_format(self, stress_vignettes):
        researcher_out = format_stdout(stress_vignettes, researcher=True)
        assert "Manipulation Checks" in researcher_out

"""Tests for vignette generation logic."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.generator import generate_vignettes, list_themes, Vignette
from src.banks import CHARACTERS, THEMES


class TestListThemes:
    def test_returns_all_three_themes(self):
        result = list_themes()
        assert set(result.keys()) == {"stress", "empathy", "moral"}

    def test_each_theme_has_required_keys(self):
        result = list_themes()
        for theme_data in result.values():
            assert "label" in theme_data
            assert "description" in theme_data
            assert "combinations" in theme_data
            assert theme_data["combinations"] > 0

    def test_combination_counts_are_positive(self):
        result = list_themes()
        for theme_data in result.values():
            assert theme_data["combinations"] >= 1


class TestGenerateVignettes:
    def test_returns_correct_count(self):
        vignettes = generate_vignettes("stress", count=5)
        assert len(vignettes) == 5

    def test_returns_empty_for_zero_count(self):
        vignettes = generate_vignettes("stress", count=0)
        assert vignettes == []

    def test_each_vignette_has_required_fields(self):
        vignettes = generate_vignettes("empathy", count=3)
        for v in vignettes:
            assert isinstance(v, Vignette)
            assert v.narrative and len(v.narrative) > 20
            assert len(v.checks) == 2
            assert v.prompt and len(v.prompt) > 10
            assert v.researcher_note and len(v.researcher_note) > 10
            assert v.theme == "empathy"

    def test_index_is_one_based(self):
        vignettes = generate_vignettes("moral", count=4)
        indices = [v.index for v in vignettes]
        assert indices == [1, 2, 3, 4]

    def test_invalid_theme_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown theme"):
            generate_vignettes("nonexistent_theme", count=1)

    def test_negative_count_raises_value_error(self):
        with pytest.raises(ValueError, match="count must be"):
            generate_vignettes("stress", count=-1)

    def test_seeded_output_is_reproducible(self):
        run_a = generate_vignettes("stress", count=5, seed=42)
        run_b = generate_vignettes("stress", count=5, seed=42)
        assert [v.narrative for v in run_a] == [v.narrative for v in run_b]
        assert [v.prompt for v in run_a] == [v.prompt for v in run_b]

    def test_different_seeds_produce_different_output(self):
        run_a = generate_vignettes("stress", count=5, seed=1)
        run_b = generate_vignettes("stress", count=5, seed=2)
        # At least one narrative should differ
        narratives_a = [v.narrative for v in run_a]
        narratives_b = [v.narrative for v in run_b]
        assert narratives_a != narratives_b

    def test_count_larger_than_character_pool_does_not_crash(self):
        # CHARACTER pool has 10 entries; requesting 25 should still work
        vignettes = generate_vignettes("stress", count=25, seed=0)
        assert len(vignettes) == 25
        for v in vignettes:
            assert v.narrative

    def test_narrative_includes_character_name(self):
        vignettes = generate_vignettes("moral", count=3, seed=7)
        for v in vignettes:
            assert v.character["name"] in v.narrative

    def test_checks_contain_character_name(self):
        vignettes = generate_vignettes("empathy", count=3, seed=3)
        for v in vignettes:
            for check in v.checks:
                assert v.character["name"] in check

    def test_all_three_themes_generate_without_error(self):
        for theme in ("stress", "empathy", "moral"):
            vignettes = generate_vignettes(theme, count=2, seed=99)
            assert len(vignettes) == 2
            assert all(v.theme == theme for v in vignettes)

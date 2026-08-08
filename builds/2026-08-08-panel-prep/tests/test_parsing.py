import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import parsing


def test_markdown_headers_split_into_sections():
    text = "# Specific Aims\nAim text.\n\n## Significance\nSig text.\n"
    sections = parsing.parse(text)
    assert sections["aims"] == "Aim text."
    assert sections["significance"] == "Sig text."


def test_allcaps_headers_split_into_sections():
    text = "SPECIFIC AIMS\nAim text.\n\nINNOVATION\nInnovation text.\n"
    sections = parsing.parse(text)
    assert sections["aims"] == "Aim text."
    assert sections["innovation"] == "Innovation text."


def test_colon_style_headers_split_into_sections():
    text = "Significance: This work matters because X.\nMore significance text.\n\nApproach: We will do Y.\n"
    sections = parsing.parse(text)
    assert "This work matters because X." in sections["significance"]
    assert "More significance text." in sections["significance"]
    assert "We will do Y." in sections["approach"]


def test_no_recognized_headers_falls_back_to_whole_document_as_aims():
    text = "This is just a plain paragraph with no headers at all describing a study."
    sections = parsing.parse(text)
    assert list(sections.keys()) == ["aims"]
    assert sections["aims"] == text


def test_empty_input_returns_empty_dict():
    assert parsing.parse("") == {}
    assert parsing.parse("   \n\n  ") == {}


def test_missing_sections_are_simply_absent():
    text = "# Specific Aims\nAim text only, no other sections.\n"
    sections = parsing.parse(text)
    assert "aims" in sections
    assert "significance" not in sections
    assert "approach" not in sections


def test_case_and_whitespace_insensitive_header_matching():
    text = "#    specific   AIMS   \nAim content here.\n"
    sections = parsing.parse(text)
    assert sections["aims"] == "Aim content here."


def test_research_strategy_alias_maps_to_approach():
    text = "# Research Strategy\nWe will run three studies.\n"
    sections = parsing.parse(text)
    assert sections["approach"] == "We will run three studies."


def test_preamble_before_first_header_is_dropped():
    text = "Grant Number: R01-12345\nPI: Jane Smith\n\n# Specific Aims\nReal aim content.\n"
    sections = parsing.parse(text)
    assert sections["aims"] == "Real aim content."
    assert "Grant Number" not in "".join(sections.values())

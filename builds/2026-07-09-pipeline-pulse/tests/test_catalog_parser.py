from pathlib import Path

import pytest

from catalog_parser import parse_catalog, parse_catalog_text

FIXTURE = Path(__file__).parent.parent / "sample_index.md"


def test_parse_catalog_from_file_returns_three_records():
    records = parse_catalog(str(FIXTURE))
    assert len(records) == 3


def test_parse_catalog_numeric_rating_parsed_as_int():
    records = parse_catalog(str(FIXTURE))
    first = next(r for r in records if r["title"] == "Sample One")
    assert first["rating"] == 3


def test_parse_catalog_blank_rating_is_none():
    records = parse_catalog(str(FIXTURE))
    second = next(r for r in records if r["title"] == "Sample Two")
    assert second["rating"] is None


def test_parse_catalog_fields_are_populated():
    records = parse_catalog(str(FIXTURE))
    first = records[0]
    assert first["date"] == "2026-06-06"
    assert first["category"] == "B"
    assert first["complexity"] == "ambitious"
    assert first["status"] == "complete"
    assert first["notes"] == "Some notes"


def test_parse_catalog_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        parse_catalog("/nonexistent/path/index.md")


def test_parse_catalog_text_single_row_table():
    text = (
        "## Full Catalog\n\n"
        "| Date | Category | Complexity | Title | Short Description | Tech | Status | Your Rating | Rating Notes |\n"
        "|------|----------|------------|-------|-------------------|------|--------|-------------|--------------|\n"
        "| 2026-01-01 | A | solid | Only Build | desc | Python | complete | 7 | good |\n"
    )
    records = parse_catalog_text(text)
    assert len(records) == 1
    assert records[0]["title"] == "Only Build"
    assert records[0]["rating"] == 7


def test_parse_catalog_text_no_table_header_returns_empty():
    assert parse_catalog_text("# Just a heading\n\nNo table here.") == []


def test_parse_catalog_text_table_with_only_header_returns_empty():
    text = (
        "## Full Catalog\n\n"
        "| Date | Category | Complexity | Title | Short Description | Tech | Status | Your Rating | Rating Notes |\n"
        "|------|----------|------------|-------|-------------------|------|--------|-------------|--------------|\n"
    )
    assert parse_catalog_text(text) == []

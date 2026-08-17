import os

import pytest

import csv_ingest
from conftest import FIXTURES_DIR

VALID_CSV = os.path.join(FIXTURES_DIR, "businesses_valid.csv")
MISSING_COLUMN_CSV = os.path.join(FIXTURES_DIR, "businesses_missing_column.csv")
NO_VERDICT_CSV = os.path.join(FIXTURES_DIR, "businesses_no_verdict.csv")


def test_load_businesses_parses_valid_csv():
    businesses, has_verdict_column = csv_ingest.load_businesses(VALID_CSV)
    assert has_verdict_column is True
    assert len(businesses) == 8
    first = businesses[0]
    assert first["name"] == "Northern Bloom Skincare"
    assert first["category"] == "Skincare"
    assert first["province"] == "Nova Scotia"
    assert first["verdict"] == "canadian"
    assert first["confidence"] == pytest.approx(0.95)
    assert "Halifax" in first["evidence"]


def test_load_businesses_missing_required_column_raises():
    with pytest.raises(ValueError, match="category"):
        csv_ingest.load_businesses(MISSING_COLUMN_CSV)


def test_load_businesses_blank_required_field_raises(tmp_path):
    bad_csv = tmp_path / "blank_name.csv"
    bad_csv.write_text("name,category\n,Bakery\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Row 2"):
        csv_ingest.load_businesses(str(bad_csv))


def test_load_businesses_no_rows_raises(tmp_path):
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("name,category\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no business rows"):
        csv_ingest.load_businesses(str(empty_csv))


def test_load_businesses_no_header_raises(tmp_path):
    truly_empty_csv = tmp_path / "truly_empty.csv"
    truly_empty_csv.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="no header row"):
        csv_ingest.load_businesses(str(truly_empty_csv))


def test_load_businesses_nonexistent_file_raises():
    with pytest.raises(FileNotFoundError):
        csv_ingest.load_businesses("/nonexistent/path/does_not_exist.csv")


def test_filter_by_verdict_default_keeps_only_canadian():
    businesses, has_verdict_column = csv_ingest.load_businesses(VALID_CSV)
    filtered = csv_ingest.filter_by_verdict(businesses, has_verdict_column, include_unverified=False)
    names = {b["name"] for b in filtered}
    assert "GlobalGlow Cosmetics" not in names
    assert "Harbourfront Woodworks" not in names
    assert "Northern Bloom Skincare" in names
    assert len(filtered) == 6
    assert all(b["verified"] for b in filtered)


def test_filter_by_verdict_include_unverified_keeps_all():
    businesses, has_verdict_column = csv_ingest.load_businesses(VALID_CSV)
    filtered = csv_ingest.filter_by_verdict(businesses, has_verdict_column, include_unverified=True)
    assert len(filtered) == 8
    by_name = {b["name"]: b for b in filtered}
    assert by_name["GlobalGlow Cosmetics"]["verified"] is False
    assert by_name["Harbourfront Woodworks"]["verified"] is False
    assert by_name["Northern Bloom Skincare"]["verified"] is True


def test_filter_by_verdict_no_verdict_column_marks_all_unverified():
    businesses, has_verdict_column = csv_ingest.load_businesses(NO_VERDICT_CSV)
    assert has_verdict_column is False
    filtered = csv_ingest.filter_by_verdict(businesses, has_verdict_column, include_unverified=False)
    assert len(filtered) == 3
    assert all(b["verified"] is False for b in filtered)


def test_select_for_spotlight_found():
    businesses, has_verdict_column = csv_ingest.load_businesses(VALID_CSV)
    filtered = csv_ingest.filter_by_verdict(businesses, has_verdict_column, include_unverified=False)
    selected = csv_ingest.select_for_spotlight(filtered, "birchwood skin co")
    assert len(selected) == 1
    assert selected[0]["name"] == "Birchwood Skin Co"


def test_select_for_spotlight_not_found_raises():
    businesses, has_verdict_column = csv_ingest.load_businesses(VALID_CSV)
    filtered = csv_ingest.filter_by_verdict(businesses, has_verdict_column, include_unverified=False)
    with pytest.raises(ValueError, match="No business named"):
        csv_ingest.select_for_spotlight(filtered, "Nonexistent Business")


def test_select_by_category():
    businesses, has_verdict_column = csv_ingest.load_businesses(VALID_CSV)
    filtered = csv_ingest.filter_by_verdict(businesses, has_verdict_column, include_unverified=False)
    skincare = csv_ingest.select_by_category(filtered, "skincare")
    assert len(skincare) == 3
    assert {b["name"] for b in skincare} == {
        "Northern Bloom Skincare",
        "Birchwood Skin Co",
        "Maple Grove Botanicals",
    }


def test_select_by_province():
    businesses, has_verdict_column = csv_ingest.load_businesses(VALID_CSV)
    filtered = csv_ingest.filter_by_verdict(businesses, has_verdict_column, include_unverified=False)
    ontario = csv_ingest.select_by_province(filtered, "Ontario")
    assert len(ontario) == 2
    assert {b["name"] for b in ontario} == {"Birchwood Skin Co", "Cedar & Stone Coffee Roasters"}

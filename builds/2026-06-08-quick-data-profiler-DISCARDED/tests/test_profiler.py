"""
Tests for src/profiler.py — type inference, column profiling, file reading, formatting.
Run with: python -m pytest tests/ -v  (from the builds/2026-06-08/ directory)
"""

import json
import sys
from pathlib import Path

# Ensure the build folder is on sys.path so imports resolve from any working directory
BUILD_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BUILD_DIR))

from src.profiler import (
    infer_type,
    profile_column,
    read_csv,
    read_json,
    profile_file,
    format_text,
    format_json,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# infer_type
# ---------------------------------------------------------------------------

class TestInferType:
    def test_integer_column(self):
        values = ["1", "2", "3", "42", "100"]
        assert infer_type(values) == "integer"

    def test_float_column(self):
        values = ["1.5", "2.3", "0.99", "100.0", "3.14"]
        assert infer_type(values) == "float"

    def test_mixed_int_float_returns_float(self):
        # Integers are a subset of floats — mixed column should resolve to float
        values = ["1", "2.5", "3", "4.1", "5"]
        assert infer_type(values) == "float"

    def test_date_column_iso(self):
        values = ["2024-01-01", "2024-06-15", "2023-12-31", "2025-03-08", "2022-07-04"]
        assert infer_type(values) == "date"

    def test_boolean_column(self):
        values = ["true", "false", "true", "true", "false"]
        assert infer_type(values) == "boolean"

    def test_boolean_yes_no(self):
        values = ["yes", "no", "yes", "no", "yes"]
        assert infer_type(values) == "boolean"

    def test_string_column(self):
        values = ["Alice", "Bob", "Charlie", "Diana", "Eve"]
        assert infer_type(values) == "string"

    def test_empty_list_returns_string(self):
        # No values to inspect — default to string
        assert infer_type([]) == "string"

    def test_mostly_integer_with_noise_returns_integer(self):
        # 9/10 integers — above 80% threshold
        values = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "not_a_number"]
        assert infer_type(values) == "integer"

    def test_mixed_string_and_number_returns_string(self):
        # Below 80% threshold for any numeric type
        values = ["abc", "123", "def", "456", "ghi", "789", "xyz"]
        assert infer_type(values) == "string"


# ---------------------------------------------------------------------------
# profile_column
# ---------------------------------------------------------------------------

class TestProfileColumn:
    def test_basic_metadata_present(self):
        col = profile_column("age", ["30", "25", "40"])
        assert col["name"] == "age"
        assert col["type"] == "integer"
        assert col["total"] == 3
        assert col["null_count"] == 0
        assert col["unique_count"] == 3

    def test_null_counting(self):
        col = profile_column("score", ["92.5", "", "88.0", "", "77.0"])
        assert col["null_count"] == 2
        assert col["null_pct"] == 40.0

    def test_all_nulls(self):
        col = profile_column("empty", ["", "", ""])
        assert col["null_count"] == 3
        assert col["unique_count"] == 0
        assert col["type"] == "string"
        assert col["sample"] == []

    def test_numeric_stats_present(self):
        col = profile_column("price", ["10.0", "20.0", "30.0", "40.0", "50.0"])
        assert "min" in col and "max" in col and "mean" in col
        assert col["min"] == 10.0
        assert col["max"] == 50.0
        assert col["mean"] == 30.0
        assert col["median"] == 30.0

    def test_std_dev_single_value(self):
        # std dev is 0 for a single value (no variance)
        col = profile_column("val", ["42"])
        assert col["std"] == 0.0

    def test_top_values_for_low_cardinality_string(self):
        values = ["A", "B", "A", "C", "A", "B", "C", "A"]
        col = profile_column("category", values, top_n=3)
        assert "top_values" in col
        top = col["top_values"]
        assert top[0]["value"] == "A"
        assert top[0]["count"] == 4

    def test_no_top_values_for_high_cardinality(self):
        # 21 unique values exceeds the cardinality threshold
        values = [str(i) for i in range(21)]
        col = profile_column("id", values)
        assert "top_values" not in col

    def test_sample_values_capped(self):
        col = profile_column("name", ["Alice", "Bob", "Charlie", "Diana"], sample_n=2)
        assert len(col["sample"]) == 2

    def test_unique_count_excludes_nulls(self):
        col = profile_column("tag", ["A", "B", "A", "", ""])
        # 2 unique non-null values: A, B
        assert col["unique_count"] == 2

    def test_whitespace_treated_as_null(self):
        col = profile_column("val", ["  ", "\t", "42"])
        assert col["null_count"] == 2


# ---------------------------------------------------------------------------
# read_csv
# ---------------------------------------------------------------------------

class TestReadCsv:
    def test_reads_header_and_rows(self):
        header, rows = read_csv(str(FIXTURES / "sample.csv"))
        assert header[0] == "id"
        assert "name" in header
        assert len(rows) == 10

    def test_row_values_are_strings(self):
        header, rows = read_csv(str(FIXTURES / "sample.csv"))
        assert all(isinstance(v, str) for row in rows for v in row)

    def test_row_length_matches_header(self):
        header, rows = read_csv(str(FIXTURES / "sample.csv"))
        for row in rows:
            assert len(row) == len(header)

    def test_file_not_found_raises(self):
        import pytest
        with pytest.raises(FileNotFoundError):
            read_csv("/nonexistent/path/file.csv")


# ---------------------------------------------------------------------------
# read_json
# ---------------------------------------------------------------------------

class TestReadJson:
    def test_reads_json_array(self):
        header, rows = read_json(str(FIXTURES / "sample.json"))
        assert "product" in header
        assert len(rows) == 5

    def test_reads_jsonl(self):
        header, rows = read_json(str(FIXTURES / "sample.jsonl"))
        assert "event" in header
        assert len(rows) == 5

    def test_null_json_value_becomes_empty_string(self):
        header, rows = read_json(str(FIXTURES / "sample.json"))
        # sample.json has null for "in_stock" on last record
        stock_idx = header.index("in_stock")
        last_row = rows[-1]
        assert last_row[stock_idx] == ""

    def test_file_not_found_raises(self):
        import pytest
        with pytest.raises(FileNotFoundError):
            read_json("/nonexistent/path/file.json")


# ---------------------------------------------------------------------------
# profile_file (integration)
# ---------------------------------------------------------------------------

class TestProfileFile:
    def test_csv_profile_structure(self):
        result = profile_file(str(FIXTURES / "sample.csv"))
        assert result["format"] == "CSV"
        assert result["rows"] == 10
        assert len(result["columns"]) == 7

    def test_json_profile_structure(self):
        result = profile_file(str(FIXTURES / "sample.json"))
        assert result["format"] == "JSON"
        assert result["rows"] == 5

    def test_jsonl_profile_structure(self):
        result = profile_file(str(FIXTURES / "sample.jsonl"))
        assert result["format"] == "JSONL"
        assert result["rows"] == 5

    def test_unsupported_extension_raises(self):
        import pytest
        with pytest.raises(ValueError, match="Unsupported file extension"):
            profile_file("data.xlsx")


# ---------------------------------------------------------------------------
# format_text / format_json
# ---------------------------------------------------------------------------

class TestFormatters:
    def setup_method(self):
        self.profile = profile_file(str(FIXTURES / "sample.csv"))

    def test_text_contains_filename(self):
        output = format_text(self.profile)
        assert "sample.csv" in output

    def test_text_contains_column_names(self):
        output = format_text(self.profile)
        assert '"id"' in output
        assert '"name"' in output
        assert '"score"' in output

    def test_text_contains_type_labels(self):
        output = format_text(self.profile)
        assert "integer" in output or "float" in output or "string" in output

    def test_json_output_is_valid_json(self):
        output = format_json(self.profile)
        parsed = json.loads(output)
        assert parsed["rows"] == 10
        assert len(parsed["columns"]) == 7

    def test_json_output_contains_column_names(self):
        output = format_json(self.profile)
        parsed = json.loads(output)
        col_names = [c["name"] for c in parsed["columns"]]
        assert "id" in col_names
        assert "name" in col_names

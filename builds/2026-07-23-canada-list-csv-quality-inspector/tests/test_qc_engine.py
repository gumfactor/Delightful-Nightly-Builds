from src.qc_engine import (
    build_row_records,
    check_required_columns_present,
    compute_recommended_action,
    decode_csv_bytes,
    parse_csv,
    validate_row,
    Flag,
)
from src.schema import Schema

HEADER = ["business_name", "category", "province", "website", "canadian_ownership_pct", "ownership_status", "email"]


def test_decode_valid_utf8_has_no_flags():
    result = decode_csv_bytes("business_name,category\nAcme,Retail\n".encode("utf-8"))
    assert result.file_flags == []
    assert "Acme" in result.text


def test_decode_detects_bom():
    raw = b"\xef\xbb\xbf" + "business_name\nAcme\n".encode("utf-8")
    result = decode_csv_bytes(raw)
    assert any(f.code == "bom_present" for f in result.file_flags)
    assert not result.text.startswith("﻿")


def test_decode_detects_invalid_utf8():
    raw = b"business_name\nAcme " + b"\xff\xfe" + b"\n"
    result = decode_csv_bytes(raw)
    assert any(f.code == "invalid_utf8" and f.severity == "error" for f in result.file_flags)


def test_decode_detects_possible_mojibake():
    # A Windows-1252 curly quote re-decoded as UTF-8 with replacement chars.
    raw = "business_name\nAcme � Co\n".encode("utf-8")
    result = decode_csv_bytes(raw)
    assert any(f.code == "possible_mojibake" for f in result.file_flags)


def test_parse_csv_empty_file_flags_error():
    header, rows, flags = parse_csv("")
    assert header == []
    assert rows == []
    assert any(f.code == "empty_file" for f in flags)


def test_parse_csv_happy_path():
    text = "business_name,category\nAcme,Retail\nBeta,Bakery\n"
    header, rows, flags = parse_csv(text)
    assert header == ["business_name", "category"]
    assert len(rows) == 2
    assert flags == []
    (row1, row1_flags) = rows[0]
    assert row1 == {"business_name": "Acme", "category": "Retail"}
    assert row1_flags == []


def test_parse_csv_detects_ragged_row():
    text = "business_name,category,province\nAcme,Retail\n"
    header, rows, flags = parse_csv(text)
    (row1, row1_flags) = rows[0]
    assert any(f.code == "ragged_row" for f in row1_flags)
    # padded so downstream code never KeyErrors
    assert row1["province"] == ""


def test_parse_csv_detects_duplicate_headers():
    text = "business_name,business_name\nAcme,Beta\n"
    header, rows, flags = parse_csv(text)
    assert any(f.code == "duplicate_headers" for f in flags)


def test_parse_csv_skips_fully_blank_lines():
    text = "business_name,category\nAcme,Retail\n\n\nBeta,Bakery\n"
    header, rows, flags = parse_csv(text)
    assert len(rows) == 2


def test_check_required_columns_present_flags_missing_column():
    schema = Schema.default()
    flags = check_required_columns_present(["business_name", "category"], schema)
    assert any(f.code == "missing_required_column" for f in flags)


def test_check_required_columns_present_ok_when_all_present():
    schema = Schema.default()
    flags = check_required_columns_present(HEADER, schema)
    assert flags == []


def test_validate_row_flags_missing_required_field():
    schema = Schema.default()
    fields = {"business_name": "", "category": "Retail", "province": "ON", "website": "acme.ca"}
    flags = validate_row(1, fields, ["business_name", "category", "province", "website"], schema)
    assert any(f.code == "missing_required_field" and f.column == "business_name" for f in flags)


def test_validate_row_flags_invalid_website():
    schema = Schema.default()
    fields = {"business_name": "Acme", "category": "Retail", "province": "ON", "website": "not a url!!"}
    flags = validate_row(1, fields, ["business_name", "category", "province", "website"], schema)
    assert any(f.code == "invalid_website" for f in flags)


def test_validate_row_accepts_bare_domain_website():
    schema = Schema.default()
    fields = {"business_name": "Acme", "category": "Retail", "province": "ON", "website": "acme.ca"}
    flags = validate_row(1, fields, ["business_name", "category", "province", "website"], schema)
    assert not any(f.code == "invalid_website" for f in flags)


def test_validate_row_flags_invalid_province():
    schema = Schema.default()
    fields = {"business_name": "Acme", "category": "Retail", "province": "Nowhereland", "website": "acme.ca"}
    flags = validate_row(1, fields, ["business_name", "category", "province", "website"], schema)
    assert any(f.code == "invalid_province" for f in flags)


def test_validate_row_flags_ownership_pct_out_of_range():
    schema = Schema.default()
    fields = {
        "business_name": "Acme", "category": "Retail", "province": "ON", "website": "acme.ca",
        "canadian_ownership_pct": "150",
    }
    flags = validate_row(1, fields, HEADER, schema)
    assert any(f.code == "ownership_pct_out_of_range" for f in flags)


def test_validate_row_flags_ownership_pct_not_numeric():
    schema = Schema.default()
    fields = {
        "business_name": "Acme", "category": "Retail", "province": "ON", "website": "acme.ca",
        "canadian_ownership_pct": "mostly",
    }
    flags = validate_row(1, fields, HEADER, schema)
    assert any(f.code == "ownership_pct_not_numeric" for f in flags)


def test_validate_row_flags_unmapped_ownership_status():
    schema = Schema.default()
    fields = {
        "business_name": "Acme", "category": "Retail", "province": "ON", "website": "acme.ca",
        "ownership_status": "partially-canadian",
    }
    flags = validate_row(1, fields, HEADER, schema)
    assert any(f.code == "unmapped_ownership_status" and f.severity == "warning" for f in flags)


def test_validate_row_flags_invalid_email():
    schema = Schema.default()
    fields = {
        "business_name": "Acme", "category": "Retail", "province": "ON", "website": "acme.ca",
        "email": "not-an-email",
    }
    flags = validate_row(1, fields, HEADER, schema)
    assert any(f.code == "invalid_email" for f in flags)


def test_validate_row_flags_control_characters():
    schema = Schema.default()
    fields = {
        "business_name": "Acme\x07Corp", "category": "Retail", "province": "ON", "website": "acme.ca",
    }
    flags = validate_row(1, fields, ["business_name", "category", "province", "website"], schema)
    assert any(f.code == "control_characters" for f in flags)


def test_validate_row_clean_row_has_no_flags():
    schema = Schema.default()
    fields = {
        "business_name": "Acme", "category": "Retail", "province": "ON", "website": "acme.ca",
        "canadian_ownership_pct": "100", "ownership_status": "canadian-owned", "email": "info@acme.ca",
    }
    flags = validate_row(1, fields, HEADER, schema)
    assert flags == []


def test_compute_recommended_action_error_means_drop():
    flags = [Flag("x", "error", "bad"), Flag("y", "warning", "meh")]
    assert compute_recommended_action(flags) == "drop"


def test_compute_recommended_action_warning_only_means_review():
    flags = [Flag("y", "warning", "meh")]
    assert compute_recommended_action(flags) == "review"


def test_compute_recommended_action_no_flags_means_keep():
    assert compute_recommended_action([]) == "keep"


def test_build_row_records_combines_structural_and_validation_flags():
    schema = Schema.default()
    header, rows, _ = parse_csv("business_name,category,province,website\n,Retail,ON,acme.ca\n")
    records = build_row_records(rows, header, schema)
    assert len(records) == 1
    assert records[0].row_index == 1
    assert any(f.code == "missing_required_field" for f in records[0].flags)
    assert records[0].recommended_action == "drop"

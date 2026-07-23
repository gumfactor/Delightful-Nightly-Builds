"""Structural, required-field, format, and encoding QC checks for a
business-directory CSV export headed for The Canada List's ingestion pipeline.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

from src.schema import Schema, normalize_province

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

SEVERITY_ORDER = {"error": 2, "warning": 1, "info": 0}


@dataclass
class Flag:
    code: str
    severity: str  # "error" | "warning" | "info"
    message: str
    column: str = ""

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "column": self.column,
        }


@dataclass
class RowRecord:
    row_index: int
    raw_fields: dict
    flags: list = field(default_factory=list)

    @property
    def recommended_action(self) -> str:
        return compute_recommended_action(self.flags)

    @property
    def flags_string(self) -> str:
        return "; ".join(f"{f.severity}:{f.code}" for f in self.flags)

    def to_dict(self) -> dict:
        return {
            "row_index": self.row_index,
            "fields": self.raw_fields,
            "flags": [f.to_dict() for f in self.flags],
            "recommended_action": self.recommended_action,
        }


class DecodeResult:
    def __init__(self, text: str, file_flags: list):
        self.text = text
        self.file_flags = file_flags


def decode_csv_bytes(raw_bytes: bytes) -> DecodeResult:
    """Decode raw CSV bytes as UTF-8, reporting BOM/encoding-level issues.

    Never raises for undecodable bytes: they are replaced so downstream
    parsing can still surface row-level problems, but a file-level error
    flag records that the source encoding was not clean UTF-8.
    """
    file_flags: list[Flag] = []

    has_bom = raw_bytes.startswith(b"\xef\xbb\xbf")
    if has_bom:
        file_flags.append(
            Flag("bom_present", "info", "File starts with a UTF-8 byte-order mark (BOM).")
        )
        raw_bytes = raw_bytes[3:]

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        file_flags.append(
            Flag(
                "invalid_utf8",
                "error",
                f"File is not valid UTF-8 (decode failed at byte offset {exc.start}). "
                "Undecodable bytes were replaced so QC could still run.",
            )
        )
        text = raw_bytes.decode("utf-8", errors="replace")

    if "�" in text:
        # Replacement character present even without a hard decode error can
        # indicate the source file was actually a different encoding
        # (e.g. Windows-1252) re-saved as UTF-8 ("mojibake").
        if not any(f.code == "invalid_utf8" for f in file_flags):
            file_flags.append(
                Flag(
                    "possible_mojibake",
                    "warning",
                    "File contains Unicode replacement characters, which usually means "
                    "it was saved in an encoding other than UTF-8 (e.g. Windows-1252).",
                )
            )

    return DecodeResult(text=text, file_flags=file_flags)


def parse_csv(text: str) -> tuple[list, list, list]:
    """Parse CSV text into (header, rows, structural_flags).

    `rows` is a list of dicts mapping the *original* header names to values.
    Ragged rows (wrong column count) are still returned, padded/truncated,
    with a structural flag attached via the returned per-row flag list
    (index-aligned with `rows`).
    """
    structural_flags: list[Flag] = []
    reader = csv.reader(io.StringIO(text))
    all_rows = list(reader)

    if not all_rows or not any(cell.strip() for cell in all_rows[0]):
        structural_flags.append(Flag("empty_file", "error", "CSV file has no header row."))
        return [], [], structural_flags

    header = [h.strip() for h in all_rows[0]]
    seen_headers: dict[str, int] = {}
    for h in header:
        seen_headers[h] = seen_headers.get(h, 0) + 1
    duplicate_headers = [h for h, count in seen_headers.items() if count > 1 and h]
    if duplicate_headers:
        structural_flags.append(
            Flag(
                "duplicate_headers",
                "error",
                f"Duplicate column header(s): {', '.join(sorted(duplicate_headers))}.",
            )
        )

    rows: list[dict] = []
    row_flags: list[list] = []
    for raw_row in all_rows[1:]:
        if not any(cell.strip() for cell in raw_row):
            continue  # skip fully blank lines
        flags: list[Flag] = []
        if len(raw_row) != len(header):
            flags.append(
                Flag(
                    "ragged_row",
                    "error",
                    f"Row has {len(raw_row)} column(s), header has {len(header)}.",
                )
            )
        padded = list(raw_row) + [""] * max(0, len(header) - len(raw_row))
        row_dict = {header[i]: padded[i] for i in range(len(header)) if i < len(header)}
        # Any extra columns beyond the header are preserved under a synthetic key.
        if len(raw_row) > len(header):
            row_dict["__extra_columns__"] = raw_row[len(header):]
        rows.append(row_dict)
        row_flags.append(flags)

    return header, list(zip(rows, row_flags)), structural_flags


def _find_column(header: list, target: str) -> str | None:
    target_lower = target.strip().lower()
    for col in header:
        if col.strip().lower() == target_lower:
            return col
    return None


def validate_row(row_index: int, raw_fields: dict, header: list, schema: Schema) -> list:
    """Run required-field, format, and character-safety checks on one row."""
    flags: list[Flag] = []

    required_lookup = {
        req: _find_column(header, req) for req in schema.required_columns
    }
    for required_name, actual_col in required_lookup.items():
        if actual_col is None:
            continue  # missing column entirely is a file-level concern, not per-row
        value = (raw_fields.get(actual_col) or "").strip()
        if not value:
            flags.append(
                Flag(
                    "missing_required_field",
                    "error",
                    f"Required field '{required_name}' is empty.",
                    column=actual_col,
                )
            )

    website_col = _find_column(header, "website")
    if website_col:
        value = (raw_fields.get(website_col) or "").strip()
        if value and not _is_valid_url(value):
            flags.append(
                Flag(
                    "invalid_website",
                    "warning",
                    f"'{value}' does not look like a valid website URL.",
                    column=website_col,
                )
            )

    province_col = _find_column(header, "province")
    if province_col:
        value = (raw_fields.get(province_col) or "").strip()
        if value and normalize_province(value) is None:
            flags.append(
                Flag(
                    "invalid_province",
                    "error",
                    f"'{value}' is not a recognized Canadian province/territory.",
                    column=province_col,
                )
            )

    ownership_pct_col = _find_column(header, "canadian_ownership_pct")
    if ownership_pct_col:
        value = (raw_fields.get(ownership_pct_col) or "").strip()
        if value:
            try:
                pct = float(value)
                if not (0 <= pct <= 100):
                    flags.append(
                        Flag(
                            "ownership_pct_out_of_range",
                            "error",
                            f"'{value}' is outside the valid 0-100 range.",
                            column=ownership_pct_col,
                        )
                    )
            except ValueError:
                flags.append(
                    Flag(
                        "ownership_pct_not_numeric",
                        "error",
                        f"'{value}' is not a number.",
                        column=ownership_pct_col,
                    )
                )

    ownership_status_col = _find_column(header, "ownership_status")
    if ownership_status_col:
        value = (raw_fields.get(ownership_status_col) or "").strip()
        if value and value.lower() not in {v.lower() for v in schema.ownership_status_values}:
            flags.append(
                Flag(
                    "unmapped_ownership_status",
                    "warning",
                    f"'{value}' is not one of the canonical ownership_status values.",
                    column=ownership_status_col,
                )
            )

    email_col = _find_column(header, "email")
    if email_col:
        value = (raw_fields.get(email_col) or "").strip()
        if value and not EMAIL_RE.match(value):
            flags.append(
                Flag(
                    "invalid_email",
                    "warning",
                    f"'{value}' does not look like a valid email address.",
                    column=email_col,
                )
            )

    for col, value in raw_fields.items():
        if col == "__extra_columns__" or not isinstance(value, str):
            continue
        if CONTROL_CHAR_RE.search(value):
            flags.append(
                Flag(
                    "control_characters",
                    "warning",
                    f"Field '{col}' contains non-printable control characters.",
                    column=col,
                )
            )
            break  # one flag per row is enough signal; avoid noisy repeats

    return flags


def _is_valid_url(value: str) -> bool:
    candidate = value if "://" in value else f"https://{value}"
    parsed = urlparse(candidate)
    if not parsed.netloc or "." not in parsed.netloc:
        return False
    # Reject netlocs with spaces or no TLD-like suffix.
    return bool(re.match(r"^[\w.-]+\.[a-zA-Z]{2,}$", parsed.netloc.split(":")[0]))


def compute_recommended_action(flags: list) -> str:
    if any(f.severity == "error" for f in flags):
        return "drop"
    if any(f.severity == "warning" for f in flags):
        return "review"
    return "keep"


def check_required_columns_present(header: list, schema: Schema) -> list:
    """File-level check: entirely missing required columns."""
    flags: list[Flag] = []
    missing = [
        req for req in schema.required_columns if _find_column(header, req) is None
    ]
    if missing:
        flags.append(
            Flag(
                "missing_required_column",
                "error",
                f"Required column(s) entirely absent from the file: {', '.join(missing)}.",
            )
        )
    return flags


def build_row_records(rows_with_flags: list, header: list, schema: Schema) -> list:
    """Turn parsed (row_dict, structural_flags) pairs into RowRecords with
    structural + validation flags combined.
    """
    records: list[RowRecord] = []
    for i, (row_dict, structural_flags) in enumerate(rows_with_flags, start=1):
        validation_flags = validate_row(i, row_dict, header, schema)
        record = RowRecord(row_index=i, raw_fields=row_dict, flags=structural_flags + validation_flags)
        records.append(record)
    return records

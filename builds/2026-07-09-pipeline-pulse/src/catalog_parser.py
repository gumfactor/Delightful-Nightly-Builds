"""Parses the Full Catalog markdown table out of a builds/index.md file."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional, TypedDict

_TABLE_HEADER_MARKER = "## Full Catalog"
_EM_DASH = "—"


class CatalogRecord(TypedDict):
    date: str
    category: str
    complexity: str
    title: str
    description: str
    tech: str
    status: str
    rating: Optional[int]
    notes: str


def _split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells if cell)


def _parse_rating(raw: str) -> Optional[int]:
    raw = raw.strip()
    if raw in ("", _EM_DASH, "-", "--"):
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def parse_catalog(index_path: str) -> list[CatalogRecord]:
    """Parse the Full Catalog table from a builds/index.md file into records.

    Raises FileNotFoundError if index_path does not exist.
    """
    path = Path(index_path)
    if not path.is_file():
        raise FileNotFoundError(f"builds/index.md not found at {index_path}")
    return parse_catalog_text(path.read_text(encoding="utf-8"))


def parse_catalog_text(text: str) -> list[CatalogRecord]:
    """Parse the Full Catalog table from raw markdown text into records."""
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line.strip().startswith(_TABLE_HEADER_MARKER))
    except StopIteration:
        return []

    table_lines = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped:
            if table_lines:
                break
            continue
        if not stripped.startswith("|"):
            break
        table_lines.append(stripped)

    if len(table_lines) < 2:
        return []

    header_cells = [c.lower() for c in _split_row(table_lines[0])]
    records: list[CatalogRecord] = []

    for line in table_lines[1:]:
        cells = _split_row(line)
        if _is_separator_row(cells):
            continue
        if len(cells) != len(header_cells):
            continue
        row = dict(zip(header_cells, cells))
        records.append(
            CatalogRecord(
                date=row.get("date", ""),
                category=row.get("category", ""),
                complexity=row.get("complexity", ""),
                title=row.get("title", ""),
                description=row.get("short description", ""),
                tech=row.get("tech", ""),
                status=row.get("status", ""),
                rating=_parse_rating(row.get("your rating", "")),
                notes=row.get("rating notes", ""),
            )
        )
    return records

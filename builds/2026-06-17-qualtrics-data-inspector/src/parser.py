"""Parse Qualtrics CSV exports into structured survey data."""

import csv
import io
from dataclasses import dataclass, field
from typing import Optional

# Qualtrics metadata column names (lowercase for case-insensitive matching).
# These are system columns, not question responses.
METADATA_COLUMNS: frozenset = frozenset({
    "startdate", "enddate", "status", "responsestatus", "ipaddress",
    "progress", "duration (in seconds)", "duration", "finished",
    "recordeddate", "responseid", "recipientlastname", "recipientfirstname",
    "recipientemail", "externalreference", "locationlatitude",
    "locationlongitude", "distributionchannel", "userlanguage",
    "qi_flags",
})


@dataclass
class QualtricsColumn:
    """Metadata for one column in a Qualtrics export."""
    name: str
    question_text: str
    import_id: Optional[str] = None


@dataclass
class ParsedSurvey:
    """Fully parsed survey: columns + data rows."""
    columns: list
    rows: list
    is_qualtrics_format: bool
    respondent_count: int

    @property
    def column_names(self) -> list:
        return [c.name for c in self.columns]

    @property
    def question_column_names(self) -> list:
        """Return only question columns, excluding Qualtrics metadata."""
        return [c.name for c in self.columns
                if c.name.lower() not in METADATA_COLUMNS]


def _is_importid_row(row: list) -> bool:
    """Return True if any cell contains a Qualtrics ImportId JSON string."""
    return any('{"ImportId"' in str(cell) for cell in row)


def parse_csv(content: str) -> ParsedSurvey:
    """
    Parse a Qualtrics CSV (or standard CSV) string into a ParsedSurvey.

    Qualtrics format: 3 header rows (column names / question text / ImportId),
    followed by data rows. Standard CSV: 1 header row followed by data rows.

    Raises ValueError if content is empty or has fewer than 2 rows.
    """
    if not content or not content.strip():
        raise ValueError("CSV content is empty")

    reader = csv.reader(io.StringIO(content))
    all_rows = list(reader)
    # Remove trailing empty rows
    while all_rows and not any(all_rows[-1]):
        all_rows.pop()

    if len(all_rows) < 2:
        raise ValueError("CSV must have at least 2 rows (header + one data row)")

    col_names = all_rows[0]

    # Detect Qualtrics format: check rows 1 and 2 for ImportId JSON
    is_qualtrics = False
    importid_row_index = None
    for i in range(1, min(4, len(all_rows))):
        if _is_importid_row(all_rows[i]):
            is_qualtrics = True
            importid_row_index = i
            break

    if is_qualtrics:
        question_text_row = all_rows[1] if importid_row_index > 1 else [""] * len(col_names)
        importid_row = all_rows[importid_row_index]
        data_start = importid_row_index + 1

        columns = [
            QualtricsColumn(
                name=col_names[i] if i < len(col_names) else f"col_{i}",
                question_text=question_text_row[i] if i < len(question_text_row) else "",
                import_id=importid_row[i] if i < len(importid_row) else None,
            )
            for i in range(len(col_names))
        ]
    else:
        columns = [
            QualtricsColumn(name=name, question_text=name)
            for name in col_names
        ]
        data_start = 1

    rows = []
    for raw_row in all_rows[data_start:]:
        # Skip blank rows
        if not any(raw_row):
            continue
        row_dict = {}
        for i, col in enumerate(columns):
            val = raw_row[i] if i < len(raw_row) else None
            row_dict[col.name] = None if (val is None or val == "") else val
        rows.append(row_dict)

    return ParsedSurvey(
        columns=columns,
        rows=rows,
        is_qualtrics_format=is_qualtrics,
        respondent_count=len(rows),
    )

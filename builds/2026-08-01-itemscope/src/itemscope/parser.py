"""CSV parsing and scoring for ItemScope.

Handles two input shapes:
  1. Binary-scored: each item column already contains 0/1 (or true/false,
     correct/incorrect) values.
  2. Raw-option: each item column contains the option letter a student
     selected; a separate answer key maps item -> correct letter.

Both shapes are normalized into a ``ScoredMatrix`` before any statistics run.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field

TRUE_TOKENS = {"1", "true", "t", "correct", "yes", "y"}
FALSE_TOKENS = {"0", "false", "f", "incorrect", "no", "n"}


class ItemScopeParseError(ValueError):
    """Raised when the input CSV cannot be parsed into a response matrix."""


@dataclass
class ResponseMatrix:
    student_ids: list[str]
    item_ids: list[str]
    # raw[i][j] is the raw cell value for student i, item j
    raw: list[list[str]]


@dataclass
class ScoredMatrix:
    student_ids: list[str]
    item_ids: list[str]
    # scores[i][j] is 0 or 1 for student i, item j
    scores: list[list[int]]
    # raw_options[i][j] is the original selected letter, or None if the
    # input was already binary-scored (no distractor analysis possible).
    raw_options: list[list[str | None]] = field(default_factory=list)
    answer_key: dict[str, str] | None = None


def _looks_like_student_id(value: str) -> bool:
    """A column is treated as the student-id column if its values aren't
    plausibly item responses (not 0/1/true/false and not a single letter)."""
    token = value.strip().lower()
    if token in TRUE_TOKENS or token in FALSE_TOKENS:
        return False
    if len(token) == 1 and token.isalpha():
        return False
    return True


def load_response_csv(path: str, student_id_col: str | None = None) -> ResponseMatrix:
    """Load a response CSV into a ResponseMatrix.

    If ``student_id_col`` is not given, the first column is treated as the
    student identifier when its values don't look like item responses.
    """
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            rows = list(reader)
    except FileNotFoundError as exc:
        raise ItemScopeParseError(f"Input file not found: {path}") from exc

    if not rows:
        raise ItemScopeParseError(f"Input file is empty: {path}")

    header = rows[0]
    data_rows = rows[1:]
    if not data_rows:
        raise ItemScopeParseError(f"Input file has a header but no data rows: {path}")

    ncols = len(header)
    for line_no, row in enumerate(data_rows, start=2):
        if len(row) != ncols:
            raise ItemScopeParseError(
                f"Row {line_no} has {len(row)} columns, expected {ncols} "
                f"(based on header): {path}"
            )

    id_col_index = 0
    if student_id_col is not None:
        if student_id_col not in header:
            raise ItemScopeParseError(
                f"--student-id-col '{student_id_col}' not found in header: {header}"
            )
        id_col_index = header.index(student_id_col)
    elif len(header) > 1 and data_rows and _looks_like_student_id(data_rows[0][0]):
        id_col_index = 0
    else:
        id_col_index = None

    if id_col_index is not None:
        item_ids = [h for i, h in enumerate(header) if i != id_col_index]
    else:
        item_ids = list(header)

    student_ids: list[str] = []
    raw: list[list[str]] = []
    for i, row in enumerate(data_rows):
        if id_col_index is not None:
            student_ids.append(row[id_col_index])
            raw.append([v for j, v in enumerate(row) if j != id_col_index])
        else:
            student_ids.append(f"student_{i + 1}")
            raw.append(list(row))

    return ResponseMatrix(student_ids=student_ids, item_ids=item_ids, raw=raw)


def load_answer_key(path: str) -> dict[str, str]:
    """Load a two-column ``item,answer`` CSV into a dict."""
    try:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            rows = list(reader)
    except FileNotFoundError as exc:
        raise ItemScopeParseError(f"Answer key file not found: {path}") from exc

    if not rows:
        raise ItemScopeParseError(f"Answer key file is empty: {path}")

    key: dict[str, str] = {}
    start = 1 if rows[0][:2] == ["item", "answer"] else 0
    for line_no, row in enumerate(rows[start:], start=start + 1):
        if len(row) < 2:
            raise ItemScopeParseError(f"Answer key row {line_no} is malformed: {row}")
        key[row[0]] = row[1].strip()
    return key


def score_matrix(matrix: ResponseMatrix, answer_key: dict[str, str] | None) -> ScoredMatrix:
    """Convert a ResponseMatrix into a ScoredMatrix.

    If ``answer_key`` is provided, cell values are treated as raw option
    letters and scored against the key. Otherwise cell values are treated
    as already-binary (0/1/true/false/correct/incorrect).
    """
    n_students = len(matrix.student_ids)
    n_items = len(matrix.item_ids)
    scores: list[list[int]] = [[0] * n_items for _ in range(n_students)]
    raw_options: list[list[str | None]] = [[None] * n_items for _ in range(n_students)]

    if answer_key is not None:
        missing = [item for item in matrix.item_ids if item not in answer_key]
        if missing:
            raise ItemScopeParseError(
                f"Answer key is missing entries for items: {missing}"
            )
        for i in range(n_students):
            for j, item_id in enumerate(matrix.item_ids):
                selected = matrix.raw[i][j].strip()
                raw_options[i][j] = selected
                scores[i][j] = 1 if selected == answer_key[item_id] else 0
    else:
        for i in range(n_students):
            for j in range(n_items):
                token = matrix.raw[i][j].strip().lower()
                if token in TRUE_TOKENS:
                    scores[i][j] = 1
                elif token in FALSE_TOKENS:
                    scores[i][j] = 0
                else:
                    raise ItemScopeParseError(
                        f"Cell '{matrix.raw[i][j]}' for student "
                        f"'{matrix.student_ids[i]}', item '{matrix.item_ids[j]}' "
                        "is not a recognized binary value and no --key was given "
                        "to score it as a raw option."
                    )

    return ScoredMatrix(
        student_ids=matrix.student_ids,
        item_ids=matrix.item_ids,
        scores=scores,
        raw_options=raw_options,
        answer_key=answer_key,
    )

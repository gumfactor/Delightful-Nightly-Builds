"""CSV ingestion and column auto-detection for TrialScope."""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from typing import Optional


COLUMN_ALIASES: dict[str, list[str]] = {
    "subject": ["subject", "subject_id", "subj", "subj_id", "participant", "participant_id", "id", "pid"],
    "condition": ["condition", "cond", "group", "condition_name", "trial_type"],
    "block": ["block", "trial_block", "block_num", "block_number"],
    "trial": ["trial", "trial_num", "trial_number", "trial_index"],
    "rt": ["rt", "reaction_time", "response_time", "latency", "rt_ms"],
    "accuracy": ["accuracy", "correct", "acc", "is_correct", "response_correct"],
}

REQUIRED_ROLES = ("subject", "condition", "rt", "accuracy")


class ColumnResolutionError(ValueError):
    """Raised when a required column role cannot be resolved from a CSV header."""


@dataclass
class Trial:
    subject: str
    condition: str
    rt_ms: Optional[float]
    correct: Optional[bool]
    block: int
    trial_num: int
    malformed_rt: bool = False
    malformed_accuracy: bool = False


@dataclass
class ParseResult:
    trials: list[Trial] = field(default_factory=list)
    warnings: int = 0
    column_map: dict[str, str] = field(default_factory=dict)


def _normalize(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def resolve_columns(header: list[str], overrides: dict[str, Optional[str]]) -> dict[str, str]:
    """Resolve each required (and optional) role to an actual header column name.

    `overrides` maps role -> explicit column name (or None to auto-detect).
    Raises ColumnResolutionError if a required role cannot be resolved.
    """
    normalized_header = {_normalize(h): h for h in header}
    resolved: dict[str, str] = {}

    for role, aliases in COLUMN_ALIASES.items():
        override = overrides.get(role)
        if override:
            if override not in header:
                raise ColumnResolutionError(
                    f"Column override --{role}-col={override!r} was not found in the CSV header {header}"
                )
            resolved[role] = override
            continue

        for alias in aliases:
            if alias in normalized_header:
                resolved[role] = normalized_header[alias]
                break

    missing = [role for role in REQUIRED_ROLES if role not in resolved]
    if missing:
        raise ColumnResolutionError(
            "Could not auto-detect required column(s): "
            + ", ".join(missing)
            + f". Header was {header}. Specify explicitly with --{missing[0]}-col=<name> (and others as needed)."
        )

    return resolved


def _coerce_float(value: str) -> tuple[Optional[float], bool]:
    if value is None or value.strip() == "":
        return None, True
    try:
        return float(value), False
    except ValueError:
        return None, True


def _coerce_bool(value: str) -> tuple[Optional[bool], bool]:
    if value is None or value.strip() == "":
        return None, True
    v = value.strip().lower()
    if v in ("1", "true", "correct", "yes", "y", "t"):
        return True, False
    if v in ("0", "false", "incorrect", "no", "n", "f"):
        return False, False
    return None, True


def parse_csv(path: str, overrides: Optional[dict[str, Optional[str]]] = None) -> ParseResult:
    """Load a trial-level CSV file and return parsed Trial rows plus a warning count."""
    overrides = overrides or {}
    result = ParseResult()

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        if not header:
            raise ColumnResolutionError("Input CSV has no header row / is empty.")

        column_map = resolve_columns(header, overrides)
        result.column_map = column_map

        per_subject_counter: dict[str, int] = {}

        for row in reader:
            subject = str(row.get(column_map["subject"], "")).strip()
            condition = str(row.get(column_map["condition"], "")).strip()

            rt_raw = row.get(column_map["rt"], "")
            rt_ms, rt_malformed = _coerce_float(rt_raw)

            acc_raw = row.get(column_map["accuracy"], "")
            correct, acc_malformed = _coerce_bool(acc_raw)

            if "block" in column_map:
                block_raw = row.get(column_map["block"], "")
                block_val, block_bad = _coerce_float(block_raw)
                block = int(block_val) if not block_bad and block_val is not None else 1
            else:
                block = 1

            per_subject_counter[subject] = per_subject_counter.get(subject, 0) + 1
            if "trial" in column_map:
                trial_raw = row.get(column_map["trial"], "")
                trial_val, trial_bad = _coerce_float(trial_raw)
                trial_num = int(trial_val) if not trial_bad and trial_val is not None else per_subject_counter[subject]
            else:
                trial_num = per_subject_counter[subject]

            if rt_malformed:
                result.warnings += 1
            if acc_malformed:
                result.warnings += 1

            result.trials.append(
                Trial(
                    subject=subject,
                    condition=condition,
                    rt_ms=rt_ms,
                    correct=correct,
                    block=block,
                    trial_num=trial_num,
                    malformed_rt=rt_malformed,
                    malformed_accuracy=acc_malformed,
                )
            )

    return result

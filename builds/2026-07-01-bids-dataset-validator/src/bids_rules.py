"""BIDS filename parsing and validation rules.

Covers a deliberately-scoped subset of the BIDS specification: the core
entities (sub, ses, task, acq, run, echo) and the raw-MRI suffixes a
typical fMRI/anatomical lab dataset uses. Full BIDS-validator parity
(MEG/EEG/iEEG, derivatives, BEP extensions) is out of scope — see PRD.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath

ENTITY_ORDER = ["sub", "ses", "task", "acq", "run", "echo"]

SUPPORTED_SUFFIXES = {
    "T1w",
    "T2w",
    "bold",
    "sbref",
    "dwi",
    "physio",
    "events",
    "magnitude1",
    "magnitude2",
    "phasediff",
    "epi",
}

NEEDS_JSON_SIDECAR = {
    "T1w",
    "T2w",
    "bold",
    "dwi",
    "sbref",
    "magnitude1",
    "magnitude2",
    "phasediff",
    "epi",
}

DATA_EXTENSIONS = {".nii.gz", ".nii"}

_MULTI_PART_EXTENSIONS = [".nii.gz", ".tsv.gz"]

# Entity values must be alphanumeric only. This is a correctness rule (BIDS
# labels are alphanumeric labels, not free text) and it doubles as a security
# guard: '.', '/', and '..' can never survive into a value, so no path
# segment built from a parsed entity value can escape the dataset root.
_SAFE_VALUE_RE = re.compile(r"^[A-Za-z0-9]+$")


@dataclass
class Finding:
    severity: str  # "error" | "warning"
    code: str
    message: str
    path: str | None = None

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "path": self.path,
        }


@dataclass
class ParsedFile:
    relpath: str
    entities: dict[str, str] = field(default_factory=dict)
    suffix: str = ""
    extension: str = ""
    is_recognized_suffix: bool = False


def split_filename(filename: str) -> tuple[list[str], str, str]:
    """Split a BIDS filename into (entity_parts, suffix, extension)."""
    extension = ""
    base = filename
    for ext in _MULTI_PART_EXTENSIONS:
        if filename.endswith(ext):
            extension = ext
            base = filename[: -len(ext)]
            break
    else:
        if "." in filename:
            base, _, ext_part = filename.rpartition(".")
            extension = "." + ext_part
        else:
            base = filename
            extension = ""

    parts = base.split("_")
    suffix = parts[-1] if parts else ""
    entity_parts = parts[:-1]
    return entity_parts, suffix, extension


def parse_filename(relpath: str) -> tuple[ParsedFile, list[Finding]]:
    """Parse a single dataset-relative file path into a ParsedFile plus any
    per-file findings (malformed entities, bad ordering, unrecognized suffix).
    """
    filename = PurePosixPath(relpath).name
    entity_parts, suffix, extension = split_filename(filename)

    findings: list[Finding] = []
    entities: dict[str, str] = {}
    order_positions: list[int] = []

    for part in entity_parts:
        if "-" not in part:
            findings.append(
                Finding(
                    "error",
                    "MALFORMED_ENTITY",
                    f"'{part}' is not a valid key-value entity",
                    relpath,
                )
            )
            continue
        key, _, value = part.partition("-")
        if not value or not _SAFE_VALUE_RE.match(value):
            findings.append(
                Finding(
                    "error",
                    "INVALID_ENTITY_VALUE",
                    f"Entity value in '{part}' must be alphanumeric",
                    relpath,
                )
            )
            continue
        entities[key] = value
        if key in ENTITY_ORDER:
            order_positions.append(ENTITY_ORDER.index(key))
        else:
            findings.append(
                Finding(
                    "warning",
                    "UNRECOGNIZED_ENTITY",
                    f"Entity key '{key}' is not a recognized core BIDS entity",
                    relpath,
                )
            )

    if "sub" not in entities:
        findings.append(
            Finding(
                "error",
                "MISSING_SUB_ENTITY",
                "Filename does not contain a sub- entity",
                relpath,
            )
        )

    if order_positions != sorted(order_positions):
        findings.append(
            Finding(
                "error",
                "BAD_ENTITY_ORDER",
                "BIDS entities are not in the canonical order "
                "(sub, ses, task, acq, run, echo)",
                relpath,
            )
        )

    is_recognized_suffix = suffix in SUPPORTED_SUFFIXES
    if not is_recognized_suffix:
        findings.append(
            Finding(
                "warning",
                "UNRECOGNIZED_SUFFIX",
                f"Suffix '{suffix}' is not one of the suffixes this tool understands",
                relpath,
            )
        )

    parsed = ParsedFile(
        relpath=relpath,
        entities=entities,
        suffix=suffix,
        extension=extension,
        is_recognized_suffix=is_recognized_suffix,
    )
    return parsed, findings


def _sidecar_relpath(f: ParsedFile) -> str:
    base = f.relpath
    if base.endswith(f.extension) and f.extension:
        base = base[: -len(f.extension)]
    return base + ".json"


def _events_relpath(f: ParsedFile) -> str:
    base = f.relpath
    if base.endswith(f.suffix + f.extension):
        base = base[: -len(f.suffix + f.extension)]
    return base + "events.tsv"


def check_dataset_description(root, existing_relpaths: set[str]) -> list[Finding]:
    import json

    if "dataset_description.json" not in existing_relpaths:
        return [
            Finding(
                "error",
                "MISSING_DATASET_DESCRIPTION",
                "dataset_description.json not found at dataset root",
            )
        ]
    dd_path = root / "dataset_description.json"
    try:
        data = json.loads(dd_path.read_text())
    except json.JSONDecodeError:
        return [
            Finding(
                "error",
                "INVALID_DATASET_DESCRIPTION",
                "dataset_description.json is not valid JSON",
            )
        ]
    findings = []
    for required_field in ("Name", "BIDSVersion"):
        if required_field not in data:
            findings.append(
                Finding(
                    "error",
                    "MISSING_DATASET_DESCRIPTION_FIELD",
                    f"dataset_description.json is missing required field '{required_field}'",
                )
            )
    return findings


def check_sidecars(files: list[ParsedFile], existing_relpaths: set[str]) -> list[Finding]:
    findings = []
    for f in files:
        if f.suffix in NEEDS_JSON_SIDECAR and f.extension in DATA_EXTENSIONS:
            sidecar = _sidecar_relpath(f)
            if sidecar not in existing_relpaths:
                findings.append(
                    Finding(
                        "warning",
                        "MISSING_SIDECAR",
                        f"No matching .json sidecar for {f.relpath}",
                        f.relpath,
                    )
                )
    return findings


def check_events(files: list[ParsedFile], existing_relpaths: set[str]) -> list[Finding]:
    findings = []
    for f in files:
        if f.suffix != "bold" or f.extension not in DATA_EXTENSIONS:
            continue
        task = f.entities.get("task", "")
        if "rest" in task.lower():
            continue
        events_path = _events_relpath(f)
        if events_path not in existing_relpaths:
            findings.append(
                Finding(
                    "warning",
                    "MISSING_EVENTS",
                    f"No matching events.tsv for task run {f.relpath}",
                    f.relpath,
                )
            )
    return findings


def check_zero_padding(files: list[ParsedFile]) -> list[Finding]:
    findings = []
    for key in ("sub", "ses", "run"):
        widths: dict[int, list[str]] = {}
        for f in files:
            value = f.entities.get(key)
            if value and value.isdigit():
                widths.setdefault(len(value), []).append(f.relpath)
        if len(widths) > 1:
            majority_width = max(widths, key=lambda w: len(widths[w]))
            for width, paths in widths.items():
                if width == majority_width:
                    continue
                for path in paths:
                    findings.append(
                        Finding(
                            "warning",
                            "INCONSISTENT_PADDING",
                            f"Entity '{key}' in {path} does not match the "
                            f"dataset's dominant zero-padding width "
                            f"({majority_width} digits)",
                            path,
                        )
                    )
    return findings


def check_duplicates(files: list[ParsedFile]) -> list[Finding]:
    findings = []
    groups: dict[tuple, list[str]] = {}
    for f in files:
        key = (tuple(sorted(f.entities.items())), f.suffix, f.extension)
        groups.setdefault(key, []).append(f.relpath)
    for paths in groups.values():
        if len(paths) > 1:
            for path in sorted(paths)[1:]:
                findings.append(
                    Finding(
                        "error",
                        "DUPLICATE_FILE",
                        f"{path} resolves to the same entities/suffix as "
                        f"{sorted(paths)[0]}",
                        path,
                    )
                )
    return findings


def check_session_consistency(files: list[ParsedFile]) -> list[Finding]:
    subjects_with_session: set[str] = set()
    subjects_without_session: set[str] = set()
    for f in files:
        sub = f.entities.get("sub")
        if not sub:
            continue
        if "ses" in f.entities:
            subjects_with_session.add(sub)
        else:
            subjects_without_session.add(sub)

    inconsistent = subjects_without_session & subjects_with_session
    findings = []
    for sub in sorted(inconsistent):
        findings.append(
            Finding(
                "warning",
                "INCONSISTENT_SESSION_STRUCTURE",
                f"Subject '{sub}' has files both with and without a ses- entity",
            )
        )
    # Subjects missing sessions entirely while others in the dataset use them
    if subjects_with_session and subjects_without_session - inconsistent:
        for sub in sorted(subjects_without_session - inconsistent):
            findings.append(
                Finding(
                    "warning",
                    "INCONSISTENT_SESSION_STRUCTURE",
                    f"Subject '{sub}' has no session-level organization while "
                    "other subjects in this dataset do",
                )
            )
    return findings

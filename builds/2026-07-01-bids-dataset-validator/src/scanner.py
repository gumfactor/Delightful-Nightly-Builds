"""Directory walk over a dataset root, producing ParsedFile records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .bids_rules import (
    Finding,
    ParsedFile,
    check_dataset_description,
    check_duplicates,
    check_events,
    check_session_consistency,
    check_sidecars,
    check_zero_padding,
    parse_filename,
)

_SKIP_NAMES = {"dataset_description.json", "README", "CHANGES", ".bidsignore"}


@dataclass
class ScanResult:
    root: Path
    files: list[ParsedFile]
    findings: list[Finding]

    @property
    def subjects(self) -> set[str]:
        return {f.entities["sub"] for f in self.files if "sub" in f.entities}


def scan_directory(root: Path) -> tuple[list[ParsedFile], set[str]]:
    """Walk the dataset root and parse every data file's name.

    Returns the parsed files and the set of all relative paths present
    (used by cross-file rules to check for sidecar/events companions).
    """
    files: list[ParsedFile] = []
    existing_relpaths: set[str] = set()

    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if path.name.startswith("."):
            continue
        relpath = path.relative_to(root).as_posix()
        existing_relpaths.add(relpath)
        if path.name in _SKIP_NAMES:
            continue
        parsed, _ = parse_filename(relpath)
        files.append(parsed)

    return files, existing_relpaths


def validate_dataset(root: Path) -> ScanResult:
    """Run the full scan + rule pipeline over a dataset directory."""
    if not root.exists():
        raise FileNotFoundError(f"Dataset path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Dataset path is not a directory: {root}")

    files, existing_relpaths = scan_directory(root)

    findings: list[Finding] = []
    for f in files:
        _, per_file_findings = parse_filename(f.relpath)
        findings.extend(per_file_findings)

    findings.extend(check_dataset_description(root, existing_relpaths))
    findings.extend(check_sidecars(files, existing_relpaths))
    findings.extend(check_events(files, existing_relpaths))
    findings.extend(check_zero_padding(files))
    findings.extend(check_duplicates(files))
    findings.extend(check_session_consistency(files))

    return ScanResult(root=root, files=files, findings=findings)

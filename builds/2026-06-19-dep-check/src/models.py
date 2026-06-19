"""Data models for dep-check."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Requirement:
    name: str                      # Normalised: lowercase, hyphens
    pinned_version: Optional[str]  # Exact version string (None if no pin)
    specifier: Optional[str]       # Full specifier, e.g. ">=2.28.0"
    source_file: str               # Which file this came from


@dataclass
class PackageResult:
    req: Requirement
    latest_version: Optional[str]
    pinned_upload_date: Optional[str]   # ISO date string or None
    days_since_pinned: Optional[int]
    # "up-to-date" | "patch" | "minor" | "major" | "unpinned" | "unknown" | "error"
    status: str
    yanked: bool = False
    yanked_reason: Optional[str] = None


@dataclass
class Summary:
    total: int = 0
    up_to_date: int = 0
    patch: int = 0
    minor: int = 0
    major: int = 0
    unpinned: int = 0
    yanked: int = 0
    unknown: int = 0

    @property
    def needs_update(self) -> int:
        return self.patch + self.minor + self.major

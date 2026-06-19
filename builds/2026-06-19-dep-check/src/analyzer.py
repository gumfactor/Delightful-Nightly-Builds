"""Pure analysis functions: version comparison, staleness, summary."""
import re
from datetime import datetime, timezone
from typing import Optional, List
from src.models import Requirement, PackageResult, Summary


def _parse_version(version_str: str) -> tuple:
    """Convert a version string to a comparable tuple of ints.

    "2.28.1" → (2, 28, 1)
    "3.0.0a1" → stripped to numeric prefix (3, 0, 0)
    """
    # Strip local version identifiers and pre/post/dev suffixes
    clean = re.split(r"[^0-9.]", version_str)[0].rstrip(".")
    if not clean:
        return (0,)
    try:
        return tuple(int(x) for x in clean.split("."))
    except ValueError:
        return (0,)


def compare_versions(pinned: Optional[str], latest: Optional[str]) -> str:
    """Classify how the pinned version relates to the latest version.

    Returns one of: "up-to-date" | "patch" | "minor" | "major" | "unpinned" | "unknown"
    """
    if pinned is None:
        return "unpinned"
    if latest is None:
        return "unknown"

    p = _parse_version(pinned)
    l = _parse_version(latest)

    if p >= l:
        return "up-to-date"

    # Pad shorter tuple
    max_len = max(len(p), len(l))
    p = p + (0,) * (max_len - len(p))
    l = l + (0,) * (max_len - len(l))

    if l[0] > p[0]:
        return "major"
    if len(l) > 1 and l[1] > p[1]:
        return "minor"
    return "patch"


def classify_staleness(days: Optional[int]) -> str:
    """Classify how stale a pinned release is by age in days.

    Returns: "fresh" | "aging" | "old" | "very-old" | "unknown"
    """
    if days is None:
        return "unknown"
    if days <= 30:
        return "fresh"
    if days <= 180:
        return "aging"
    if days <= 365:
        return "old"
    return "very-old"


def _days_since(upload_date_str: Optional[str]) -> Optional[int]:
    """Compute days between upload_date_str (ISO 8601) and now UTC."""
    if not upload_date_str:
        return None
    # Normalise: "2023-01-15T12:00:00Z" or "2023-01-15T12:00:00"
    clean = upload_date_str.rstrip("Z").split(".")[0]
    try:
        dt = datetime.fromisoformat(clean).replace(tzinfo=timezone.utc)
        return (datetime.now(tz=timezone.utc) - dt).days
    except ValueError:
        return None


def build_result(
    req: Requirement,
    latest_version: Optional[str],
    pinned_upload_date: Optional[str],
    yanked: bool,
    yanked_reason: Optional[str],
) -> PackageResult:
    """Combine raw PyPI data with a Requirement into a PackageResult."""
    status = compare_versions(req.pinned_version, latest_version)
    days = _days_since(pinned_upload_date)
    return PackageResult(
        req=req,
        latest_version=latest_version,
        pinned_upload_date=pinned_upload_date,
        days_since_pinned=days,
        status=status,
        yanked=yanked,
        yanked_reason=yanked_reason,
    )


def compute_summary(results: List[PackageResult]) -> Summary:
    """Aggregate a list of PackageResults into a Summary."""
    s = Summary(total=len(results))
    for r in results:
        if r.yanked:
            s.yanked += 1
        status = r.status
        if status == "up-to-date":
            s.up_to_date += 1
        elif status == "patch":
            s.patch += 1
        elif status == "minor":
            s.minor += 1
        elif status == "major":
            s.major += 1
        elif status == "unpinned":
            s.unpinned += 1
        else:
            s.unknown += 1
    return s

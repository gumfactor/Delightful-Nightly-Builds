"""Data models and small helpers shared across modules."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def parse_ts(value: str | None) -> datetime | None:
    """Parse a GitHub ISO-8601 timestamp (``...Z``); return None when missing or malformed."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def seconds_between(start: datetime | None, end: datetime | None) -> float:
    """Non-negative seconds between two datetimes; 0 if either is missing."""
    if start is None or end is None:
        return 0.0
    return max(0.0, (end - start).total_seconds())


@dataclass
class Step:
    name: str
    seconds: float
    conclusion: str | None


@dataclass
class Job:
    run_id: int
    name: str
    labels: list[str]
    seconds: float
    conclusion: str | None
    steps: list[Step] = field(default_factory=list)


@dataclass
class Run:
    id: int
    repo: str
    workflow: str
    path: str
    event: str
    branch: str
    sha: str
    attempt: int
    conclusion: str | None
    started: datetime | None
    seconds: float
    url: str = ""
    jobs: list[Job] = field(default_factory=list)

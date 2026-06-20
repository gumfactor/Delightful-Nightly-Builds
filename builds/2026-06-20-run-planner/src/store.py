"""Persistent run log backed by runs.json in the build root."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Default path — tests patch this to a tmp file
RUNS_FILE: Path = Path(__file__).parent.parent / "runs.json"


def _load(path: Optional[Path] = None) -> dict:
    p = path or RUNS_FILE
    if not p.exists():
        return {"runs": []}
    with open(p) as f:
        return json.load(f)


def _save(data: dict, path: Optional[Path] = None) -> None:
    p = path or RUNS_FILE
    with open(p, "w") as f:
        json.dump(data, f, indent=2)


def parse_duration(time_str: str) -> int:
    """Parse 'mm:ss' or 'hh:mm:ss' into total seconds."""
    parts = time_str.strip().split(":")
    if len(parts) == 2:
        try:
            return int(parts[0]) * 60 + int(parts[1])
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str!r}. Use mm:ss or hh:mm:ss")
    elif len(parts) == 3:
        try:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str!r}. Use mm:ss or hh:mm:ss")
    else:
        raise ValueError(f"Invalid time format: {time_str!r}. Use mm:ss or hh:mm:ss")


def format_pace(distance_km: float, duration_seconds: int) -> str:
    """Return pace as 'mm:ss per km'."""
    if distance_km <= 0:
        return "--:--"
    pace_sec = duration_seconds / distance_km
    mins = int(pace_sec // 60)
    secs = int(pace_sec % 60)
    return f"{mins}:{secs:02d}"


def log_run(
    date: str,
    distance_km: float,
    duration_seconds: int,
    effort: str = "moderate",
    notes: str = "",
    _path: Optional[Path] = None,
) -> dict:
    """Persist a run and return the saved record."""
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date: {date!r}. Use YYYY-MM-DD")

    if distance_km <= 0:
        raise ValueError(f"Distance must be positive, got {distance_km}")
    if duration_seconds <= 0:
        raise ValueError(f"Duration must be positive, got {duration_seconds}")

    valid_efforts = {"easy", "moderate", "hard"}
    if effort not in valid_efforts:
        raise ValueError(f"Effort must be one of {sorted(valid_efforts)}, got {effort!r}")

    data = _load(_path)
    run_id = f"{date}-{len(data['runs']) + 1:03d}"

    run = {
        "id": run_id,
        "date": date,
        "distance_km": round(distance_km, 2),
        "duration_seconds": duration_seconds,
        "effort": effort,
        "notes": notes,
        "pace": format_pace(distance_km, duration_seconds),
    }
    data["runs"].append(run)
    _save(data, _path)
    return run


def list_runs(_path: Optional[Path] = None) -> List[dict]:
    """Return all runs sorted by date ascending."""
    data = _load(_path)
    return sorted(data["runs"], key=lambda r: r["date"])

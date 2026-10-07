"""Generate data/sample_data.json: deterministic, ILLUSTRATIVE series (not real statistics)."""
from __future__ import annotations

import json
import math
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from canpulse import config  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "data" / "sample_data.json"
END = date(2026, 9, 30)


def monthly(start: int, base: float, drift: float, wobble: float, rng: random.Random) -> list[list]:
    pts, val, d = [], base, date(start, 1, 1)
    while d <= END.replace(day=1):
        val += drift + rng.gauss(0, wobble) + math.sin(d.month / 12 * 6.28) * wobble * 0.3
        pts.append([d.isoformat(), round(val, 3)])
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return pts


def daily(start: int, base: float, vol: float, rng: random.Random, floor: float | None = None) -> list[list]:
    pts, val, d = [], base, date(start, 1, 1)
    while d <= END:
        if d.weekday() < 5:
            val += rng.gauss(0, vol)
            if floor is not None:
                val = max(floor, val)
            pts.append([d.isoformat(), round(val, 4)])
        d += timedelta(days=1)
    return pts


def main() -> None:
    rng = random.Random(7)
    shapes = {
        "cpi": monthly(2006, 100, 0.19, 0.12, rng),
        "policy_rate": daily(2006, 4.0, 0.004, rng, 0.25),
        "gov10y": daily(2006, 4.0, 0.03, rng, 0.5),
        "gov2y": daily(2006, 3.8, 0.03, rng, 0.2),
        "usdcad": daily(2006, 1.15, 0.003, rng, 0.9),
        "unemployment": monthly(2006, 6.5, 0.0, 0.12, rng),
        "participation": monthly(2006, 67.0, -0.005, 0.1, rng),
        "gdp": monthly(2006, 1_300_000, 1500, 2500, rng),
        "retail": monthly(2006, 30_000_000, 55_000, 150_000, rng),
        "housing": monthly(2006, 85, 0.12, 0.15, rng),
    }
    series = {}
    for spec in config.INDICATORS:
        series[spec["id"]] = {k: spec[k] for k in ("id", "label", "unit", "source", "freq", "higher_is", "group")}
        series[spec["id"]]["points"] = shapes[spec["id"]]
    doc = {"fetched_at": "2026-09-30T00:00:00Z", "sample": True, "series": series, "errors": {}}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(doc), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

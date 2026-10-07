"""Pure analysis: changes, percentiles, derived series, signals."""
from __future__ import annotations

import bisect
import statistics
from datetime import date, timedelta
from typing import Any

from . import config

Points = list[list]  # [[iso, value], ...] ascending


def _d(iso: str) -> date:
    return date.fromisoformat(iso)


def value_on_or_before(points: Points, target: str) -> float | None:
    """Last observation dated <= target, or None if none exists."""
    dates = [p[0] for p in points]
    i = bisect.bisect_right(dates, target)
    return points[i - 1][1] if i else None


def window(points: Points, years: float) -> Points:
    if not points:
        return []
    cutoff = (_d(points[-1][0]) - timedelta(days=round(365.25 * years))).isoformat()
    return [p for p in points if p[0] >= cutoff]


def is_level_series(unit: str) -> bool:
    """Level series (indices, dollars) use % change; rate series use point change."""
    return unit not in ("%", "pp", "CAD per USD")


def change(points: Points, days: int, level: bool) -> float | None:
    if len(points) < 2:
        return None
    latest_date, latest = points[-1]
    base_date = (_d(latest_date) - timedelta(days=days)).isoformat()
    # require history reaching back at least as far as the base date, with a small tolerance
    if points[0][0] > (_d(base_date) + timedelta(days=20)).isoformat():
        return None
    base = value_on_or_before(points, (_d(base_date) + timedelta(days=15)).isoformat()
                              if days >= 300 else base_date)
    if base is None:
        return None
    if level:
        return None if base == 0 else (latest / base - 1) * 100
    return latest - base


def percentile_rank(values: list[float], x: float) -> float:
    if not values:
        return 50.0
    below = sum(1 for v in values if v < x)
    equal = sum(1 for v in values if v == x)
    return 100.0 * (below + 0.5 * equal) / len(values)


def zscore(values: list[float], x: float) -> float | None:
    if len(values) < 3:
        return None
    sd = statistics.pstdev(values)
    return None if sd == 0 else (x - statistics.fmean(values)) / sd


def trend(points: Points, freq: str) -> str:
    """rising / falling / flat comparing latest with ~3 months earlier, relative to noise."""
    if len(points) < 4:
        return "flat"
    latest = points[-1]
    base = value_on_or_before(points, (_d(latest[0]) - timedelta(days=91)).isoformat())
    if base is None:
        return "flat"
    recent = [p[1] for p in window(points, 3)]
    sd = statistics.pstdev(recent) if len(recent) > 2 else 0
    threshold = max(0.25 * sd, 1e-9)
    delta = latest[1] - base
    if delta > threshold:
        return "rising"
    if delta < -threshold:
        return "falling"
    return "flat"


def classify(sid: str, higher_is: str, tr: str, z: float | None, latest: float) -> tuple[str, str]:
    """Return (signal, reason). signal in good/bad/watch/neutral."""
    if sid == "curve":
        if latest < 0:
            return "watch", "Yield curve inverted"
        return "neutral", "Curve upward sloping"
    if sid == "real_rate":
        if latest < 0:
            return "watch", "Negative real policy rate (stimulative)"
        if latest > 2:
            return "watch", "Restrictive real policy rate"
        return "neutral", "Real rate moderate"
    if z is not None and abs(z) >= 2:
        return "watch", f"Unusual vs 5-yr range (z={z:+.1f})"
    if higher_is == "good":
        return {"rising": ("good", "Improving"), "falling": ("bad", "Deteriorating")}.get(
            tr, ("neutral", "Steady"))
    if higher_is == "bad":
        return {"rising": ("bad", "Worsening"), "falling": ("good", "Improving")}.get(
            tr, ("neutral", "Steady"))
    return "neutral", {"rising": "Rising", "falling": "Falling"}.get(tr, "Steady")


def analyze_series(s: dict[str, Any], today: date | None = None) -> dict[str, Any]:
    pts: Points = s["points"]
    today = today or date.today()
    latest_date, latest = pts[-1]
    level = is_level_series(s["unit"])
    five = [p[1] for p in window(pts, 5)]
    tr = trend(pts, s["freq"])
    z = zscore(five, latest)
    signal, reason = classify(s["id"], s["higher_is"], tr, z, latest)
    age = (today - _d(latest_date)).days
    return {
        "id": s["id"], "latest": latest, "latest_date": latest_date,
        "chg_1m": change(pts, 30, level) if s["freq"] == "D" else change(pts, 31, level),
        "yoy": change(pts, 365, level),
        "yoy_kind": "pct" if level else "pp",
        "pct5y": round(percentile_rank(five, latest), 1),
        "z": None if z is None else round(z, 2),
        "trend": tr, "signal": signal, "reason": reason,
        "age_days": age, "stale": age > config.STALE_DAYS[s["freq"]],
    }


def build_derived(series: dict[str, dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    meta = {d["id"]: d for d in config.DERIVED}
    if "cpi" in series and "policy_rate" in series:
        cpi, rate = series["cpi"]["points"], series["policy_rate"]["points"]
        pts = []
        for iso, val in cpi:
            prior = value_on_or_before(cpi, (_d(iso) - timedelta(days=365) + timedelta(days=15)).isoformat())
            if prior is None or cpi[0][0] > (_d(iso) - timedelta(days=350)).isoformat():
                continue
            pol = value_on_or_before(rate, iso)
            if pol is None:
                continue
            pts.append([iso, round(pol - (val / prior - 1) * 100, 3)])
        if pts:
            out["real_rate"] = _mk(meta["real_rate"], pts)
    if "gov10y" in series and "gov2y" in series:
        two = dict(series["gov2y"]["points"])
        pts = [[d, round(v - two[d], 3)] for d, v in series["gov10y"]["points"] if d in two]
        if pts:
            out["curve"] = _mk(meta["curve"], pts)
    return out


def _mk(meta: dict, pts: Points) -> dict:
    return {"id": meta["id"], "label": meta["label"], "unit": meta["unit"], "source": "derived",
            "freq": meta["freq"], "higher_is": meta["higher_is"], "group": meta["group"],
            "note": meta.get("note", ""), "points": pts}


def analyze_all(series: dict[str, dict], today: date | None = None) -> tuple[dict[str, dict], dict[str, dict]]:
    """Return (all series incl. derived, stats by id)."""
    full = dict(series)
    full.update(build_derived(series))
    stats = {sid: analyze_series(s, today) for sid, s in full.items() if s.get("points")}
    return full, stats

"""Relative Rotation Graph (RRG)-style analytics.

All formulas are documented in PRD.md. This module is pure computation:
it takes already-fetched price series and returns structured results,
with no I/O of its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean, pstdev, stdev


DEFAULT_SECTORS = [
    "XLK", "XLF", "XLE", "XLV", "XLI",
    "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC",
]
DEFAULT_BENCHMARK = "SPY"

QUADRANT_LEADING = "Leading"
QUADRANT_WEAKENING = "Weakening"
QUADRANT_LAGGING = "Lagging"
QUADRANT_IMPROVING = "Improving"


class InsufficientDataError(Exception):
    """Raised when there isn't enough price history to compute a full result."""


@dataclass(frozen=True)
class SectorPoint:
    date: str
    rs_ratio: float
    rs_momentum: float
    quadrant: str


@dataclass(frozen=True)
class SectorResult:
    ticker: str
    tail: list  # list[SectorPoint], oldest first
    latest: SectorPoint
    previous: SectorPoint | None  # point one trading day before latest, if available


def classify_quadrant(rs_ratio: float, rs_momentum: float) -> str:
    """Fixed convention: a value exactly at 100 counts as the '>=100' side."""
    if rs_ratio >= 100:
        return QUADRANT_LEADING if rs_momentum >= 100 else QUADRANT_WEAKENING
    return QUADRANT_IMPROVING if rs_momentum >= 100 else QUADRANT_LAGGING


def _cross_sectional_zscores(values_by_ticker: dict) -> dict:
    """Z-score a dict[ticker -> float] across its own tickers at one point in time.

    Degenerate-case guard: fewer than 2 valid values, or a population with
    zero spread, yields a z-score of 0.0 for every ticker rather than NaN
    or a division error.
    """
    valid = {t: v for t, v in values_by_ticker.items() if v is not None}
    if len(valid) < 2:
        return {t: (0.0 if v is not None else None) for t, v in values_by_ticker.items()}
    vals = list(valid.values())
    mu = mean(vals)
    sigma = stdev(vals)  # sample std, ddof=1
    if sigma == 0:
        return {t: (0.0 if v is not None else None) for t, v in values_by_ticker.items()}
    return {
        t: ((v - mu) / sigma if v is not None else None)
        for t, v in values_by_ticker.items()
    }


def _sma(series: list, window: int, index: int) -> float | None:
    """Simple moving average of series[index-window+1 .. index], or None if unavailable."""
    if index - window + 1 < 0:
        return None
    segment = series[index - window + 1: index + 1]
    return mean(segment)


def compute_rs_lines(prices: dict, benchmark: str) -> dict:
    """RS_i(t) = 100 * close_i(t) / close_benchmark(t) for every non-benchmark ticker.

    `prices` maps ticker -> list of (date_str, close) tuples, all aligned to the
    same dates in the same order (callers are responsible for alignment).
    Returns dict[ticker -> list[(date_str, rs_value)]].
    """
    if benchmark not in prices:
        raise InsufficientDataError(f"Benchmark '{benchmark}' missing from price data")
    bench_series = prices[benchmark]
    rs_lines = {}
    for ticker, series in prices.items():
        if ticker == benchmark:
            continue
        if len(series) != len(bench_series):
            raise InsufficientDataError(
                f"'{ticker}' has {len(series)} price points, benchmark has {len(bench_series)}"
            )
        rs_lines[ticker] = [
            (date, 100.0 * close / bench_close)
            for (date, close), (_, bench_close) in zip(series, bench_series)
        ]
    return rs_lines


def compute_rotation(
    prices: dict,
    benchmark: str = DEFAULT_BENCHMARK,
    ratio_window: int = 10,
    momentum_window: int = 10,
    tail_length: int = 10,
) -> dict:
    """Compute RS-Ratio / RS-Momentum / quadrant history for every sector.

    Returns dict[ticker -> SectorResult].
    Raises InsufficientDataError if there isn't enough history to produce
    at least one valid point after the ratio/momentum warm-up period.
    """
    rs_lines = compute_rs_lines(prices, benchmark)
    sectors = list(rs_lines.keys())
    if not sectors:
        raise InsufficientDataError("No sector tickers provided alongside the benchmark")

    n_days = len(next(iter(rs_lines.values())))
    dates = [d for d, _ in next(iter(rs_lines.values()))]
    rs_values = {t: [v for _, v in rs_lines[t]] for t in sectors}

    # Step 1: smoothed RS per sector per day
    sma_rs = {t: [_sma(rs_values[t], ratio_window, i) for i in range(n_days)] for t in sectors}

    # Step 2: cross-sectional z-score -> RS-Ratio, per day
    rs_ratio = {t: [None] * n_days for t in sectors}
    for i in range(n_days):
        day_values = {t: sma_rs[t][i] for t in sectors}
        zscores = _cross_sectional_zscores(day_values)
        for t in sectors:
            z = zscores[t]
            rs_ratio[t][i] = None if z is None else 100.0 + z

    # Step 3: raw momentum (simple difference) -> cross-sectional z-score -> RS-Momentum
    raw_momentum = {t: [None] * n_days for t in sectors}
    for t in sectors:
        for i in range(n_days):
            if i - momentum_window < 0:
                continue
            prior = rs_ratio[t][i - momentum_window]
            current = rs_ratio[t][i]
            if prior is not None and current is not None:
                raw_momentum[t][i] = current - prior

    rs_momentum = {t: [None] * n_days for t in sectors}
    for i in range(n_days):
        day_values = {t: raw_momentum[t][i] for t in sectors}
        zscores = _cross_sectional_zscores(day_values)
        for t in sectors:
            z = zscores[t]
            rs_momentum[t][i] = None if z is None else 100.0 + z

    results = {}
    for t in sectors:
        points = [
            SectorPoint(
                date=dates[i],
                rs_ratio=rs_ratio[t][i],
                rs_momentum=rs_momentum[t][i],
                quadrant=classify_quadrant(rs_ratio[t][i], rs_momentum[t][i]),
            )
            for i in range(n_days)
            if rs_ratio[t][i] is not None and rs_momentum[t][i] is not None
        ]
        if not points:
            raise InsufficientDataError(
                f"Not enough history for '{t}' to compute a single valid Ratio/Momentum point "
                f"(need at least ratio_window + momentum_window = {ratio_window + momentum_window} "
                f"trading days, got {n_days})"
            )
        tail = points[-tail_length:]
        latest = points[-1]
        previous = points[-2] if len(points) >= 2 else None
        results[t] = SectorResult(ticker=t, tail=tail, latest=latest, previous=previous)

    return results

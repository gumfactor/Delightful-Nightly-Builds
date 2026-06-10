"""Generate inline SVG sparklines from a list of closing prices."""

from __future__ import annotations


_WIDTH = 80
_HEIGHT = 28
_STROKE_WIDTH = 1.5
_COLOR_UP = "#4ade80"      # green
_COLOR_DOWN = "#f87171"    # red
_COLOR_FLAT = "#94a3b8"    # slate gray
_COLOR_NONE = "#334155"    # dark background placeholder


def _trend_color(prices: list[float]) -> str:
    """Return a hex color based on whether prices trended up, down, or flat."""
    if len(prices) < 2:
        return _COLOR_FLAT
    delta = prices[-1] - prices[0]
    if delta > 0:
        return _COLOR_UP
    if delta < 0:
        return _COLOR_DOWN
    return _COLOR_FLAT


def _normalize_prices(prices: list[float], height: int) -> list[float]:
    """
    Scale prices to [2, height-2] so the line stays inside the SVG bounds.
    Returns y-coordinates (SVG: 0 is top), so higher price = lower y.
    """
    min_p = min(prices)
    max_p = max(prices)
    span = max_p - min_p

    usable = height - 4  # 2px padding top and bottom
    if span == 0:
        # Flat line in the middle
        return [height / 2] * len(prices)

    return [2 + usable * (1.0 - (p - min_p) / span) for p in prices]


def make_sparkline(prices: list[float]) -> str:
    """
    Return an inline SVG element (no <svg> wrapper needed; returned as full <svg> tag).
    Width=80, Height=28. Gracefully handles 0 or 1 data points.
    """
    if not prices:
        # Return a flat placeholder line
        mid = _HEIGHT / 2
        return (
            f'<svg width="{_WIDTH}" height="{_HEIGHT}" viewBox="0 0 {_WIDTH} {_HEIGHT}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<line x1="4" y1="{mid:.1f}" x2="{_WIDTH-4}" y2="{mid:.1f}" '
            f'stroke="{_COLOR_NONE}" stroke-width="{_STROKE_WIDTH}"/>'
            f"</svg>"
        )

    if len(prices) == 1:
        mid = _HEIGHT / 2
        color = _COLOR_FLAT
        return (
            f'<svg width="{_WIDTH}" height="{_HEIGHT}" viewBox="0 0 {_WIDTH} {_HEIGHT}" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<circle cx="{_WIDTH // 2}" cy="{mid:.1f}" r="2" fill="{color}"/>'
            f"</svg>"
        )

    color = _trend_color(prices)
    ys = _normalize_prices(prices, _HEIGHT)
    n = len(prices)
    x_step = (_WIDTH - 8) / (n - 1)  # 4px padding each side

    points = " ".join(
        f"{4 + i * x_step:.1f},{ys[i]:.1f}" for i in range(n)
    )

    # Dot at the last point
    last_x = 4 + (n - 1) * x_step
    last_y = ys[-1]

    return (
        f'<svg width="{_WIDTH}" height="{_HEIGHT}" viewBox="0 0 {_WIDTH} {_HEIGHT}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<polyline points="{points}" fill="none" stroke="{color}" '
        f'stroke-width="{_STROKE_WIDTH}" stroke-linejoin="round" stroke-linecap="round"/>'
        f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="2" fill="{color}"/>'
        f"</svg>"
    )

"""Real, publicly published CRA annual contribution limit tables.

Sources cross-checked against multiple independent public references
(ratehub.ca, wealthsimple.com, lifeannuities.com, TD/RBC/National Bank
advisor pages) on 2026-09-09; the TFSA table's implied cumulative totals
($102,000 by 2025, $109,000 by 2026 for someone eligible since 2009) match
the widely-cited public figures, which was used as a cross-check before
committing to these numbers. Direct fetch of the canonical canada.ca page
was blocked by this build container's egress proxy (a build-environment
constraint, not a design choice) — see BUILD_LOG.md.

Both accounts began in 2009. Every dollar figure below is CAD.
"""

from __future__ import annotations

TFSA_ANNUAL_LIMITS: dict[int, float] = {
    2009: 5_000,
    2010: 5_000,
    2011: 5_000,
    2012: 5_000,
    2013: 5_500,
    2014: 5_500,
    2015: 10_000,
    2016: 5_500,
    2017: 5_500,
    2018: 5_500,
    2019: 6_000,
    2020: 6_000,
    2021: 6_000,
    2022: 6_000,
    2023: 6_500,
    2024: 7_000,
    2025: 7_000,
    2026: 7_000,
}

RRSP_ANNUAL_LIMITS: dict[int, float] = {
    2009: 21_000,
    2010: 22_000,
    2011: 22_450,
    2012: 22_970,
    2013: 23_820,
    2014: 24_270,
    2015: 24_930,
    2016: 25_370,
    2017: 26_010,
    2018: 26_230,
    2019: 26_500,
    2020: 27_230,
    2021: 27_830,
    2022: 29_210,
    2023: 30_780,
    2024: 31_560,
    2025: 32_490,
    2026: 33_810,
}

TFSA_FIRST_YEAR = min(TFSA_ANNUAL_LIMITS)
RRSP_FIRST_YEAR = min(RRSP_ANNUAL_LIMITS)
LAST_TABULATED_YEAR = max(TFSA_ANNUAL_LIMITS)

RRSP_OVERCONTRIBUTION_GRACE = 2_000.0
OVERCONTRIBUTION_MONTHLY_PENALTY_RATE = 0.01
RRIF_CONVERSION_AGE = 71
TFSA_ELIGIBILITY_AGE = 18


class LimitTableError(ValueError):
    """Raised when a year falls outside the tabulated limit range."""


def tfsa_limit(year: int) -> float:
    """Return the TFSA annual dollar limit for ``year``."""
    if year not in TFSA_ANNUAL_LIMITS:
        raise LimitTableError(
            f"No TFSA limit tabulated for {year}. "
            f"Known range: {TFSA_FIRST_YEAR}-{LAST_TABULATED_YEAR}."
        )
    return TFSA_ANNUAL_LIMITS[year]


def rrsp_limit(year: int) -> float:
    """Return the RRSP annual dollar limit for ``year``."""
    if year not in RRSP_ANNUAL_LIMITS:
        raise LimitTableError(
            f"No RRSP limit tabulated for {year}. "
            f"Known range: {RRSP_FIRST_YEAR}-{LAST_TABULATED_YEAR}."
        )
    return RRSP_ANNUAL_LIMITS[year]

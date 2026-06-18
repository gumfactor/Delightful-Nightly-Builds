"""Distributional statistics, normality tests, and correlation utilities."""

import math
from typing import Optional


# ── Core numeric utilities ────────────────────────────────────────────────────

def _mean(values: list) -> float:
    return sum(values) / len(values)


def _variance(values: list, ddof: int = 1) -> float:
    """Sample variance with given degrees-of-freedom correction."""
    n = len(values)
    if n <= ddof:
        return 0.0
    m = _mean(values)
    return sum((x - m) ** 2 for x in values) / (n - ddof)


def _std(values: list, ddof: int = 1) -> float:
    return math.sqrt(_variance(values, ddof))


def _percentile(sorted_values: list, p: float) -> float:
    """Interpolated percentile (0–100) from a pre-sorted list."""
    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    idx = p / 100 * (n - 1)
    lo, hi = int(idx), min(int(idx) + 1, n - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (idx - lo)


# ── Distributional stats ──────────────────────────────────────────────────────

def skewness(values: list) -> Optional[float]:
    """
    Fisher-Pearson standardized third-moment skewness (adjusted for sample bias).

    Returns None if n < 3 or std == 0.
    """
    n = len(values)
    if n < 3:
        return None
    m = _mean(values)
    s = _std(values, ddof=1)
    if s == 0:
        return None
    g1 = sum(((x - m) / s) ** 3 for x in values) / n
    # Adjusted for sample: G1 = g1 * sqrt(n*(n-1)) / (n-2)
    return g1 * math.sqrt(n * (n - 1)) / (n - 2)


def excess_kurtosis(values: list) -> Optional[float]:
    """
    Excess kurtosis (Fisher's definition, adjusted for bias).

    Returns None if n < 4 or std == 0.
    """
    n = len(values)
    if n < 4:
        return None
    m = _mean(values)
    s = _std(values, ddof=1)
    if s == 0:
        return None
    g2 = sum(((x - m) / s) ** 4 for x in values) / n - 3
    # Bias-adjusted (G2):
    return (n - 1) / ((n - 2) * (n - 3)) * ((n + 1) * g2 + 6)


def descriptive_stats(values: list) -> dict:
    """
    Return a dict of descriptive statistics for a list of floats.

    Keys: n, mean, std, min, q1, median, q3, max, iqr, skewness, kurtosis.
    """
    n = len(values)
    if n == 0:
        return {"n": 0}
    sv = sorted(values)
    m = _mean(values)
    sd = _std(values, ddof=1) if n > 1 else 0.0
    q1 = _percentile(sv, 25)
    q3 = _percentile(sv, 75)
    return {
        "n": n,
        "mean": round(m, 4),
        "std": round(sd, 4),
        "min": sv[0],
        "q1": round(q1, 4),
        "median": round(_percentile(sv, 50), 4),
        "q3": round(q3, 4),
        "max": sv[-1],
        "iqr": round(q3 - q1, 4),
        "skewness": round(skewness(values), 4) if skewness(values) is not None else None,
        "kurtosis": round(excess_kurtosis(values), 4) if excess_kurtosis(values) is not None else None,
    }


# ── Normality test (D'Agostino–Pearson K²) ───────────────────────────────────

def _chi2_sf(x: float, df: float) -> float:
    """
    Survival function for chi-squared distribution: P(chi2 > x).

    Computed via the regularized upper incomplete gamma Q(df/2, x/2).
    """
    if x <= 0:
        return 1.0
    return _gamma_upper(df / 2, x / 2)


def _gamma_upper(a: float, x: float) -> float:
    """Regularized upper incomplete gamma Q(a, x) = 1 - P(a, x)."""
    if x < 0:
        return 1.0
    if x < a + 1:
        return 1.0 - _gamma_series(a, x)
    return _gamma_cf(a, x)


def _gamma_series(a: float, x: float, max_iter: int = 300, tol: float = 1e-12) -> float:
    """Regularized lower incomplete gamma P(a, x) via series expansion."""
    if x == 0:
        return 0.0
    ap = a
    delta = 1.0 / a
    total = delta
    for _ in range(max_iter):
        ap += 1
        delta *= x / ap
        total += delta
        if abs(delta) < abs(total) * tol:
            break
    return total * math.exp(-x + a * math.log(x) - math.lgamma(a))


def _gamma_cf(a: float, x: float, max_iter: int = 300, tol: float = 1e-12) -> float:
    """Regularized upper incomplete gamma Q(a, x) via Lentz continued fraction."""
    fpmin = 1e-300
    b = x + 1 - a
    c = 1 / fpmin
    d = 1 / b if abs(b) > fpmin else 1 / fpmin
    h = d
    for i in range(1, max_iter + 1):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < fpmin:
            d = fpmin
        c = b + an / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < tol:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def _normal_sf(z: float) -> float:
    """Upper tail probability for the standard normal: P(Z > z)."""
    return math.erfc(z / math.sqrt(2)) / 2


def normality_test(values: list) -> Optional[dict]:
    """
    D'Agostino–Pearson K² omnibus normality test.

    Combines skewness and kurtosis into a single chi-squared(2) test statistic.
    Returns a dict with keys: statistic, p_value, is_normal (p > 0.05).
    Returns None if n < 8.

    Reference: D'Agostino & Pearson (1973).
    """
    n = len(values)
    if n < 8:
        return None

    g1 = skewness(values)
    g2 = excess_kurtosis(values)
    if g1 is None or g2 is None:
        return None

    # Skewness test (D'Agostino 1970)
    y = g1 * math.sqrt((n + 1) * (n + 3) / (6 * (n - 2)))
    b2_g1 = 3 * (n ** 2 + 27 * n - 70) * (n + 1) * (n + 3) / (
        (n - 2) * (n + 5) * (n + 7) * (n + 9)
    )
    w2 = -1 + math.sqrt(2 * (b2_g1 - 1))
    if w2 <= 0:
        return None
    delta = 1 / math.sqrt(math.log(math.sqrt(w2)))
    alpha = math.sqrt(2 / (w2 - 1))
    arg = y / alpha
    z1 = delta * math.log(arg + math.sqrt(arg ** 2 + 1))

    # Kurtosis test (Anscombe & Glynn 1983)
    mean_g2 = -6 / (n + 1)
    var_g2 = 24 * n * (n - 2) * (n - 3) / ((n + 1) ** 2 * (n + 3) * (n + 5))
    if var_g2 <= 0:
        return None
    x_val = (g2 - mean_g2) / math.sqrt(var_g2)
    b = (
        6
        * (n ** 2 - 5 * n + 2)
        / ((n + 7) * (n + 9))
        * math.sqrt(6 * (n + 3) * (n + 5) / (n * (n - 2) * (n - 3)))
    )
    a_val = 6 + 8 / b * (2 / b + math.sqrt(1 + 4 / b ** 2))
    term = 1 - 2 / (9 * a_val)
    cube_root_arg = 1 - 2 / a_val
    if cube_root_arg <= 0:
        z2 = 0.0
    else:
        z2 = (term - (1 - 2 / a_val) ** (1 / 3) * (1 + x_val * math.sqrt(2 / (a_val - 4)))) / math.sqrt(
            2 / (9 * a_val)
        )

    k2 = z1 ** 2 + z2 ** 2
    p_value = _chi2_sf(k2, df=2)

    return {
        "statistic": round(k2, 4),
        "p_value": round(p_value, 4),
        "is_normal": p_value > 0.05,
        "skewness_z": round(z1, 4),
        "kurtosis_z": round(z2, 4),
    }


# ── Correlation ───────────────────────────────────────────────────────────────

def pearson_r(x: list, y: list) -> Optional[float]:
    """
    Pearson correlation coefficient between two equal-length lists.

    Returns None if either list has fewer than 2 elements or zero variance.
    """
    n = len(x)
    if n < 2 or len(y) != n:
        return None
    mx, my = _mean(x), _mean(y)
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    denom_x = math.sqrt(sum((v - mx) ** 2 for v in x))
    denom_y = math.sqrt(sum((v - my) ** 2 for v in y))
    if denom_x == 0 or denom_y == 0:
        return None
    return round(num / (denom_x * denom_y), 4)


def correlation_matrix(columns: dict) -> dict:
    """
    Compute a pairwise Pearson correlation matrix.

    columns: dict mapping column name → list of float values (must be same length).
    Returns a dict of dicts: {col_a: {col_b: r, ...}, ...}.
    """
    names = list(columns.keys())
    matrix: dict = {}
    for i, name_i in enumerate(names):
        matrix[name_i] = {}
        for j, name_j in enumerate(names):
            if i == j:
                matrix[name_i][name_j] = 1.0
            elif j < i:
                matrix[name_i][name_j] = matrix[name_j][name_i]
            else:
                # Pairwise complete observations
                pairs = [
                    (columns[name_i][k], columns[name_j][k])
                    for k in range(len(columns[name_i]))
                    if columns[name_i][k] is not None and columns[name_j][k] is not None
                ]
                if len(pairs) < 2:
                    matrix[name_i][name_j] = None
                else:
                    xs = [p[0] for p in pairs]
                    ys = [p[1] for p in pairs]
                    matrix[name_i][name_j] = pearson_r(xs, ys)
    return matrix


def item_total_correlations(rows: list, scale_columns: list) -> dict:
    """
    Compute corrected item-total correlations for a scale.

    For each item, computes Pearson r between the item and the sum of
    all OTHER items (corrected item-total, avoiding part-whole inflation).

    Returns: {column_name: correlation or None}.
    """
    result = {}
    for target_col in scale_columns:
        other_cols = [c for c in scale_columns if c != target_col]
        if not other_cols:
            result[target_col] = None
            continue

        pairs = []
        for row in rows:
            target_val = row.get(target_col)
            other_vals = [row.get(c) for c in other_cols]
            if target_val is None or any(v is None for v in other_vals):
                continue
            try:
                item_score = float(target_val)
                rest_score = sum(float(v) for v in other_vals)
                pairs.append((item_score, rest_score))
            except (ValueError, TypeError):
                continue

        if len(pairs) < 2:
            result[target_col] = None
        else:
            xs = [p[0] for p in pairs]
            ys = [p[1] for p in pairs]
            result[target_col] = pearson_r(xs, ys)

    return result


def extract_numeric_column(rows: list, col_name: str) -> list:
    """Extract numeric (float) values from a column, skipping None and non-numeric."""
    out = []
    for row in rows:
        v = row.get(col_name)
        if v is None:
            continue
        try:
            out.append(float(v))
        except (ValueError, TypeError):
            continue
    return out

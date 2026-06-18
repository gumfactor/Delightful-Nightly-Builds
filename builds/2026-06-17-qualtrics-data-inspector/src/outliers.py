"""Outlier detection: Z-score and IQR methods."""

from src.statistics import (
    _mean, _std, _percentile, extract_numeric_column
)


def zscore_outliers(
    rows: list,
    columns: list,
    threshold: float = 3.0,
    id_fn=None,
) -> dict:
    """
    Detect per-column Z-score outliers.

    Returns: {col_name: {respondent_id: z_score}} for values where |z| > threshold.

    id_fn: callable(row) → str. Defaults to ResponseId / id(row).
    """
    if id_fn is None:
        id_fn = _default_id

    result: dict = {}
    for col in columns:
        values_with_ids = []
        for row in rows:
            v = row.get(col)
            if v is None:
                continue
            try:
                values_with_ids.append((_default_id(row), float(v)))
            except (ValueError, TypeError):
                continue

        if len(values_with_ids) < 3:
            continue

        nums = [v for _, v in values_with_ids]
        m = _mean(nums)
        s = _std(nums, ddof=1)
        if s == 0:
            continue

        outliers = {}
        for rid, v in values_with_ids:
            z = (v - m) / s
            if abs(z) > threshold:
                outliers[rid] = round(z, 3)

        if outliers:
            result[col] = outliers

    return result


def iqr_outliers(rows: list, columns: list) -> dict:
    """
    Detect per-column IQR outliers (Tukey fences: Q1 - 1.5*IQR, Q3 + 1.5*IQR).

    Returns: {col_name: {respondent_id: value}} for values outside the fences.
    """
    result: dict = {}
    for col in columns:
        values_with_ids = []
        for row in rows:
            v = row.get(col)
            if v is None:
                continue
            try:
                values_with_ids.append((_default_id(row), float(v)))
            except (ValueError, TypeError):
                continue

        if len(values_with_ids) < 4:
            continue

        nums_sorted = sorted(v for _, v in values_with_ids)
        q1 = _percentile(nums_sorted, 25)
        q3 = _percentile(nums_sorted, 75)
        iqr = q3 - q1
        if iqr == 0:
            continue

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers = {}
        for rid, v in values_with_ids:
            if v < lower or v > upper:
                outliers[rid] = v

        if outliers:
            result[col] = outliers

    return result


def respondent_outlier_counts(
    zscore_result: dict,
    iqr_result: dict,
) -> dict:
    """
    Count how many columns each respondent appears as an outlier in.

    Returns: {respondent_id: count} for respondents flagged on ≥ 1 column.
    Counts are the union of Z-score and IQR flags (a column counted once per respondent
    even if flagged by both methods).
    """
    from collections import defaultdict
    counts: dict = defaultdict(set)

    for col, outliers in zscore_result.items():
        for rid in outliers:
            counts[rid].add(("z", col))

    for col, outliers in iqr_result.items():
        for rid in outliers:
            counts[rid].add(("iqr", col))

    return {rid: len({col for _, col in flags}) for rid, flags in counts.items()}


def _default_id(row: dict) -> str:
    """Return a stable string identifier for a row."""
    for key in ("ResponseId", "responseid", "response_id", "ID", "id"):
        if row.get(key) is not None:
            return str(row[key])
    return str(id(row))

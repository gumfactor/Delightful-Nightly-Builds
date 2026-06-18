"""Compute data quality metrics from a parsed Qualtrics survey."""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QualityThresholds:
    """Configurable thresholds used throughout quality checks.

    All defaults represent commonly accepted values in social science research.
    """
    fast_response_seconds: int = 60
    straight_liner_min_items: int = 3
    missing_column_warn: float = 0.05      # 5% — flag in report
    missing_column_flag: float = 0.20      # 20% — serious concern
    missing_respondent_flag: float = 0.20  # 20% of items blank per respondent
    outlier_z_threshold: float = 3.0
    low_item_total_r: float = 0.20         # items below this are problematic
    condition_max_categories: int = 10


@dataclass
class QualityReport:
    """All quality metrics for one survey dataset."""
    # ── Core ──
    respondent_count: int
    completed_count: int
    completion_rate: float
    timing_stats: dict
    per_column_missing: dict
    straight_liner_ids: list
    duplicate_ips: list
    cronbach_results: dict
    fast_response_ids: list
    timing_threshold_seconds: int
    detected_scales: dict

    # ── Extended ──
    thresholds: QualityThresholds = field(default_factory=QualityThresholds)
    high_missing_respondents: list = field(default_factory=list)
    column_stats: dict = field(default_factory=dict)
    outlier_zscore: dict = field(default_factory=dict)
    outlier_iqr: dict = field(default_factory=dict)
    respondent_outlier_counts: dict = field(default_factory=dict)
    item_total_correlations: dict = field(default_factory=dict)
    correlation_matrices: dict = field(default_factory=dict)
    floor_ceiling_effects: dict = field(default_factory=dict)
    condition_column: Optional[str] = field(default=None)
    condition_tests: dict = field(default_factory=dict)
    attention_specs: list = field(default_factory=list)
    attention_results: dict = field(default_factory=dict)
    careless_index: dict = field(default_factory=dict)


# ── Helpers shared by other modules ──────────────────────────────────────────

def compute_missing_rate(values: list) -> float:
    """Return the fraction of None values in a list (0.0 to 1.0)."""
    if not values:
        return 0.0
    return sum(1 for v in values if v is None) / len(values)


def compute_completion_rate(rows: list) -> float:
    """Return the fraction of rows where Progress == '100'."""
    if not rows:
        return 0.0
    completed = sum(1 for r in rows if str(r.get("Progress") or "").strip() == "100")
    return completed / len(rows)


def _parse_duration(row: dict) -> Optional[float]:
    """Extract numeric duration from 'Duration (in seconds)' or 'Duration' column."""
    val = row.get("Duration (in seconds)") or row.get("Duration")
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def compute_timing_stats(rows: list, threshold_seconds: int = 60) -> dict:
    """
    Return timing statistics from the Duration column.

    Keys: count, mean, median, min, max, fast_count.
    Returns zeroed dict if no timing data is available.
    """
    durations = [d for d in (_parse_duration(r) for r in rows) if d is not None]
    if not durations:
        return {"count": 0, "mean": None, "median": None, "min": None,
                "max": None, "fast_count": 0}

    durations_sorted = sorted(durations)
    n = len(durations_sorted)
    mean = sum(durations_sorted) / n
    mid = n // 2
    median = durations_sorted[mid] if n % 2 == 1 else (
        (durations_sorted[mid - 1] + durations_sorted[mid]) / 2
    )
    fast_count = sum(1 for d in durations_sorted if d < threshold_seconds)

    return {
        "count": n,
        "mean": round(mean, 1),
        "median": round(median, 1),
        "min": round(durations_sorted[0], 1),
        "max": round(durations_sorted[-1], 1),
        "fast_count": fast_count,
    }


def _get_response_id(row: dict) -> str:
    """Return a stable string identifier for a respondent row."""
    for key in ("ResponseId", "responseid", "response_id", "ID", "id"):
        if row.get(key) is not None:
            return str(row[key])
    return str(id(row))


def detect_straight_liners(rows: list, scale_columns: list, min_items: int = 3) -> list:
    """
    Return response IDs of straight-liners: respondents who gave the exact same
    non-None value to every item in scale_columns (requires >= min_items responses).
    """
    ids = []
    for row in rows:
        vals = [row.get(c) for c in scale_columns if row.get(c) is not None]
        if len(vals) >= min_items and len(set(vals)) == 1:
            ids.append(_get_response_id(row))
    return ids


def detect_duplicate_ips(rows: list) -> list:
    """Return list of IP addresses that appear in more than one response row."""
    ip_counts: dict = {}
    for row in rows:
        ip = row.get("IPAddress") or row.get("ipAddress") or row.get("ipaddress")
        if ip is not None:
            ip_counts[ip] = ip_counts.get(ip, 0) + 1
    return [ip for ip, count in ip_counts.items() if count > 1]


def _sample_variance(values: list) -> float:
    """Compute unbiased sample variance (denominator n-1)."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return sum((x - mean) ** 2 for x in values) / (n - 1)


def cronbach_alpha(item_scores: list) -> Optional[float]:
    """
    Compute Cronbach's alpha from a list of per-item score lists.

    item_scores[i] is a list of respondent scores for item i.
    Returns None if computation is not possible (< 2 items, < 2 respondents,
    or zero total variance).
    """
    k = len(item_scores)
    if k < 2:
        return None
    n = len(item_scores[0]) if item_scores else 0
    if n < 2:
        return None

    item_variances = [_sample_variance(scores) for scores in item_scores]
    total_scores = [
        sum(item_scores[i][j] for i in range(k))
        for j in range(n)
    ]
    total_variance = _sample_variance(total_scores)
    if total_variance == 0:
        return None

    alpha = (k / (k - 1)) * (1.0 - sum(item_variances) / total_variance)
    return round(alpha, 4)


def auto_detect_scales(column_names: list) -> dict:
    """
    Group columns by PREFIX_N pattern into scales.

    Example: [Q2_1, Q2_2, Q2_3] → {"Q2": ["Q2_1","Q2_2","Q2_3"]}.
    Only groups with >= 2 columns are returned.
    """
    groups: dict = {}
    for col in column_names:
        match = re.match(r'^(.+)_(\d+)$', col)
        if match:
            prefix = match.group(1)
            groups.setdefault(prefix, []).append(col)
    return {k: sorted(v) for k, v in groups.items() if len(v) >= 2}


def high_missing_respondents(
    rows: list,
    question_columns: list,
    threshold: float = 0.20,
) -> list:
    """Return IDs of respondents missing more than threshold fraction of question items."""
    flagged = []
    for row in rows:
        n_total = len(question_columns)
        if n_total == 0:
            continue
        n_missing = sum(1 for c in question_columns if row.get(c) is None)
        if n_missing / n_total > threshold:
            flagged.append(_get_response_id(row))
    return flagged


def floor_ceiling_effects(rows: list, columns: list, threshold: float = 0.80) -> dict:
    """
    Detect floor and ceiling effects per column.

    A floor effect exists when > threshold of valid responses are at the minimum value.
    A ceiling effect exists when > threshold are at the maximum value.

    Returns: {col: {floor_rate, ceiling_rate, floor_effect, ceiling_effect}}.
    """
    result: dict = {}
    for col in columns:
        vals = []
        for row in rows:
            v = row.get(col)
            if v is None:
                continue
            try:
                vals.append(float(v))
            except (ValueError, TypeError):
                continue
        if len(vals) < 3:
            continue
        min_v, max_v = min(vals), max(vals)
        if min_v == max_v:
            continue
        n = len(vals)
        floor_rate = sum(1 for v in vals if v == min_v) / n
        ceiling_rate = sum(1 for v in vals if v == max_v) / n
        result[col] = {
            "floor_rate": round(floor_rate, 4),
            "ceiling_rate": round(ceiling_rate, 4),
            "floor_effect": floor_rate > threshold,
            "ceiling_effect": ceiling_rate > threshold,
        }
    return result


# ── Main entry point ──────────────────────────────────────────────────────────

def compute_quality(
    survey,
    scale_groups: Optional[dict] = None,
    timing_threshold: int = 60,
    thresholds: Optional[QualityThresholds] = None,
    detect_conditions: bool = True,
    expected_attention_answers: Optional[dict] = None,
) -> QualityReport:
    """
    Compute the full quality report for a ParsedSurvey.

    scale_groups: optional dict mapping scale name to list of column names.
    If None, scales are auto-detected from column name patterns.
    timing_threshold: responses shorter than this (in seconds) are flagged.
    thresholds: configurable threshold values; uses QualityThresholds defaults if None.
    detect_conditions: if True, auto-detect condition columns and run between-group tests.
    """
    from src.statistics import (
        descriptive_stats, normality_test, item_total_correlations,
        correlation_matrix, extract_numeric_column,
    )
    from src.outliers import (
        zscore_outliers, iqr_outliers,
        respondent_outlier_counts as _resp_outlier_counts,
    )
    from src.conditions import detect_condition_columns, run_condition_tests
    from src.attention import detect_attention_check_columns, score_attention_checks
    from src.careless import compute_careless_index

    if thresholds is None:
        thresholds = QualityThresholds(fast_response_seconds=timing_threshold)

    rows = survey.rows

    # ── Completion & timing ──
    completed_count = sum(
        1 for r in rows if str(r.get("Progress") or "").strip() == "100"
    )
    completion_rate = completed_count / len(rows) if rows else 0.0
    timing_stats = compute_timing_stats(rows, timing_threshold)
    fast_response_ids = [
        _get_response_id(r) for r in rows
        if _parse_duration(r) is not None and _parse_duration(r) < timing_threshold
    ]

    # ── Missing data ──
    per_column_missing = {
        col.name: compute_missing_rate([r.get(col.name) for r in rows])
        for col in survey.columns
    }

    # ── Scale detection ──
    question_cols = survey.question_column_names
    detected_scales = scale_groups if scale_groups is not None else auto_detect_scales(question_cols)

    # ── Straight-lining ──
    all_scale_cols = list({c for cols in detected_scales.values() for c in cols})
    if not all_scale_cols:
        all_scale_cols = question_cols
    straight_liner_ids = detect_straight_liners(
        rows, all_scale_cols, thresholds.straight_liner_min_items
    )

    # ── Duplicate IPs ──
    duplicate_ips = detect_duplicate_ips(rows)

    # ── Cronbach's alpha ──
    cronbach_results: dict = {}
    for scale_name, cols in detected_scales.items():
        complete_rows = [r for r in rows if all(r.get(c) is not None for c in cols)]
        if len(complete_rows) < 2:
            cronbach_results[scale_name] = None
            continue
        try:
            item_scores = [[float(r[c]) for r in complete_rows] for c in cols]
            cronbach_results[scale_name] = cronbach_alpha(item_scores)
        except (ValueError, TypeError):
            cronbach_results[scale_name] = None

    # ── Per-respondent missing ──
    high_missing = high_missing_respondents(
        rows, question_cols, thresholds.missing_respondent_flag
    )

    # ── Distributional stats & normality (numeric question columns only) ──
    col_stats: dict = {}
    for col in question_cols:
        nums = extract_numeric_column(rows, col)
        if len(nums) < 3:
            continue
        stats = descriptive_stats(nums)
        norm = normality_test(nums)
        col_stats[col] = {**stats, "normality": norm}

    # ── Outlier detection ──
    numeric_q_cols = [c for c in question_cols if col_stats.get(c, {}).get("n", 0) >= 3]
    z_outliers = zscore_outliers(rows, numeric_q_cols, thresholds.outlier_z_threshold)
    iq_outliers = iqr_outliers(rows, numeric_q_cols)
    resp_outlier_counts = _resp_outlier_counts(z_outliers, iq_outliers)

    # ── Item-total correlations ──
    itc_results: dict = {}
    for scale_name, cols in detected_scales.items():
        itc_results[scale_name] = item_total_correlations(rows, cols)

    # ── Correlation matrices (None-aware, pairwise complete) ──
    corr_matrices: dict = {}
    for scale_name, cols in detected_scales.items():
        col_data: dict = {}
        for c in cols:
            aligned = []
            for row in rows:
                v = row.get(c)
                try:
                    aligned.append(float(v) if v is not None else None)
                except (ValueError, TypeError):
                    aligned.append(None)
            col_data[c] = aligned
        valid_cols = {c: v for c, v in col_data.items() if any(x is not None for x in v)}
        if len(valid_cols) >= 2:
            corr_matrices[scale_name] = correlation_matrix(valid_cols)

    # ── Floor/ceiling effects ──
    fc_effects = floor_ceiling_effects(rows, numeric_q_cols)

    # ── Condition detection & between-group tests ──
    cond_col = None
    cond_tests: dict = {}
    if detect_conditions and detected_scales:
        candidates = detect_condition_columns(
            survey, thresholds.condition_max_categories
        )
        if candidates:
            cond_col = candidates[0]
            cond_tests = run_condition_tests(rows, cond_col, detected_scales)

    # ── Attention checks ──
    attn_specs = detect_attention_check_columns(survey, expected_attention_answers)
    attn_results = score_attention_checks(survey, attn_specs)

    # ── Careless responding index ──
    # Build a temporary report stub to pass to compute_careless_index
    _stub = QualityReport(
        respondent_count=len(rows),
        completed_count=completed_count,
        completion_rate=completion_rate,
        timing_stats=timing_stats,
        per_column_missing=per_column_missing,
        straight_liner_ids=straight_liner_ids,
        duplicate_ips=duplicate_ips,
        cronbach_results=cronbach_results,
        fast_response_ids=fast_response_ids,
        timing_threshold_seconds=timing_threshold,
        detected_scales=detected_scales,
        thresholds=thresholds,
        high_missing_respondents=high_missing,
        column_stats=col_stats,
        outlier_zscore=z_outliers,
        outlier_iqr=iq_outliers,
        respondent_outlier_counts=resp_outlier_counts,
        item_total_correlations=itc_results,
        correlation_matrices=corr_matrices,
        floor_ceiling_effects=fc_effects,
        condition_column=cond_col,
        condition_tests=cond_tests,
    )
    careless = compute_careless_index(_stub, attn_results if attn_results else None)

    return QualityReport(
        respondent_count=len(rows),
        completed_count=completed_count,
        completion_rate=completion_rate,
        timing_stats=timing_stats,
        per_column_missing=per_column_missing,
        straight_liner_ids=straight_liner_ids,
        duplicate_ips=duplicate_ips,
        cronbach_results=cronbach_results,
        fast_response_ids=fast_response_ids,
        timing_threshold_seconds=timing_threshold,
        detected_scales=detected_scales,
        thresholds=thresholds,
        high_missing_respondents=high_missing,
        column_stats=col_stats,
        outlier_zscore=z_outliers,
        outlier_iqr=iq_outliers,
        respondent_outlier_counts=resp_outlier_counts,
        item_total_correlations=itc_results,
        correlation_matrices=corr_matrices,
        floor_ceiling_effects=fc_effects,
        condition_column=cond_col,
        condition_tests=cond_tests,
        attention_specs=attn_specs,
        attention_results=attn_results,
        careless_index=careless,
    )

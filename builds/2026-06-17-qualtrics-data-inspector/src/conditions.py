"""
Auto-detect experimental conditions/groups and run between-group statistical tests.

All tests are non-parametric (no normality assumption).
P-values use normal or chi-squared approximations valid for n ≥ 10 per group.
"""

import math
from typing import Optional

from src.statistics import _mean, _std, _chi2_sf, _normal_sf


# ── Condition column detection ────────────────────────────────────────────────

# Column name fragments that suggest a condition/group variable
_CONDITION_HINTS = frozenset({
    "condition", "group", "arm", "treatment", "version", "branch",
    "cell", "cond", "grp", "fl_", "wave", "cohort",
})


def detect_condition_columns(
    survey,
    max_categories: int = 10,
    min_categories: int = 2,
) -> list:
    """
    Identify columns that look like experimental condition or group variables.

    Heuristics (in priority order):
    1. Column name contains a known condition-hint keyword.
    2. Column has 2–max_categories distinct non-null string values.
    3. At least 5% of respondents have each category.

    Returns a list of column names ranked by confidence.
    """
    from src.parser import METADATA_COLUMNS

    candidates = []
    rows = survey.rows
    if not rows:
        return []

    for col in survey.question_column_names:
        values = [row.get(col) for row in rows if row.get(col) is not None]
        if not values:
            continue

        unique_vals = set(values)
        n_unique = len(unique_vals)

        if not (min_categories <= n_unique <= max_categories):
            continue

        # Check minimum representation per category
        n_total = len(values)
        counts = {v: values.count(v) for v in unique_vals}
        min_proportion = min(counts.values()) / n_total
        if min_proportion < 0.05:
            continue

        # Score by name hint
        name_lower = col.lower()
        name_hit = any(hint in name_lower for hint in _CONDITION_HINTS)

        # Exclude columns where values look like numeric responses (all parseable as int)
        all_numeric = all(_is_int_like(v) for v in unique_vals)

        if name_hit or (not all_numeric and n_unique <= 5):
            candidates.append((col, name_hit, n_unique))

    # Sort: name hits first, then fewest categories (clearest conditions)
    candidates.sort(key=lambda x: (not x[1], x[2]))
    return [col for col, _, _ in candidates]


def _is_int_like(v: str) -> bool:
    try:
        int(v)
        return True
    except (ValueError, TypeError):
        return False


# ── Group summary statistics ──────────────────────────────────────────────────

def group_descriptive_stats(rows: list, condition_col: str, measure_col: str) -> dict:
    """
    Return per-group descriptive statistics for a measure column.

    Returns: {group_label: {'n': int, 'mean': float, 'std': float, 'median': float}}.
    """
    from src.statistics import _percentile

    groups: dict = {}
    for row in rows:
        group = row.get(condition_col)
        val = row.get(measure_col)
        if group is None or val is None:
            continue
        try:
            groups.setdefault(group, []).append(float(val))
        except (ValueError, TypeError):
            continue

    result = {}
    for group, vals in sorted(groups.items()):
        sv = sorted(vals)
        n = len(vals)
        result[group] = {
            "n": n,
            "mean": round(_mean(vals), 3) if n > 0 else None,
            "std": round(_std(vals, ddof=1), 3) if n > 1 else None,
            "median": round(_percentile(sv, 50), 3) if n > 0 else None,
        }
    return result


def compute_scale_scores(rows: list, scale_groups: dict) -> dict:
    """
    Compute per-respondent mean scale score for each scale.

    Returns: {scale_name: {respondent_id: mean_score}}.
    """
    from src.quality import _get_response_id

    result: dict = {}
    for scale_name, cols in scale_groups.items():
        scores = {}
        for row in rows:
            vals = []
            for c in cols:
                v = row.get(c)
                if v is None:
                    continue
                try:
                    vals.append(float(v))
                except (ValueError, TypeError):
                    continue
            if vals:
                scores[_get_response_id(row)] = sum(vals) / len(vals)
        result[scale_name] = scores
    return result


# ── Mann-Whitney U (2 groups) ─────────────────────────────────────────────────

def mann_whitney_u(group1: list, group2: list) -> Optional[dict]:
    """
    Two-sided Mann-Whitney U test (Wilcoxon rank-sum).

    Uses the normal approximation valid when min(n1, n2) ≥ 8.
    Effect size: r = z / sqrt(N).

    Returns dict with: U, z, p_value, effect_size_r, n1, n2.
    Returns None if either group has fewer than 2 observations.
    """
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return None

    # Rank all observations together, handling ties with average ranks
    combined = [(v, 0) for v in group1] + [(v, 1) for v in group2]
    combined.sort(key=lambda x: x[0])

    n = n1 + n2
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        # Find all tied observations
        while j < n - 1 and combined[j][0] == combined[j + 1][0]:
            j += 1
        avg_rank = (i + j) / 2 + 1  # 1-indexed average rank
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1

    r1 = sum(ranks[k] for k in range(n) if combined[k][1] == 0)
    u1 = r1 - n1 * (n1 + 1) / 2
    u2 = n1 * n2 - u1
    u = min(u1, u2)

    # Normal approximation
    mean_u = n1 * n2 / 2
    # Variance with tie correction
    tie_correction = 0.0
    i = 0
    while i < n:
        j = i
        while j < n - 1 and combined[j][0] == combined[j + 1][0]:
            j += 1
        tie_len = j - i + 1
        if tie_len > 1:
            tie_correction += tie_len ** 3 - tie_len
        i = j + 1
    var_u = (n1 * n2 / 12) * (n + 1 - tie_correction / (n * (n - 1)))
    if var_u <= 0:
        return {"U": u, "z": 0.0, "p_value": 1.0, "effect_size_r": 0.0, "n1": n1, "n2": n2}

    z = (u - mean_u) / math.sqrt(var_u)
    p_value = 2 * _normal_sf(abs(z))
    r = z / math.sqrt(n)

    return {
        "U": round(u, 1),
        "z": round(z, 4),
        "p_value": round(p_value, 4),
        "effect_size_r": round(r, 4),
        "n1": n1,
        "n2": n2,
    }


# ── Kruskal-Wallis H (k ≥ 2 groups) ─────────────────────────────────────────

def kruskal_wallis(groups: list) -> Optional[dict]:
    """
    Kruskal-Wallis H test for differences among k ≥ 2 independent groups.

    Uses chi-squared approximation with df = k - 1. Valid when each group n ≥ 5.

    Returns dict with: H, df, p_value. Returns None if fewer than 2 groups or
    any group has fewer than 2 observations.
    """
    k = len(groups)
    if k < 2:
        return None
    if any(len(g) < 2 for g in groups):
        return None

    combined = []
    for group_idx, group in enumerate(groups):
        for v in group:
            combined.append((v, group_idx))
    combined.sort(key=lambda x: x[0])

    n = len(combined)
    if n < 3:
        return None

    # Assign ranks with tie averaging
    ranks = [0.0] * n
    i = 0
    tie_sum = 0.0
    while i < n:
        j = i
        while j < n - 1 and combined[j][0] == combined[j + 1][0]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for idx in range(i, j + 1):
            ranks[idx] = avg_rank
        tie_len = j - i + 1
        if tie_len > 1:
            tie_sum += tie_len ** 3 - tie_len
        i = j + 1

    # Group rank sums
    rank_sums = [0.0] * k
    group_counts = [0] * k
    for obs_idx, (_, group_idx) in enumerate(combined):
        rank_sums[group_idx] += ranks[obs_idx]
        group_counts[group_idx] += 1

    h = (12 / (n * (n + 1))) * sum(
        rs ** 2 / nc for rs, nc in zip(rank_sums, group_counts)
    ) - 3 * (n + 1)

    # Tie correction
    if n > 1:
        tie_factor = 1 - tie_sum / (n ** 3 - n)
        if tie_factor > 0:
            h /= tie_factor

    df = k - 1
    p_value = _chi2_sf(h, df)

    return {
        "H": round(h, 4),
        "df": df,
        "p_value": round(p_value, 4),
    }


# ── Run all condition tests ───────────────────────────────────────────────────

def run_condition_tests(
    rows: list,
    condition_col: str,
    scale_groups: dict,
) -> dict:
    """
    For each scale, test whether group means differ significantly by condition.

    Uses Mann-Whitney U for 2 groups, Kruskal-Wallis for 3+ groups.

    Returns:
    {
        scale_name: {
            "group_stats": {group: {n, mean, std, median}},
            "test": {type, ...test result fields...},
        }
    }
    """
    scale_scores = compute_scale_scores(rows, scale_groups)
    results: dict = {}

    # Build per-group rows for condition column
    group_labels: list = sorted({
        row.get(condition_col)
        for row in rows
        if row.get(condition_col) is not None
    })

    if len(group_labels) < 2:
        return {}

    for scale_name, score_map in scale_scores.items():
        group_stats = {}
        group_score_lists = []

        # Map respondent IDs to condition
        from src.quality import _get_response_id
        id_to_condition = {
            _get_response_id(row): row.get(condition_col)
            for row in rows
            if row.get(condition_col) is not None
        }

        for label in group_labels:
            vals = [
                score
                for rid, score in score_map.items()
                if id_to_condition.get(rid) == label
            ]
            if vals:
                group_score_lists.append(vals)
                sv = sorted(vals)
                from src.statistics import _percentile
                group_stats[label] = {
                    "n": len(vals),
                    "mean": round(_mean(vals), 3),
                    "std": round(_std(vals, ddof=1), 3) if len(vals) > 1 else None,
                    "median": round(_percentile(sv, 50), 3),
                }

        if len(group_score_lists) < 2:
            continue

        if len(group_labels) == 2:
            test_result = mann_whitney_u(group_score_lists[0], group_score_lists[1])
            test_type = "Mann-Whitney U"
        else:
            test_result = kruskal_wallis(group_score_lists)
            test_type = "Kruskal-Wallis H"

        if test_result is not None:
            test_result["type"] = test_type

        results[scale_name] = {
            "condition_col": condition_col,
            "group_stats": group_stats,
            "test": test_result,
        }

    return results

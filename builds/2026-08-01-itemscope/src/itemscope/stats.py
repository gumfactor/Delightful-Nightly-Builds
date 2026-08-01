"""Classical test theory statistics for ItemScope.

Every threshold used for flagging is a named constant here, not a magic
number scattered through the code.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from itemscope.parser import ScoredMatrix

TOO_EASY_THRESHOLD = 0.95
TOO_HARD_THRESHOLD = 0.20
POOR_DISCRIMINATION_THRESHOLD = 0.15
NEGATIVE_DISCRIMINATION_THRESHOLD = 0.0
UPPER_LOWER_FRACTION = 0.27
SMALL_N_GROUP_SIZE = 2  # below this many students per group, label small-N


@dataclass
class ItemStats:
    item_id: str
    p_value: float
    discrimination: float | None  # None if undefined (zero variance)
    discrimination_note: str | None
    flags: list[str] = field(default_factory=list)
    distractor_analysis: dict | None = None  # only present for raw-option input


@dataclass
class TestStats:
    n_students: int
    n_items: int
    mean_score: float
    sd_score: float
    sem: float | None
    kr20: float | None
    kr20_note: str | None
    items: list[ItemStats]


def p_value(item_column: list[int]) -> float:
    if not item_column:
        return 0.0
    return sum(item_column) / len(item_column)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _population_variance(values: list[float]) -> float:
    if not values:
        return 0.0
    m = _mean(values)
    return sum((v - m) ** 2 for v in values) / len(values)


def _population_stdev(values: list[float]) -> float:
    return math.sqrt(_population_variance(values))


def pearson_correlation(x: list[float], y: list[float]) -> float | None:
    """Pearson correlation coefficient. Returns None if either variable has
    zero variance (undefined correlation), rather than raising or returning
    NaN."""
    if len(x) != len(y) or len(x) < 2:
        return None
    sx = _population_stdev(x)
    sy = _population_stdev(y)
    if sx == 0.0 or sy == 0.0:
        return None
    mx, my = _mean(x), _mean(y)
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / len(x)
    return cov / (sx * sy)


def point_biserial_discrimination(
    item_column: list[int], total_scores_excluding_item: list[float]
) -> float | None:
    """Point-biserial correlation between a binary item and the
    corrected total score (total score with that item excluded)."""
    return pearson_correlation(
        [float(v) for v in item_column], total_scores_excluding_item
    )


def kr20(scores: list[list[int]]) -> tuple[float | None, str | None]:
    """Kuder-Richardson Formula 20 reliability for binary items.

    Returns (value, note). value is None when reliability isn't meaningful
    (fewer than 2 items).
    """
    n_items = len(scores[0]) if scores else 0
    if n_items < 2:
        return None, "not meaningful for a single item"

    item_columns = [[row[j] for row in scores] for j in range(n_items)]
    sum_pq = 0.0
    for col in item_columns:
        p = p_value(col)
        q = 1 - p
        sum_pq += p * q

    total_scores = [float(sum(row)) for row in scores]
    variance_total = _population_variance(total_scores)
    if variance_total == 0.0:
        return None, "not meaningful — every student scored identically"

    k = n_items
    value = (k / (k - 1)) * (1 - sum_pq / variance_total)
    return value, None


def _upper_lower_split(total_scores: list[float]) -> tuple[list[int], list[int], bool]:
    """Return (upper_indices, lower_indices, is_small_n) using the top/bottom
    27% by total score. Falls back to at least 1 student per group when the
    class is small, and flags the result as small-N in that case."""
    n = len(total_scores)
    group_size = max(1, round(n * UPPER_LOWER_FRACTION))
    order = sorted(range(n), key=lambda i: total_scores[i])
    lower_indices = order[:group_size]
    upper_indices = order[-group_size:]
    is_small_n = group_size < SMALL_N_GROUP_SIZE
    return upper_indices, lower_indices, is_small_n


NON_FUNCTIONING_LABEL = "non_functioning_distractor"
REVERSED_PULL_LABEL = "reversed_distractor_pull"


def distractor_analysis(
    raw_options: list[str], correct_answer: str, upper_indices: list[int], lower_indices: list[int]
) -> dict:
    """Analyze which options the upper- and lower-scoring groups picked.

    Returns a dict: {option: {"upper_rate": float, "lower_rate": float,
    "is_correct": bool}}, plus a "flags" list of distractor-level problems.
    """
    options = sorted(set(raw_options))
    upper_options = [raw_options[i] for i in upper_indices]
    lower_options = [raw_options[i] for i in lower_indices]

    result: dict = {"options": {}, "flags": []}
    for option in options:
        upper_rate = upper_options.count(option) / len(upper_options) if upper_options else 0.0
        lower_rate = lower_options.count(option) / len(lower_options) if lower_options else 0.0
        is_correct = option == correct_answer
        result["options"][option] = {
            "upper_rate": upper_rate,
            "lower_rate": lower_rate,
            "is_correct": is_correct,
        }
        if not is_correct:
            if upper_rate == 0.0 and lower_rate == 0.0:
                result["flags"].append(
                    {"option": option, "type": NON_FUNCTIONING_LABEL}
                )
            elif upper_rate > lower_rate:
                result["flags"].append(
                    {"option": option, "type": REVERSED_PULL_LABEL}
                )
    return result


def analyze(matrix: ScoredMatrix) -> TestStats:
    n_students = len(matrix.student_ids)
    n_items = len(matrix.item_ids)
    total_scores = [float(sum(row)) for row in matrix.scores]
    mean_score = _mean(total_scores)
    sd_score = _population_stdev(total_scores)

    reliability, reliability_note = kr20(matrix.scores)
    sem = sd_score * math.sqrt(1 - reliability) if reliability is not None and reliability <= 1 else None

    has_raw_options = any(
        matrix.raw_options[i][j] is not None for i in range(n_students) for j in range(n_items)
    ) if matrix.raw_options else False

    upper_indices, lower_indices, small_n = (
        _upper_lower_split(total_scores) if n_students > 0 else ([], [], True)
    )

    item_results: list[ItemStats] = []
    for j, item_id in enumerate(matrix.item_ids):
        column = [matrix.scores[i][j] for i in range(n_students)]
        corrected_total = [total_scores[i] - column[i] for i in range(n_students)]
        p = p_value(column)
        r = point_biserial_discrimination(column, corrected_total)

        flags: list[str] = []
        note = None
        if r is None:
            note = "undefined (zero variance)"
        else:
            if r < NEGATIVE_DISCRIMINATION_THRESHOLD:
                flags.append("negative_discrimination")
            elif r < POOR_DISCRIMINATION_THRESHOLD:
                flags.append("poor_discrimination")
        if p > TOO_EASY_THRESHOLD:
            flags.append("too_easy")
        if p < TOO_HARD_THRESHOLD:
            flags.append("too_hard")

        distractor_result = None
        if has_raw_options and matrix.answer_key is not None:
            raw_col = [matrix.raw_options[i][j] for i in range(n_students)]
            if all(v is not None for v in raw_col):
                distractor_result = distractor_analysis(
                    raw_col, matrix.answer_key[item_id], upper_indices, lower_indices
                )
                if small_n:
                    distractor_result["small_n"] = True
                for f in distractor_result["flags"]:
                    flags.append(f["type"])

        item_results.append(
            ItemStats(
                item_id=item_id,
                p_value=p,
                discrimination=r,
                discrimination_note=note,
                flags=flags,
                distractor_analysis=distractor_result,
            )
        )

    return TestStats(
        n_students=n_students,
        n_items=n_items,
        mean_score=mean_score,
        sd_score=sd_score,
        sem=sem,
        kr20=reliability,
        kr20_note=reliability_note,
        items=item_results,
    )

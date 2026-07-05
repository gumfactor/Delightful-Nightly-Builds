"""Per-subject/condition aggregation and configurable QC flag logic for TrialScope."""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Optional

from parsing import Trial


@dataclass
class QCConfig:
    rt_floor_ms: float = 150.0
    rt_ceiling_ms: float = 5000.0
    sd_outlier: float = 3.5
    chance_rate: float = 0.5
    chance_alpha: float = 0.05
    min_completion: float = 0.8
    expected_trials: Optional[int] = None
    exclude_threshold: int = 2
    ceiling_accuracy: float = 1.0
    ceiling_fast_multiplier: float = 1.5


@dataclass
class SubjectSummary:
    subject: str
    n_trials: int
    n_correct: int
    accuracy: float
    mean_rt: Optional[float]
    median_rt: Optional[float]
    sd_rt: Optional[float]
    n_fast_guess: int = 0
    n_outlier: int = 0
    flags: list[str] = field(default_factory=list)

    @property
    def excluded(self) -> bool:
        return len(self.flags) > 0


@dataclass
class ConditionSummary:
    condition: str
    n_trials: int
    n_subjects: int
    accuracy: float
    mean_rt: Optional[float]
    sd_rt: Optional[float]


@dataclass
class TrialFlagResult:
    trial_index: int
    flag: str  # "" | "fast_guess" | "outlier" | "both"


def _binomial_p_at_least(k: int, n: int, p: float) -> float:
    """P(X >= k) for X ~ Binomial(n, p), computed exactly with math.comb."""
    if n == 0:
        return 1.0
    return sum(math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(k, n + 1))


def flag_trials(trials: list[Trial], config: QCConfig) -> list[TrialFlagResult]:
    """Flag individual trials as fast-guess and/or outlier, per-subject.

    Outlier detection uses a modified z-score (median / median-absolute-deviation)
    over each subject's own correct-trial RTs, plus an absolute ceiling. MAD-based
    detection is used instead of mean/population-SD because a single extreme value
    inflates its own reference SD: for one outlier among n samples, the maximum
    achievable mean/SD z-score is bounded by sqrt(n-1) *no matter how extreme the
    outlier is*, which makes a fixed SD-multiplier threshold effectively unusable at
    typical per-condition trial counts. Median and MAD are robust to a single
    extreme value, so the modified z-score stays sensitive regardless of sample size.
    """
    by_subject: dict[str, list[int]] = {}
    for idx, t in enumerate(trials):
        by_subject.setdefault(t.subject, []).append(idx)

    results: list[TrialFlagResult] = [TrialFlagResult(i, "") for i in range(len(trials))]

    for subject, indices in by_subject.items():
        correct_rts = [
            trials[i].rt_ms
            for i in indices
            if trials[i].rt_ms is not None and trials[i].correct
        ]
        subj_median = statistics.median(correct_rts) if correct_rts else None
        subj_mad = (
            statistics.median([abs(x - subj_median) for x in correct_rts])
            if correct_rts
            else 0.0
        )

        for i in indices:
            rt = trials[i].rt_ms
            flags = []
            if rt is not None:
                if rt < config.rt_floor_ms:
                    flags.append("fast_guess")
                is_abs_outlier = rt > config.rt_ceiling_ms
                is_robust_outlier = False
                if subj_median is not None and subj_mad > 0:
                    modified_z = 0.6745 * (rt - subj_median) / subj_mad
                    is_robust_outlier = abs(modified_z) > config.sd_outlier
                if is_abs_outlier or is_robust_outlier:
                    flags.append("outlier")
            results[i].flag = "+".join(flags)

    return results


def summarize_subjects(
    trials: list[Trial], trial_flags: list[TrialFlagResult], config: QCConfig
) -> list[SubjectSummary]:
    by_subject: dict[str, list[int]] = {}
    for idx, t in enumerate(trials):
        by_subject.setdefault(t.subject, []).append(idx)

    summaries: list[SubjectSummary] = []
    for subject, indices in sorted(by_subject.items()):
        n_trials = len(indices)
        graded = [trials[i] for i in indices if trials[i].correct is not None]
        n_correct = sum(1 for t in graded if t.correct)
        accuracy = (n_correct / len(graded)) if graded else 0.0

        correct_rts = [
            trials[i].rt_ms for i in indices if trials[i].rt_ms is not None and trials[i].correct
        ]
        mean_rt = statistics.mean(correct_rts) if correct_rts else None
        median_rt = statistics.median(correct_rts) if correct_rts else None
        sd_rt = statistics.pstdev(correct_rts) if len(correct_rts) > 1 else (0.0 if correct_rts else None)

        n_fast_guess = sum(1 for i in indices if "fast_guess" in trial_flags[i].flag)
        n_outlier = sum(1 for i in indices if "outlier" in trial_flags[i].flag)

        flags: list[str] = []

        # Chance-level performance: P(X >= n_correct | n, chance_rate) high => can't
        # reject the "just guessing" null, i.e. performance is not distinguishable
        # from chance at the configured alpha.
        if graded:
            p_value = _binomial_p_at_least(n_correct, len(graded), config.chance_rate)
            if p_value > config.chance_alpha:
                flags.append(f"chance_level (p={p_value:.3f} vs chance={config.chance_rate:.2f})")

        # Excessive missing / incomplete data.
        expected = config.expected_trials
        if expected and expected > 0:
            completion = n_trials / expected
            if completion < config.min_completion:
                flags.append(f"incomplete ({n_trials}/{expected} trials, {completion:.0%})")

        # Implausible ceiling performance: perfect accuracy with implausibly fast RT.
        if (
            graded
            and accuracy >= config.ceiling_accuracy
            and mean_rt is not None
            and mean_rt < config.rt_floor_ms * config.ceiling_fast_multiplier
        ):
            flags.append(f"ceiling_implausible (100% correct, mean RT {mean_rt:.0f}ms)")

        # High proportion of fast-guess / outlier trials also contributes a flag.
        if n_trials and (n_fast_guess / n_trials) >= 0.2:
            flags.append(f"high_fast_guess_rate ({n_fast_guess}/{n_trials} trials)")

        summaries.append(
            SubjectSummary(
                subject=subject,
                n_trials=n_trials,
                n_correct=n_correct,
                accuracy=accuracy,
                mean_rt=mean_rt,
                median_rt=median_rt,
                sd_rt=sd_rt,
                n_fast_guess=n_fast_guess,
                n_outlier=n_outlier,
                flags=flags,
            )
        )

    return summaries


def summarize_conditions(trials: list[Trial]) -> list[ConditionSummary]:
    by_condition: dict[str, list[Trial]] = {}
    for t in trials:
        by_condition.setdefault(t.condition, []).append(t)

    summaries: list[ConditionSummary] = []
    for condition, cond_trials in sorted(by_condition.items()):
        graded = [t for t in cond_trials if t.correct is not None]
        n_correct = sum(1 for t in graded if t.correct)
        accuracy = (n_correct / len(graded)) if graded else 0.0
        correct_rts = [t.rt_ms for t in cond_trials if t.rt_ms is not None and t.correct]
        mean_rt = statistics.mean(correct_rts) if correct_rts else None
        sd_rt = statistics.pstdev(correct_rts) if len(correct_rts) > 1 else (0.0 if correct_rts else None)
        n_subjects = len({t.subject for t in cond_trials})

        summaries.append(
            ConditionSummary(
                condition=condition,
                n_trials=len(cond_trials),
                n_subjects=n_subjects,
                accuracy=accuracy,
                mean_rt=mean_rt,
                sd_rt=sd_rt,
            )
        )

    return summaries


def recommend_exclusions(
    subjects: list[SubjectSummary], config: QCConfig
) -> list[SubjectSummary]:
    """Subjects meeting or exceeding the configured flag-count threshold."""
    return [s for s in subjects if len(s.flags) >= config.exclude_threshold]


def learning_curve(
    trials: list[Trial], n_bins: int = 5
) -> dict[str, list[dict]]:
    """Accuracy/RT trend across binned trial position, per condition."""
    by_condition: dict[str, list[Trial]] = {}
    for t in trials:
        by_condition.setdefault(t.condition, []).append(t)

    curves: dict[str, list[dict]] = {}
    for condition, cond_trials in sorted(by_condition.items()):
        ordered = sorted(cond_trials, key=lambda t: (t.subject, t.block, t.trial_num))
        n = len(ordered)
        if n == 0:
            curves[condition] = []
            continue
        bin_size = max(1, math.ceil(n / n_bins))
        points = []
        for b in range(0, n, bin_size):
            chunk = ordered[b : b + bin_size]
            graded = [t for t in chunk if t.correct is not None]
            acc = (sum(1 for t in graded if t.correct) / len(graded)) if graded else 0.0
            rts = [t.rt_ms for t in chunk if t.rt_ms is not None and t.correct]
            mean_rt = statistics.mean(rts) if rts else None
            points.append({"bin": len(points) + 1, "accuracy": acc, "mean_rt": mean_rt, "n": len(chunk)})
        curves[condition] = points

    return curves

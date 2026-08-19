"""Deterministic effort audit: per-line validation and cross-grant overcommitment detection."""

from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from src.models import AuditConfig, EffortLine, Flag, OvercommitmentWindow, Severity


def audit_effort(
    lines: list[EffortLine], budget_grant_ids: set[str], config: AuditConfig
) -> tuple[list[Flag], list[OvercommitmentWindow]]:
    flags: list[Flag] = []

    grant_names: dict[str, set[str]] = defaultdict(set)
    valid_lines: list[EffortLine] = []

    for el in lines:
        if el.percent_effort <= 0:
            flags.append(
                Flag(
                    Severity.ERROR,
                    "zero_or_negative_effort",
                    f"Row {el.row_number}: percent_effort {el.percent_effort} must be positive",
                    grant_id=el.grant_id,
                    person_name=el.person_name,
                    row_numbers=(el.row_number,),
                )
            )
            continue

        if el.percent_effort > 100:
            flags.append(
                Flag(
                    Severity.ERROR,
                    "effort_over_100_single_line",
                    f"Row {el.row_number}: a single commitment of {el.percent_effort}% exceeds 100%",
                    grant_id=el.grant_id,
                    person_name=el.person_name,
                    row_numbers=(el.row_number,),
                )
            )

        if el.period_end < el.period_start:
            flags.append(
                Flag(
                    Severity.ERROR,
                    "invalid_period",
                    f"Row {el.row_number}: period_end {el.period_end} is before period_start {el.period_start}",
                    grant_id=el.grant_id,
                    person_name=el.person_name,
                    row_numbers=(el.row_number,),
                )
            )
            continue

        if el.grant_id not in budget_grant_ids:
            flags.append(
                Flag(
                    Severity.INFO,
                    "orphan_effort_grant",
                    f"Row {el.row_number}: grant_id '{el.grant_id}' has no matching entry in the budget file",
                    grant_id=el.grant_id,
                    person_name=el.person_name,
                    row_numbers=(el.row_number,),
                )
            )

        grant_names[el.grant_id].add(el.grant_name)
        valid_lines.append(el)

    for grant_id, names in grant_names.items():
        if len(names) > 1:
            flags.append(
                Flag(
                    Severity.WARNING,
                    "grant_name_mismatch",
                    f"grant_id '{grant_id}' appears with different grant_name values: {sorted(names)}",
                    grant_id=grant_id,
                )
            )

    windows = _find_overcommitment_windows(valid_lines, config.effort_cap_percent)
    for w in windows:
        flags.append(
            Flag(
                Severity.ERROR,
                "overcommitment",
                f"{w.person_name}: effort commitments total {w.peak_percent:.1f}% from {w.start.isoformat()} "
                f"to {w.end.isoformat()} across grants {', '.join(w.grant_ids)} (cap {config.effort_cap_percent:.0f}%)",
                person_name=w.person_name,
                row_numbers=(),
            )
        )

    return flags, windows


def _find_overcommitment_windows(
    lines: list[EffortLine], cap_percent: float
) -> list[OvercommitmentWindow]:
    windows: list[OvercommitmentWindow] = []

    by_person: dict[str, list[EffortLine]] = defaultdict(list)
    for el in lines:
        by_person[el.person_name].append(el)

    for person_name, person_lines in by_person.items():
        events_by_date: dict = defaultdict(list)
        for el in person_lines:
            events_by_date[el.period_start].append((el.percent_effort, el.grant_id))
            events_by_date[el.period_end + timedelta(days=1)].append((-el.percent_effort, el.grant_id))

        dates = sorted(events_by_date.keys())
        running_total = 0.0
        active_grants: dict[str, float] = defaultdict(float)

        window_start = None
        window_peak = 0.0
        window_peak_grants: set[str] = set()
        window_end = None

        for i, d in enumerate(dates):
            for delta, grant_id in events_by_date[d]:
                running_total += delta
                active_grants[grant_id] += delta
                if abs(active_grants[grant_id]) < 1e-9:
                    del active_grants[grant_id]

            segment_end = dates[i + 1] - timedelta(days=1) if i + 1 < len(dates) else d

            if running_total > cap_percent + 1e-9:
                if window_start is None:
                    window_start = d
                    window_peak = running_total
                    window_peak_grants = set(active_grants.keys())
                elif running_total > window_peak:
                    window_peak = running_total
                    window_peak_grants = set(active_grants.keys())
                window_end = segment_end
            else:
                if window_start is not None:
                    windows.append(
                        OvercommitmentWindow(
                            person_name=person_name,
                            start=window_start,
                            end=window_end,
                            peak_percent=window_peak,
                            grant_ids=tuple(sorted(window_peak_grants)),
                        )
                    )
                    window_start = None
                    window_peak = 0.0
                    window_peak_grants = set()

        if window_start is not None:
            windows.append(
                OvercommitmentWindow(
                    person_name=person_name,
                    start=window_start,
                    end=window_end,
                    peak_percent=window_peak,
                    grant_ids=tuple(sorted(window_peak_grants)),
                )
            )

    return windows

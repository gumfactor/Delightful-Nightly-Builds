"""Deterministic budget audit: MTDC computation and cross-checks."""

from __future__ import annotations

from collections import defaultdict

from src.models import AuditConfig, BudgetLine, Flag, GrantBudgetSummary, KNOWN_BUDGET_CATEGORIES, Severity


def audit_budget(
    lines: list[BudgetLine], config: AuditConfig
) -> tuple[list[Flag], list[GrantBudgetSummary]]:
    flags: list[Flag] = []
    summaries: list[GrantBudgetSummary] = []

    groups: dict[tuple[str, str], list[BudgetLine]] = defaultdict(list)
    for line in lines:
        groups[(line.grant_id, line.fiscal_year)].append(line)

    for (grant_id, fiscal_year), group_lines in groups.items():
        grant_name = group_lines[0].grant_name

        categories_present = {gl.category for gl in group_lines}
        if "Personnel" in categories_present and "Fringe Benefits" not in categories_present:
            flags.append(
                Flag(
                    Severity.WARNING,
                    "missing_fringe",
                    f"{grant_name} ({fiscal_year}): has a Personnel line but no Fringe Benefits line",
                    grant_id=grant_id,
                )
            )

        seen_keys: dict[tuple, int] = {}
        direct_total = 0.0
        mtdc = 0.0
        stated_indirect = 0.0

        for gl in group_lines:
            if gl.category not in KNOWN_BUDGET_CATEGORIES:
                flags.append(
                    Flag(
                        Severity.WARNING,
                        "unknown_category",
                        f"{grant_name} ({fiscal_year}), row {gl.row_number}: unrecognized category '{gl.category}'",
                        grant_id=grant_id,
                        row_numbers=(gl.row_number,),
                    )
                )

            if gl.direct_cost <= 0:
                flags.append(
                    Flag(
                        Severity.ERROR,
                        "zero_or_negative_cost",
                        f"{grant_name} ({fiscal_year}), row {gl.row_number}: direct_cost {gl.direct_cost} must be positive",
                        grant_id=grant_id,
                        row_numbers=(gl.row_number,),
                    )
                )

            dup_key = (gl.category, gl.description, round(gl.direct_cost, 2))
            if dup_key in seen_keys:
                flags.append(
                    Flag(
                        Severity.WARNING,
                        "duplicate_line",
                        f"{grant_name} ({fiscal_year}): rows {seen_keys[dup_key]} and {gl.row_number} appear to be duplicate line items",
                        grant_id=grant_id,
                        row_numbers=(seen_keys[dup_key], gl.row_number),
                    )
                )
            else:
                seen_keys[dup_key] = gl.row_number

            if gl.category == "Indirect":
                stated_indirect += gl.direct_cost
                continue

            direct_total += gl.direct_cost

            if gl.category == "Subcontract":
                included = min(gl.direct_cost, config.subcontract_exempt_threshold)
                excluded = max(0.0, gl.direct_cost - config.subcontract_exempt_threshold)
                mtdc += included
                if excluded > 0:
                    flags.append(
                        Flag(
                            Severity.INFO,
                            "subcontract_threshold_applied",
                            f"{grant_name} ({fiscal_year}), row {gl.row_number}: only the first "
                            f"${config.subcontract_exempt_threshold:,.2f} of this ${gl.direct_cost:,.2f} "
                            "subcontract is included in MTDC; ${:,.2f} excluded".format(excluded),
                            grant_id=grant_id,
                            row_numbers=(gl.row_number,),
                        )
                    )
            elif gl.category in config.mtdc_exempt_categories:
                pass
            else:
                mtdc += gl.direct_cost

        expected_indirect = round(mtdc * config.far_rate, 2)

        if stated_indirect > 0:
            delta = round(stated_indirect - expected_indirect, 2)
            if abs(delta) > config.tolerance:
                flags.append(
                    Flag(
                        Severity.ERROR,
                        "indirect_mismatch",
                        f"{grant_name} ({fiscal_year}): stated indirect cost ${stated_indirect:,.2f} does not "
                        f"match expected ${expected_indirect:,.2f} (MTDC ${mtdc:,.2f} x {config.far_rate:.2%}), "
                        f"delta ${delta:,.2f}",
                        grant_id=grant_id,
                    )
                )
        else:
            flags.append(
                Flag(
                    Severity.INFO,
                    "no_indirect_line",
                    f"{grant_name} ({fiscal_year}): no Indirect line found; expected indirect cost is "
                    f"${expected_indirect:,.2f} (MTDC ${mtdc:,.2f} x {config.far_rate:.2%})",
                    grant_id=grant_id,
                )
            )

        total = direct_total + (stated_indirect if stated_indirect > 0 else expected_indirect)

        summaries.append(
            GrantBudgetSummary(
                grant_id=grant_id,
                grant_name=grant_name,
                fiscal_year=fiscal_year,
                direct_total=direct_total,
                mtdc=mtdc,
                expected_indirect=expected_indirect,
                stated_indirect=stated_indirect,
                total=total,
            )
        )

    return flags, summaries

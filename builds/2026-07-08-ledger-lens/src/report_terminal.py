"""Colored terminal summary output."""

from __future__ import annotations

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
DIM = "\033[2m"


def render_terminal(
    summary: dict,
    categories: list,
    top_merchants: list,
    recurring: list,
    budget_status: list | None,
    insights: str,
    currency_symbol: str = "$",
) -> str:
    lines = []
    lines.append(f"{BOLD}{CYAN}Ledger Lens — Spending Report{RESET}")
    lines.append(
        f"{summary['months_covered']} month(s), {summary['transaction_count']} transactions\n"
    )

    lines.append(f"{BOLD}Overview{RESET}")
    lines.append(f"  Income:    {GREEN}{currency_symbol}{summary['total_income']:.2f}{RESET}")
    lines.append(f"  Expenses:  {RED}{currency_symbol}{summary['total_expenses']:.2f}{RESET}")
    lines.append(f"  Net:       {currency_symbol}{summary['net']:.2f}")
    lines.append(f"  Avg/day:   {currency_symbol}{summary['avg_daily_spend']:.2f}\n")

    lines.append(f"{BOLD}Top Categories{RESET}")
    for cat in categories[:8]:
        lines.append(
            f"  {cat['category']:<16} {currency_symbol}{cat['total']:>9.2f}  "
            f"({cat['pct_of_expenses']:.1f}%, {cat['count']} txns)"
        )
    lines.append("")

    lines.append(f"{BOLD}Top Merchants{RESET}")
    for merchant in top_merchants[:5]:
        lines.append(
            f"  {merchant['merchant']:<30} {currency_symbol}{merchant['total']:>9.2f}  "
            f"({merchant['count']}x)"
        )
    lines.append("")

    lines.append(f"{BOLD}Recurring Charges{RESET}")
    if recurring:
        for rec in recurring:
            lines.append(
                f"  {rec['merchant']:<30} {currency_symbol}{rec['avg_amount']:>7.2f}/mo  "
                f"({rec['occurrences']}x over {rec['months_seen']} months)"
            )
    else:
        lines.append(f"  {DIM}None detected.{RESET}")
    lines.append("")

    if budget_status:
        lines.append(f"{BOLD}Budget vs. Actual (monthly avg){RESET}")
        for b in budget_status:
            flag = f"{RED}OVER{RESET}" if b["over_budget"] else f"{GREEN}ok{RESET}"
            lines.append(
                f"  {b['category']:<16} {currency_symbol}{b['monthly_avg_actual']:>8.2f} "
                f"/ {currency_symbol}{b['monthly_cap']:.2f}  ({b['pct_of_cap']:.0f}%)  {flag}"
            )
        lines.append("")

    lines.append(f"{BOLD}Insights{RESET}")
    lines.append(f"  {insights}")

    return "\n".join(lines)

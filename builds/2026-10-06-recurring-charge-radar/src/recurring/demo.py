"""Synthetic statement generator for --demo and tests. No real data."""
from __future__ import annotations

import random
from datetime import date, timedelta

from .detect import add_months
from .models import Transaction


def demo_transactions(end: date = date(2026, 10, 6), seed: int = 7) -> list[Transaction]:
    rng = random.Random(seed)
    txns: list[Transaction] = []

    def monthly(desc: str, amount: float, day: int, months: int = 14, stop: date | None = None,
                hike: tuple[date, float] | None = None) -> None:
        start = add_months(date(end.year, end.month, 1), -months)
        for i in range(months + 1):
            when = add_months(start, i).replace(day=min(day, 28))
            if when > end or (stop and when > stop):
                continue
            price = hike[1] if hike and when >= hike[0] else amount
            txns.append(Transaction(when, desc, price, "demo.csv"))

    monthly("NETFLIX.COM 866-579-7172 CA", 20.99, 3, hike=(date(2026, 3, 3), 23.99))
    monthly("SPOTIFY P1A2B3C4 STOCKHOLM", 12.99, 11)
    monthly("OPENAI *CHATGPT SUBSCR SAN FRANCISCO CA", 27.40, 14)
    monthly("ANTHROPIC CLAUDE.AI SUBSCRIPTION", 27.40, 19)
    monthly("GOODLIFE FITNESS #4412 TORONTO ON", 14.97, 1)
    monthly("DROPBOX*PLUS DUBLIN IE", 13.50, 6, stop=date(2026, 2, 28))
    monthly("PAP ROGERS WIRELESS", 85.00, 22)
    monthly("GITHUB, INC. SAN FRANCISCO CA", 5.45, 8)
    for i in range(15):
        when = add_months(date(end.year, end.month, 1), -14 + i).replace(day=26)
        if when <= end:
            txns.append(Transaction(when, "TORONTO HYDRO PAP", round(rng.uniform(70, 150), 2), "demo.csv"))
    for year, price in ((2024, 20.18), (2025, 20.18), (2026, 22.48)):
        when = date(year, 9, 22)
        if when <= end:
            txns.append(Transaction(when, "NAMECHEAP.COM PHOENIX AZ", price, "demo.csv"))
    for year in (2025,):
        txns.append(Transaction(date(year, 10, 15), "AMAZON PRIME*MEMBERSHIP", 99.00, "demo.csv"))
    # Irregular spending that must NOT be flagged.
    when = end - timedelta(days=420)
    while when <= end:
        if rng.random() < 0.55:
            txns.append(Transaction(when, f"STARBUCKS #{rng.randint(1000, 9999)} TORONTO ON",
                                    round(rng.uniform(4.5, 12.5), 2), "demo.csv"))
        when += timedelta(days=rng.randint(1, 6))
    for _ in range(40):
        when = end - timedelta(days=rng.randint(0, 420))
        txns.append(Transaction(when, f"LOBLAWS #{rng.randint(100, 999)} TORONTO ON",
                                round(rng.uniform(25, 190), 2), "demo.csv"))
    txns.sort(key=lambda t: t.date)
    return txns

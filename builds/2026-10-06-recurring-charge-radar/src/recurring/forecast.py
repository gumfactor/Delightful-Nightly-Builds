"""Forecast upcoming charges and export them as an iCalendar file."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .detect import advance
from .models import Series


@dataclass(frozen=True)
class Upcoming:
    date: date
    merchant: str
    amount: float
    cadence: str
    variable: bool


def upcoming_charges(series: list[Series], today: date, days: int = 60) -> list[Upcoming]:
    """All expected charges between ``today`` and ``today + days`` (inclusive)."""
    horizon = today + timedelta(days=days)
    out: list[Upcoming] = []
    for item in series:
        if item.status not in ("active", "zombie") or item.next_expected is None:
            continue
        due, step = item.next_expected, 0
        while due <= horizon:
            if due >= today:
                out.append(Upcoming(due, item.merchant, item.typical_amount, item.cadence, item.variable))
            step += 1
            due = advance(item.next_expected, item.cadence, step)
    out.sort(key=lambda u: (u.date, -u.amount))
    return out


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", "\;").replace(",", "\\,").replace("\n", "\\n")


def to_ics(items: list[Upcoming]) -> str:
    """Render all-day VEVENTs. Lines are CRLF-terminated per RFC 5545."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Recurring Charge Radar//EN", "CALSCALE:GREGORIAN"]
    for index, item in enumerate(items):
        stamp = item.date.strftime("%Y%m%d")
        prefix = "~" if item.variable else ""
        lines += [
            "BEGIN:VEVENT",
            f"UID:{stamp}-{index}@recurring-charge-radar",
            f"DTSTAMP:{stamp}T000000Z",
            f"DTSTART;VALUE=DATE:{stamp}",
            f"DTEND;VALUE=DATE:{(item.date + timedelta(days=1)).strftime('%Y%m%d')}",
            f"SUMMARY:{_escape(f'{item.merchant} {prefix}${item.amount:.2f}')}",
            f"DESCRIPTION:{_escape(f'Expected {item.cadence} charge')}",
            "BEGIN:VALARM",
            "TRIGGER:-P2D",
            "ACTION:DISPLAY",
            "DESCRIPTION:Charge in 2 days",
            "END:VALARM",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"

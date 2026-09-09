"""Optional plain-English admin briefing via the Anthropic Messages API.

Called directly with `urllib.request` — no `anthropic` package needed, and
none is installed in the build/test environment. Only aggregate numbers
(room balances, overcontribution flags, deadline dates) are ever sent —
never individual transaction dates or amounts. With no `ANTHROPIC_API_KEY`
set, `generate_briefing` never attempts a network call and returns a
deterministic template sentence instead.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import date

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
REQUEST_TIMEOUT_SECONDS = 20


def build_summary_payload(
    tfsa_available_room: float,
    tfsa_is_overcontributed: bool,
    tfsa_overcontribution_amount: float,
    rrsp_available_room: float,
    rrsp_is_overcontributed: bool,
    rrsp_overcontribution_amount: float,
    rrsp_deadline: date,
    rrsp_deadline_tax_year: int,
    tfsa_next_room_date: date,
) -> dict:
    return {
        "tfsa_available_room": round(tfsa_available_room, 2),
        "tfsa_is_overcontributed": tfsa_is_overcontributed,
        "tfsa_overcontribution_amount": round(tfsa_overcontribution_amount, 2),
        "rrsp_available_room": round(rrsp_available_room, 2),
        "rrsp_is_overcontributed": rrsp_is_overcontributed,
        "rrsp_overcontribution_amount": round(rrsp_overcontribution_amount, 2),
        "rrsp_deadline": rrsp_deadline.isoformat(),
        "rrsp_deadline_tax_year": rrsp_deadline_tax_year,
        "tfsa_next_room_date": tfsa_next_room_date.isoformat(),
    }


def deterministic_summary(payload: dict) -> str:
    parts = []
    if payload["tfsa_is_overcontributed"]:
        parts.append(
            f"TFSA is over-contributed by ${payload['tfsa_overcontribution_amount']:,.2f} — "
            "withdraw the excess as soon as possible to stop the 1%/month CRA tax."
        )
    else:
        parts.append(f"TFSA has ${payload['tfsa_available_room']:,.2f} of room available.")

    if payload["rrsp_is_overcontributed"]:
        parts.append(
            f"RRSP is over-contributed by ${payload['rrsp_overcontribution_amount']:,.2f} "
            "beyond the $2,000 grace buffer — the 1%/month CRA tax is accruing."
        )
    else:
        parts.append(f"RRSP has ${payload['rrsp_available_room']:,.2f} of room available.")

    parts.append(
        f"Next RRSP contribution deadline: {payload['rrsp_deadline']} "
        f"(applies to tax year {payload['rrsp_deadline_tax_year']})."
    )
    parts.append(f"Next TFSA room opens: {payload['tfsa_next_room_date']}.")
    return " ".join(parts)


def generate_briefing(payload: dict, api_key: str | None) -> str:
    if not api_key:
        return deterministic_summary(payload)

    prompt = (
        "You are a concise personal-finance admin assistant. Given only these "
        "aggregate RRSP/TFSA figures (JSON), write a 2-3 sentence plain-English "
        "status update with any urgent action item. Never invent numbers not "
        f"present in the JSON.\n\n{json.dumps(payload)}"
    )
    body = json.dumps(
        {
            "model": ANTHROPIC_MODEL,
            "max_tokens": 300,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=body,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            result = json.loads(response.read())
        return result["content"][0]["text"]
    except (OSError, KeyError, IndexError, ValueError):
        # OSError covers urllib.error.URLError/HTTPError plus raw socket/timeout
        # failures; KeyError/IndexError/ValueError cover a malformed response body.
        return deterministic_summary(payload)

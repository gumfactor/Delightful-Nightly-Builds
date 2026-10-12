"""Optional AI commentary via the Anthropic Messages API (stdlib HTTP, key from env)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Callable

from .metrics import summarize

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-sonnet-5-5"

Transport = Callable[[str, dict, dict], dict]


class AiError(Exception):
    pass


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.1f}%"


def _money(value: float | None) -> str:
    if value is None:
        return "n/a"
    sign = "-" if value < 0 else ""
    value = abs(value)
    for threshold, suffix in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
        if value >= threshold:
            return f"{sign}${value / threshold:.2f}{suffix}"
    return f"{sign}${value:,.0f}"


def build_prompt(companies: list[dict]) -> str:
    lines = ["Compare these companies using only the figures below (from SEC 10-K XBRL data).",
             "Write 4-6 plain sentences for an analyst: who is growing fastest, who converts "
             "revenue to cash best, balance-sheet risk, and one caveat about comparability. "
             "No hype, no investment advice, do not invent numbers.", ""]
    for company in companies:
        s = summarize(company)
        lines.append(
            f"{s['ticker']} ({s['name']}), FY{s['latest_year']}: revenue {_money(s['revenue'])}, "
            f"net income {_money(s['net_income'])}, FCF {_money(s['free_cash_flow'])}, "
            f"gross margin {_pct(s['gross_margin'])}, operating margin {_pct(s['operating_margin'])}, "
            f"net margin {_pct(s['net_margin'])}, ROE {_pct(s['roe'])}, "
            f"revenue CAGR {_pct(s['revenue_cagr'])}, net income CAGR {_pct(s['net_income_cagr'])}")
    return "\n".join(lines)


def http_transport(url: str, headers: dict, body: dict) -> dict:
    request = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raise AiError(f"Anthropic API returned HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise AiError(f"Anthropic API request failed: {exc}") from exc


def commentary(companies: list[dict], transport: Transport = http_transport,
               model: str | None = None) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise AiError("ANTHROPIC_API_KEY is not set; skipping AI commentary.")
    if not companies:
        raise AiError("No companies to comment on.")
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    body = {"model": model or os.environ.get("EDGAR_AI_MODEL", DEFAULT_MODEL), "max_tokens": 600,
            "messages": [{"role": "user", "content": build_prompt(companies)}]}
    reply = transport(API_URL, headers, body)
    parts = [block.get("text", "") for block in reply.get("content", []) if block.get("type") == "text"]
    text = "".join(parts).strip()
    if not text:
        raise AiError("Anthropic API returned no text.")
    return text

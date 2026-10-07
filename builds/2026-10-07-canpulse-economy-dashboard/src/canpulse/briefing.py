"""Plain-English briefing: Claude if ANTHROPIC_API_KEY is set, rule-based otherwise."""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any, Callable

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-haiku-4-5-20251001"

Poster = Callable[[str, dict, dict], dict]


def _fmt(sid: str, st: dict) -> str:
    yoy = st.get("yoy")
    suffix = "" if yoy is None else f", {yoy:+.1f}{'%' if st['yoy_kind'] == 'pct' else ' pp'} y/y"
    return f"{st['latest']:.2f} ({st['latest_date']}){suffix}"


def rule_based(series: dict[str, dict], stats: dict[str, dict]) -> list[str]:
    lines: list[str] = []
    if "cpi" in stats and stats["cpi"].get("yoy") is not None:
        c = stats["cpi"]["yoy"]
        tone = "above the BoC's 1–3% target band" if c > 3 else (
            "below the BoC's 1–3% target band" if c < 1 else "inside the BoC's 1–3% target band")
        lines.append(f"Inflation is {c:.1f}% year over year, {tone}.")
    if "policy_rate" in stats:
        lines.append(f"The BoC overnight rate is {stats['policy_rate']['latest']:.2f}%"
                     + (f"; real policy rate {stats['real_rate']['latest']:+.1f} pp."
                        if "real_rate" in stats else "."))
    if "curve" in stats:
        cv = stats["curve"]["latest"]
        lines.append(f"The 10y–2y curve is {cv:+.2f} pp ({'inverted' if cv < 0 else 'positively sloped'}).")
    if "unemployment" in stats:
        u = stats["unemployment"]
        lines.append(f"Unemployment is {u['latest']:.1f}% and {u['trend']} over three months.")
    if "usdcad" in stats:
        u = stats["usdcad"]
        lines.append(f"USD/CAD is {u['latest']:.4f} ({u['chg_1m']:+.1f}% over a month)."
                     if u.get("chg_1m") is not None else f"USD/CAD is {u['latest']:.4f}.")
    flagged = [f"{series[sid]['label']}: {st['reason']}" for sid, st in stats.items()
               if st["signal"] in ("watch", "bad") and sid in series]
    if flagged:
        lines.append("Flags: " + "; ".join(flagged) + ".")
    return lines


def build_prompt(series: dict[str, dict], stats: dict[str, dict]) -> str:
    rows = [f"- {series[sid]['label']}: {_fmt(sid, st)}; trend {st['trend']}; "
            f"5y percentile {st['pct5y']:.0f}; signal {st['signal']}"
            for sid, st in stats.items() if sid in series]
    return ("You are briefing a Canadian academic/founder who follows Canadian economic policy "
            "and runs a consumer platform. Using ONLY the public statistics below, write 4-6 "
            "short plain sentences (no hype, no filler, no bullet markup) on what the numbers "
            "say about inflation, rates, jobs, housing and the Canadian dollar, and what is "
            "notable or contradictory. Do not speculate beyond the data.\n\n" + "\n".join(rows))


def http_post(url: str, headers: dict, payload: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 - fixed https host
        return json.loads(resp.read().decode())


def ai_briefing(series: dict[str, dict], stats: dict[str, dict], api_key: str | None = None,
                post: Poster = http_post) -> dict[str, Any]:
    """Return {'source': 'ai'|'rules', 'lines': [...], 'error': str|None}."""
    key = api_key if api_key is not None else os.environ.get("ANTHROPIC_API_KEY", "")
    fallback = rule_based(series, stats)
    if not key:
        return {"source": "rules", "lines": fallback, "error": None}
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    payload = {"model": MODEL, "max_tokens": 500,
               "messages": [{"role": "user", "content": build_prompt(series, stats)}]}
    try:
        resp = post(API_URL, headers, payload)
        text = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text").strip()
        if not text:
            raise ValueError("empty response")
        return {"source": "ai", "lines": [s for s in text.split("\n") if s.strip()], "error": None}
    except Exception as exc:  # noqa: BLE001 - always degrade to rules
        return {"source": "rules", "lines": fallback, "error": f"{type(exc).__name__}: {exc}"[:150]}

"""Render the dashboard HTML by embedding one JSON blob into template.html."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import config

TEMPLATE = Path(__file__).with_name("template.html")
CHART_JS_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.js"


def safe_json(obj: Any) -> str:
    """JSON safe to embed inside a <script> element."""
    text = json.dumps(obj, separators=(",", ":"), ensure_ascii=True)
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def build_payload(series: dict[str, dict], stats: dict[str, dict], errors: dict[str, str],
                  briefing: dict, meta: dict) -> dict[str, Any]:
    labels = {s["id"]: s for s in config.INDICATORS}
    failed = [{"id": sid, "label": labels[sid]["label"] if sid in labels else sid,
               "group": labels.get(sid, {}).get("group", "Other"), "error": msg}
              for sid, msg in errors.items() if sid not in series]
    order = [s["id"] for s in config.INDICATORS] + [d["id"] for d in config.DERIVED]
    ordered = [sid for sid in order if sid in series]
    return {"meta": meta, "order": ordered, "series": series, "stats": stats,
            "failed": failed, "briefing": briefing, "events": config.EVENTS}


def render_html(payload: dict[str, Any]) -> str:
    html = TEMPLATE.read_text(encoding="utf-8")
    return html.replace("/*__DATA__*/null", safe_json(payload)).replace("__CHART_JS_URL__", CHART_JS_URL)

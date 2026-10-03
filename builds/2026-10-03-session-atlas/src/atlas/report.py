"""Render the self-contained HTML explorer."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .stats import build_stats, resume_prompt
from .store import Store, prompts_by_source

TEMPLATE = Path(__file__).with_name("template.html")
PLACEHOLDER = "__ATLAS_DATA__"


def script_safe_json(payload: Any) -> str:
    """JSON that cannot terminate or alter the enclosing <script> element."""
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace(
        "\u2028", "\\u2028").replace("\u2029", "\\u2029")


def build_payload(store: Store, since: str | None = None, tz_offset_hours: float = 0.0) -> dict[str, Any]:
    sessions = store.sessions(since)
    prompts = prompts_by_source(store)
    rows = []
    for s in sessions:
        rows.append({
            "id": s["id"], "project": s["project"], "path": s["project_path"], "branch": s["branch"],
            "start": s["start"], "end": s["end"], "hours": round(s["active_seconds"] / 3600, 3),
            "prompts": s["prompts"], "assistant": s["assistant_msgs"], "sidechain": s["sidechain_msgs"],
            "errors": s["tool_errors"], "cost": s["cost_usd"], "unpriced": s["unpriced"],
            "tokens": s["input_tokens"] + s["output_tokens"] + s["cache_write_tokens"] + s["cache_read_tokens"],
            "tools": sorted(s["tools"].items(), key=lambda kv: kv[1], reverse=True)[:8],
            "files": sorted(s["files"].items(), key=lambda kv: kv[1], reverse=True)[:10],
            "title": s["title"], "summary": s["summary"], "first": s["first_prompt"][:400],
            "last": s["last_prompt"][:400], "final": s["last_assistant"][:800],
            "texts": prompts.get(s["source"], []), "resume": resume_prompt(s),
        })
    return {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tz": tz_offset_hours,
        "stats": build_stats(sessions, tz_offset_hours),
        "sessions": rows,
    }


def render_html(payload: dict[str, Any]) -> str:
    template = TEMPLATE.read_text(encoding="utf-8")
    return template.replace(PLACEHOLDER, script_safe_json(payload))


def write_report(store: Store, out_path: str | Path, since: str | None = None, tz_offset_hours: float = 0.0) -> Path:
    path = Path(out_path)
    path.write_text(render_html(build_payload(store, since, tz_offset_hours)), encoding="utf-8")
    return path

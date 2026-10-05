"""Generate a synthetic transcript corpus (no personal data) for trying the dashboard."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _assistant(session: str, cwd: str, ts: datetime, msg_id: str, model: str, usage: tuple[int, int, int, int],
               tools: list[tuple[str, str, dict]] | None = None, sidechain: bool = False) -> dict:
    return {
        "type": "assistant", "sessionId": session, "cwd": cwd, "timestamp": ts.isoformat(), "isSidechain": sidechain,
        "message": {
            "id": msg_id, "model": model,
            "usage": dict(zip(("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"), usage)),
            "content": [{"type": "tool_use", "id": tid, "name": name, "input": inp} for tid, name, inp in (tools or [])],
        },
    }


def _result(session: str, ts: datetime, tool_id: str, is_error: bool) -> dict:
    return {"type": "user", "sessionId": session, "timestamp": ts.isoformat(),
            "message": {"content": [{"type": "tool_result", "tool_use_id": tool_id, "is_error": is_error}]}}


def write_demo(root: Path, now: datetime | None = None) -> Path:
    now = now or datetime.now(timezone.utc)
    root.mkdir(parents=True, exist_ok=True)
    healthy = [_assistant("demo-healthy", "/work/canada-list", now - timedelta(days=3, minutes=40 - i), f"h{i}",
                          "claude-sonnet-4-5", (200, 600, 1500 if i == 0 else 100, 0 if i == 0 else 9000 + i * 900),
                          [(f"ht{i}", "Read", {"file_path": f"/work/canada-list/mod{i}.py"})]) for i in range(30)]
    thrash, base = [], now - timedelta(days=2, hours=2)
    for i in range(24):
        ts = base + timedelta(minutes=i * 2)
        thrash.append(_assistant("demo-thrash", "/work/kwyeter", ts, f"t{i}", "claude-opus-4-1", (500, 900, 4000, 20000 + i * 6000),
                                 [(f"tt{i}", "Read", {"file_path": "/work/kwyeter/app.dart"}), (f"tb{i}", "Bash", {"command": "flutter test"})],
                                 sidechain=i % 6 == 0))
        thrash.append(_result("demo-thrash", ts, f"tb{i}", i % 3 != 0))
    cold = [_assistant("demo-cold", "/work/lab-admin", now - timedelta(days=1, hours=1) + timedelta(minutes=i * 40), f"c{i}",
                       "claude-haiku-4-5", (60000, 800, 40000, 1000)) for i in range(4)]
    mystery = [_assistant("demo-new-model", "/work/lab-admin", now - timedelta(hours=3, minutes=-i), f"m{i}", "claude-future-9", (1000, 500, 0, 0))
               for i in range(3)]
    for name, rows in (("healthy", healthy), ("thrash", thrash), ("cold", cold + mystery)):
        project_dir = root / f"-work-{name}"
        project_dir.mkdir(exist_ok=True)
        lines = [json.dumps(r) for r in rows]
        lines.insert(1, "{not valid json")  # exercised by the parser's bad-line counter
        (project_dir / f"{name}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root

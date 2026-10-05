import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

BASE = datetime(2026, 10, 1, 15, 0, tzinfo=timezone.utc)


def assistant(sid="s1", msg_id="m1", ts=BASE, model="claude-sonnet-4-5", usage=(100, 50, 0, 0), tools=(), cwd="/w/proj", sidechain=False):
    return {
        "type": "assistant", "sessionId": sid, "cwd": cwd, "timestamp": ts.isoformat(), "isSidechain": sidechain,
        "message": {
            "id": msg_id, "model": model,
            "usage": dict(zip(("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"), usage)),
            "content": [{"type": "tool_use", "id": t, "name": n, "input": i} for t, n, i in tools],
        },
    }


def result(tool_id, is_error=False, sid="s1"):
    return {"type": "user", "sessionId": sid, "timestamp": BASE.isoformat(),
            "message": {"content": [{"type": "tool_result", "tool_use_id": tool_id, "is_error": is_error}]}}


@pytest.fixture
def write_transcript(tmp_path):
    def _write(rows, name="a.jsonl", raw_lines=()):
        folder = tmp_path / "projects" / "p"
        folder.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps(r) for r in rows] + list(raw_lines)
        (folder / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
        return tmp_path / "projects"
    return _write


def at(minutes):
    return BASE + timedelta(minutes=minutes)

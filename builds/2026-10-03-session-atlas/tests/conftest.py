import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def write_jsonl(path: Path, records: list) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(r if isinstance(r, str) else json.dumps(r) for r in records) + "\n", encoding="utf-8")
    return path


def user(ts, content, **extra):
    return {"type": "user", "sessionId": "s1", "cwd": "/work/proj", "gitBranch": "main", "timestamp": ts,
            "message": {"role": "user", "content": content}, **extra}


def assistant(ts, content, msg_id="m1", model="claude-sonnet-4-5", usage=None, **extra):
    message = {"id": msg_id, "role": "assistant", "model": model, "content": content}
    if usage is not None:
        message["usage"] = usage
    return {"type": "assistant", "sessionId": "s1", "cwd": "/work/proj", "timestamp": ts, "message": message, **extra}


@pytest.fixture
def basic_log(tmp_path):
    usage = {"input_tokens": 100, "output_tokens": 50, "cache_creation_input_tokens": 10, "cache_read_input_tokens": 900}
    records = [
        user("2026-09-01T10:00:00Z", "Fix the <b>parser</b> bug"),
        assistant("2026-09-01T10:00:20Z", [{"type": "tool_use", "id": "t1", "name": "Edit",
                                           "input": {"file_path": "/work/proj/a.py"}}], "m1", usage=usage),
        user("2026-09-01T10:00:30Z", [{"type": "tool_result", "tool_use_id": "t1", "is_error": True, "content": "x"}]),
        assistant("2026-09-01T10:00:50Z", [{"type": "text", "text": "Fixed it."}], "m2",
                  usage={"input_tokens": 10, "output_tokens": 5}),
    ]
    return write_jsonl(tmp_path / "logs" / "-work-proj" / "s1.jsonl", records)

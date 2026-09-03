"""Builders for synthetic Claude Code session transcript lines, used across the test suite.

These mirror the real JSONL shape verified against this build container's own session
transcript (see BUILD_LOG.md / WhyThis.md) without ever committing real transcript content.
"""
from __future__ import annotations

import json
import uuid as uuid_mod
from pathlib import Path

DEFAULT_SESSION = "session-aaaa"
DEFAULT_CWD = "/home/user/some-project"


def _uuid() -> str:
    return str(uuid_mod.uuid4())


def user_prompt(
    text: str,
    *,
    session_id: str = DEFAULT_SESSION,
    cwd: str = DEFAULT_CWD,
    timestamp: str = "2026-09-01T12:00:00.000Z",
    entrypoint: str = "cli",
    git_branch: str = "main",
    is_sidechain: bool = False,
    prompt_uuid: str | None = None,
) -> dict:
    return {
        "type": "user",
        "message": {"role": "user", "content": text},
        "uuid": prompt_uuid or _uuid(),
        "sessionId": session_id,
        "timestamp": timestamp,
        "cwd": cwd,
        "entrypoint": entrypoint,
        "gitBranch": git_branch,
        "isSidechain": is_sidechain,
    }


def tool_use_line(
    tool_name: str,
    tool_input: dict,
    *,
    tool_id: str | None = None,
    session_id: str = DEFAULT_SESSION,
    cwd: str = DEFAULT_CWD,
    timestamp: str = "2026-09-01T12:00:01.000Z",
) -> tuple[dict, str]:
    tid = tool_id or f"toolu_{_uuid()[:8]}"
    line = {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": tid, "name": tool_name, "input": tool_input}],
        },
        "uuid": _uuid(),
        "sessionId": session_id,
        "timestamp": timestamp,
        "cwd": cwd,
    }
    return line, tid


def tool_result_line(
    tool_use_id: str,
    content: str,
    *,
    is_error: bool = False,
    session_id: str = DEFAULT_SESSION,
    cwd: str = DEFAULT_CWD,
    timestamp: str = "2026-09-01T12:00:02.000Z",
) -> dict:
    return {
        "type": "user",
        "message": {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": content,
                    "is_error": is_error,
                }
            ],
        },
        "uuid": _uuid(),
        "sessionId": session_id,
        "timestamp": timestamp,
        "cwd": cwd,
        "isSidechain": False,
    }


def assistant_text_line(
    text: str,
    *,
    session_id: str = DEFAULT_SESSION,
    cwd: str = DEFAULT_CWD,
    timestamp: str = "2026-09-01T12:00:03.000Z",
) -> dict:
    return {
        "type": "assistant",
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
        "uuid": _uuid(),
        "sessionId": session_id,
        "timestamp": timestamp,
        "cwd": cwd,
    }


def bookkeeping_line(line_type: str = "queue-operation") -> dict:
    return {"type": line_type, "sessionId": DEFAULT_SESSION}


def write_jsonl(path: Path, lines: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for line in lines:
            fh.write(json.dumps(line))
            fh.write("\n")


def bash_episode(tool_input_command: str, result_text: str, *, is_error: bool = False) -> list[dict]:
    """A one-tool-call episode: an assistant Bash tool_use followed by its tool_result."""
    use_line, tid = tool_use_line("Bash", {"command": tool_input_command})
    result = tool_result_line(tid, result_text, is_error=is_error)
    return [use_line, result]


def edit_episode(file_path: str, *, is_error: bool = False, result_text: str = "OK") -> list[dict]:
    use_line, tid = tool_use_line("Edit", {"file_path": file_path, "old_string": "a", "new_string": "b"})
    result = tool_result_line(tid, result_text, is_error=is_error)
    return [use_line, result]

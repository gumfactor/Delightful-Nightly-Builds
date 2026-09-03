"""Extract human-authored prompt turns from Claude Code session transcript files.

Claude Code stores one JSONL file per session under a project directory (by default
``~/.claude/projects/<sanitized-cwd>/<session-id>.jsonl``). Each line is a JSON object.
The types relevant here (verified against a real transcript before writing this module):

- ``type: "user"`` with ``message.role == "user"`` — either a genuine human prompt turn
  (``message.content`` is a plain string, or a list containing a non-empty ``text`` block)
  or a tool-result echo (``message.content`` is a list of ``tool_result`` blocks only,
  the on-disk representation of a tool response per the Anthropic Messages API convention).
- ``type: "assistant"`` — Claude's own turns, including ``tool_use`` blocks.
- Other top-level types (``queue-operation``, ``attachment``, ``atis-latch``, ``summary``, …)
  are session bookkeeping, not conversation turns, and are skipped.

Lines with ``isSidechain: true`` belong to a subagent's internal transcript, not the
top-level human/Claude conversation, and are excluded from prompt extraction.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator


@dataclass
class RawLine:
    """One parsed JSONL line, kept generic so episode.py can walk raw lines too."""

    index: int
    obj: dict[str, Any]


@dataclass
class PromptTurn:
    """A single human-authored prompt extracted from a session transcript."""

    prompt_uuid: str
    session_id: str
    project: str
    git_branch: str | None
    entrypoint: str | None
    timestamp: str
    prompt_text: str
    line_index: int  # index of this line within the source file (for episode scoping)


def read_jsonl_lines(path: Path) -> list[RawLine]:
    """Read a transcript file into raw parsed lines, skipping malformed lines."""
    lines: list[RawLine] = []
    with path.open("r", encoding="utf-8") as fh:
        for i, raw in enumerate(fh):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            lines.append(RawLine(index=i, obj=obj))
    return lines


def _extract_text_from_content(content: Any) -> str | None:
    """Return human-authored prompt text from a message content value, or None if this
    turn is not a genuine prompt (e.g. a pure tool_result echo)."""
    if isinstance(content, str):
        stripped = content.strip()
        return stripped if stripped else None

    if isinstance(content, list):
        text_parts: list[str] = []
        saw_only_tool_result = True
        for block in content:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "text":
                saw_only_tool_result = False
                text = block.get("text", "")
                if isinstance(text, str) and text.strip():
                    text_parts.append(text.strip())
            elif block_type != "tool_result":
                saw_only_tool_result = False
        if saw_only_tool_result or not text_parts:
            return None
        return "\n".join(text_parts)

    return None


def extract_prompts(lines: list[RawLine]) -> list[PromptTurn]:
    """Extract genuine human-authored prompt turns from a session's raw lines."""
    prompts: list[PromptTurn] = []
    for raw_line in lines:
        obj = raw_line.obj
        if obj.get("type") != "user":
            continue
        if obj.get("isSidechain") is True:
            continue

        message = obj.get("message")
        if not isinstance(message, dict):
            continue
        if message.get("role") != "user":
            continue

        text = _extract_text_from_content(message.get("content"))
        if text is None:
            continue

        prompt_uuid = obj.get("uuid")
        session_id = obj.get("sessionId")
        timestamp = obj.get("timestamp")
        if not prompt_uuid or not session_id or not timestamp:
            continue

        prompts.append(
            PromptTurn(
                prompt_uuid=str(prompt_uuid),
                session_id=str(session_id),
                project=str(obj.get("cwd") or "unknown"),
                git_branch=obj.get("gitBranch"),
                entrypoint=obj.get("entrypoint"),
                timestamp=str(timestamp),
                prompt_text=text,
                line_index=raw_line.index,
            )
        )
    return prompts


def iter_session_files(claude_dir: Path) -> Iterator[Path]:
    """Yield every session transcript file under a Claude Code projects directory."""
    if not claude_dir.exists():
        return
    yield from sorted(claude_dir.glob("**/*.jsonl"))

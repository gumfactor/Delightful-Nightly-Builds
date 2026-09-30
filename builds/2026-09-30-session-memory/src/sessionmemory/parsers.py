"""Parsers for AI conversation transcripts. Read-only; malformed input is skipped."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

from .models import Message, Session

SYSTEM_BLOCK = re.compile(r"<(system-reminder|local-command-stdout|local-command-caveat)>.*?</\1>", re.S)
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
MAX_MESSAGE_CHARS = 20000


def clean_text(text: str) -> str:
    text = SYSTEM_BLOCK.sub("", text or "").strip()
    return text[:MAX_MESSAGE_CHARS]


def _text_from_blocks(content: Any) -> str:
    """Join the human-readable text blocks; tool_use/tool_result/thinking are dropped."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    return "\n".join(part for part in parts if part)


def _iso_from_epoch(value: Any) -> str:
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError, OverflowError, OSError):
        return ""


def _decode_project_dir(dirname: str) -> str:
    # Claude Code encodes /home/me/proj as -home-me-proj; the last segment is the best label.
    parts = [part for part in dirname.split("-") if part]
    return parts[-1] if parts else dirname


def parse_claude_code(path: Path) -> Session | None:
    messages: list[Message] = []
    files: list[str] = []
    cwd = branch = title = session_id = ""
    try:
        handle = path.open(encoding="utf-8", errors="replace")
    except OSError:
        return None
    with handle:
        for line in handle:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            kind = record.get("type")
            if kind == "summary" and record.get("summary"):
                title = title or str(record["summary"])
                continue
            if kind not in ("user", "assistant") or record.get("isMeta"):
                continue
            session_id = session_id or str(record.get("sessionId", ""))
            cwd = cwd or str(record.get("cwd", ""))
            branch = branch or str(record.get("gitBranch", ""))
            message = record.get("message")
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if kind == "assistant" and isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") in EDIT_TOOLS:
                        target = (block.get("input") or {}).get("file_path") or (block.get("input") or {}).get("notebook_path")
                        if target and target not in files:
                            files.append(str(target))
            text = clean_text(_text_from_blocks(content))
            if text:
                messages.append(Message(kind, text, str(record.get("timestamp", ""))))
    if not messages:
        return None
    project = Path(cwd).name if cwd else _decode_project_dir(path.parent.name)
    first_user = next((m.text for m in messages if m.role == "user"), messages[0].text)
    return Session(
        id=f"claude-code:{session_id or path.stem}",
        source="claude-code",
        project=project or "unknown",
        title=title or first_user.strip().splitlines()[0][:100],
        started=messages[0].ts,
        ended=messages[-1].ts,
        branch=branch,
        path=str(path),
        messages=messages,
        files=files,
    )


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return None


def parse_claude_ai(path: Path) -> list[Session]:
    data = _load_json(path)
    sessions: list[Session] = []
    if not isinstance(data, list):
        return sessions
    for convo in data:
        if not isinstance(convo, dict) or "chat_messages" not in convo:
            continue
        messages = []
        for item in convo.get("chat_messages") or []:
            if not isinstance(item, dict):
                continue
            role = "user" if item.get("sender") == "human" else "assistant"
            text = clean_text(item.get("text") or _text_from_blocks(item.get("content")))
            if text:
                messages.append(Message(role, text, str(item.get("created_at", ""))))
        if not messages:
            continue
        project = convo.get("project")
        project_name = project.get("name") if isinstance(project, dict) else ""
        sessions.append(Session(
            id=f"claude-ai:{convo.get('uuid') or len(sessions)}",
            source="claude-ai",
            project=project_name or "claude.ai chats",
            title=str(convo.get("name") or messages[0].text[:100]),
            started=str(convo.get("created_at") or messages[0].ts),
            ended=messages[-1].ts,
            path=str(path),
            messages=messages,
        ))
    return sessions


def _chatgpt_linear(mapping: dict[str, Any], current: str | None) -> list[dict[str, Any]]:
    """Walk parent pointers from the current node back to the root, then reverse."""
    chain, seen = [], set()
    node_id = current
    while node_id and node_id in mapping and node_id not in seen:
        seen.add(node_id)
        node = mapping[node_id]
        chain.append(node)
        node_id = node.get("parent")
    return list(reversed(chain))


def parse_chatgpt(path: Path) -> list[Session]:
    data = _load_json(path)
    sessions: list[Session] = []
    if not isinstance(data, list):
        return sessions
    for convo in data:
        if not isinstance(convo, dict) or not isinstance(convo.get("mapping"), dict):
            continue
        current = convo.get("current_node")
        if not current:  # fall back to the last node in dict order
            current = next(reversed(convo["mapping"]), None)
        messages = []
        for node in _chatgpt_linear(convo["mapping"], current):
            msg = node.get("message")
            if not isinstance(msg, dict):
                continue
            role = (msg.get("author") or {}).get("role")
            if role not in ("user", "assistant"):
                continue
            parts = (msg.get("content") or {}).get("parts") or []
            text = clean_text("\n".join(part for part in parts if isinstance(part, str)))
            if text:
                messages.append(Message(role, text, _iso_from_epoch(msg.get("create_time"))))
        if not messages:
            continue
        sessions.append(Session(
            id=f"chatgpt:{convo.get('conversation_id') or convo.get('id') or len(sessions)}",
            source="chatgpt",
            project="chatgpt chats",
            title=str(convo.get("title") or messages[0].text[:100]),
            started=_iso_from_epoch(convo.get("create_time")) or messages[0].ts,
            ended=messages[-1].ts,
            path=str(path),
            messages=messages,
        ))
    return sessions


def parse_file(path: Path) -> list[Session]:
    """Dispatch on extension and, for JSON, on the shape of the content."""
    if path.suffix == ".jsonl":
        session = parse_claude_code(path)
        return [session] if session else []
    if path.suffix == ".json":
        data = _load_json(path)
        if isinstance(data, list) and data and isinstance(data[0], dict):
            if "chat_messages" in data[0]:
                return parse_claude_ai(path)
            if "mapping" in data[0]:
                return parse_chatgpt(path)
    return []


def iter_files(paths: Iterable[Path]) -> Iterator[Path]:
    for root in paths:
        root = Path(root).expanduser()
        if root.is_file():
            yield root
        elif root.is_dir():
            yield from sorted(p for p in root.rglob("*") if p.is_file() and p.suffix in (".json", ".jsonl"))


def default_claude_code_dir() -> Path:
    return Path.home() / ".claude" / "projects"


def discover(paths: Iterable[Path] | None = None) -> Iterator[Session]:
    targets = list(paths) if paths else [default_claude_code_dir()]
    for file in iter_files(targets):
        yield from parse_file(file)

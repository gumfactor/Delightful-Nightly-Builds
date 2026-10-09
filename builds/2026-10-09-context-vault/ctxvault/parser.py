"""Parse Claude Code JSONL session transcripts into a normalised structure."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

FILE_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit", "Read"}
MAX_TEXT = 20_000


@dataclass
class Message:
    idx: int
    role: str
    ts: str
    text: str


@dataclass
class ParsedSession:
    session_id: str
    project: str
    cwd: str = ""
    branch: str = ""
    started: str = ""
    ended: str = ""
    messages: list[Message] = field(default_factory=list)
    files: dict[str, int] = field(default_factory=dict)
    hint_title: str = ""


def project_name(cwd: str, dir_name: str) -> str:
    """Prefer the last path component of cwd; fall back to the encoded dir name."""
    if cwd:
        return Path(cwd.replace("\\", "/")).name or cwd
    return dir_name.strip("-").split("-")[-1] or dir_name


def _block_text(content) -> tuple[str, list[str]]:
    """Return (visible text, file paths touched) for a message content value."""
    if isinstance(content, str):
        return content, []
    texts: list[str] = []
    paths: list[str] = []
    if not isinstance(content, list):
        return "", paths
    for block in content:
        if not isinstance(block, dict):
            continue
        kind = block.get("type")
        if kind == "text" and isinstance(block.get("text"), str):
            texts.append(block["text"])
        elif kind == "tool_use":
            args = block.get("input") or {}
            if block.get("name") in FILE_TOOLS and isinstance(args, dict):
                path = args.get("file_path") or args.get("notebook_path")
                if isinstance(path, str) and path:
                    paths.append(path)
        # tool_result and thinking blocks are deliberately not indexed: noisy
    return "\n".join(texts), paths


def parse_session(path: Path) -> ParsedSession | None:
    """Parse one transcript file. Returns None when it holds no conversation."""
    session = ParsedSession(session_id=path.stem, project=project_name("", path.parent.name))
    try:
        handle = path.open("r", encoding="utf-8", errors="replace")
    except OSError:
        return None
    with handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            if record.get("type") == "summary" and isinstance(record.get("summary"), str):
                session.hint_title = record["summary"]
                continue
            if record.get("type") not in ("user", "assistant"):
                continue
            if record.get("isMeta") or record.get("isSidechain"):
                continue
            message = record.get("message")
            if not isinstance(message, dict):
                continue
            text, paths = _block_text(message.get("content"))
            for file_path in paths:
                session.files[file_path] = session.files.get(file_path, 0) + 1
            ts = record.get("timestamp") if isinstance(record.get("timestamp"), str) else ""
            if record.get("sessionId"):
                session.session_id = str(record["sessionId"])
            if record.get("cwd") and not session.cwd:
                session.cwd = str(record["cwd"])
            if record.get("gitBranch"):
                session.branch = str(record["gitBranch"])
            text = text.strip()
            if not text or text.startswith(("<command-name>", "<local-command", "Caveat:")):
                continue
            session.messages.append(
                Message(len(session.messages), record["type"], ts, text[:MAX_TEXT])
            )
            session.started = session.started or ts
            session.ended = ts or session.ended
    if not session.messages:
        return None
    session.project = project_name(session.cwd, path.parent.name)
    return session

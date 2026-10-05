"""Defensive parser for Claude Code JSONL transcripts."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

USAGE_FIELDS = ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")


@dataclass
class Turn:
    session_id: str
    project: str
    ts: datetime
    model: str
    input: int = 0
    output: int = 0
    cache_write: int = 0
    cache_read: int = 0
    sidechain: bool = False
    tools: list[tuple[str, str, str]] = field(default_factory=list)  # (tool_use_id, name, key)

    @property
    def context(self) -> int:
        return self.input + self.cache_write + self.cache_read


@dataclass
class Session:
    id: str
    project: str
    turns: list[Turn] = field(default_factory=list)
    results: dict[str, bool] = field(default_factory=dict)  # tool_use_id -> is_error


@dataclass
class ScanStats:
    files: int = 0
    lines: int = 0
    bad_lines: int = 0
    assistant_entries: int = 0
    turns: int = 0
    no_usage: int = 0
    unreadable_files: int = 0


def default_root() -> Path:
    base = os.environ.get("CLAUDE_CONFIG_DIR")
    return (Path(base) if base else Path.home() / ".claude") / "projects"


def find_transcripts(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(root.rglob("*.jsonl"))


def parse_ts(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _as_int(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else 0


def tool_key(name: str, tool_input: object) -> str:
    """Stable identity of a tool call, used to detect repeated work."""
    if isinstance(tool_input, dict):
        for field_name in ("file_path", "path", "command", "pattern", "url"):
            value = tool_input.get(field_name)
            if isinstance(value, str):
                return value[:300]
        return json.dumps(tool_input, sort_keys=True, default=str)[:300]
    return ""


def _project_name(cwd: object, path: Path) -> str:
    if isinstance(cwd, str) and cwd.strip("/\\"):
        return cwd.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
    return path.parent.name or "unknown"


def _blocks(message: dict) -> list[dict]:
    content = message.get("content")
    return [block for block in content if isinstance(block, dict)] if isinstance(content, list) else []


def parse_file(path: Path, stats: ScanStats) -> Iterator[tuple[str, Turn | dict[str, bool]]]:
    """Yield ('turn', Turn) per deduplicated assistant message and ('results', {id: is_error})."""
    stats.files += 1
    pending: dict[str, Turn] = {}
    order: list[str] = []
    try:
        handle = path.open(encoding="utf-8", errors="replace")
    except OSError:
        stats.unreadable_files += 1
        return
    with handle:
        for line_number, raw in enumerate(handle):
            raw = raw.strip()
            if not raw:
                continue
            stats.lines += 1
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                stats.bad_lines += 1
                continue
            if not isinstance(entry, dict):
                stats.bad_lines += 1
                continue
            message = entry.get("message")
            message = message if isinstance(message, dict) else {}
            kind = entry.get("type")
            if kind == "user":
                results = {
                    block["tool_use_id"]: bool(block.get("is_error"))
                    for block in _blocks(message)
                    if block.get("type") == "tool_result" and isinstance(block.get("tool_use_id"), str)
                }
                if results:
                    yield "results", results
                continue
            if kind != "assistant":
                continue
            stats.assistant_entries += 1
            usage = message.get("usage")
            ts = parse_ts(entry.get("timestamp"))
            if not isinstance(usage, dict) or ts is None:
                stats.no_usage += 1
                continue
            key = str(message.get("id") or entry.get("requestId") or f"{path}:{line_number}")
            turn = pending.get(key)
            if turn is None:
                turn = Turn(
                    session_id=str(entry.get("sessionId") or path.stem),
                    project=_project_name(entry.get("cwd"), path),
                    ts=ts,
                    model=str(message.get("model") or "unknown"),
                    sidechain=bool(entry.get("isSidechain")),
                )
                pending[key] = turn
                order.append(key)
            turn.input = max(turn.input, _as_int(usage.get("input_tokens")))
            turn.output = max(turn.output, _as_int(usage.get("output_tokens")))
            turn.cache_write = max(turn.cache_write, _as_int(usage.get("cache_creation_input_tokens")))
            turn.cache_read = max(turn.cache_read, _as_int(usage.get("cache_read_input_tokens")))
            known = {tool_id for tool_id, _, _ in turn.tools}
            for block in _blocks(message):
                tool_id = block.get("id")
                if block.get("type") == "tool_use" and isinstance(tool_id, str) and tool_id not in known:
                    name = str(block.get("name") or "unknown")
                    turn.tools.append((tool_id, name, tool_key(name, block.get("input"))))
                    known.add(tool_id)
    for key in order:
        stats.turns += 1
        yield "turn", pending[key]


def load_sessions(root: Path) -> tuple[list[Session], ScanStats]:
    stats = ScanStats()
    sessions: dict[str, Session] = {}
    results: dict[str, bool] = {}  # tool_use ids are globally unique, so one pool is safe
    for path in find_transcripts(root):
        for kind, payload in parse_file(path, stats):
            if kind == "turn":
                turn = payload  # type: ignore[assignment]
                session = sessions.setdefault(turn.session_id, Session(turn.session_id, turn.project))
                session.turns.append(turn)
            else:
                results.update(payload)  # type: ignore[arg-type]
    for session in sessions.values():
        session.turns.sort(key=lambda turn: turn.ts)
        ids = {tool_id for turn in session.turns for tool_id, _, _ in turn.tools}
        session.results = {tool_id: results[tool_id] for tool_id in ids if tool_id in results}
    return sorted(sessions.values(), key=lambda s: s.turns[0].ts), stats

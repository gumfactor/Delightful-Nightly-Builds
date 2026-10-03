"""Tolerant parser for Claude Code JSONL session transcripts."""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from .pricing import PRICE_KEYS, estimate_cost

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
MAX_TEXT = 4000


@dataclass
class Session:
    id: str
    project: str = ""
    branch: str = ""
    start: str = ""
    end: str = ""
    active_seconds: int = 0
    prompts: list[tuple[str, str]] = field(default_factory=list)  # (timestamp, text)
    assistant_msgs: int = 0
    sidechain_msgs: int = 0
    tool_errors: int = 0
    usage_by_model: dict[str, dict[str, int]] = field(default_factory=dict)
    tools: Counter = field(default_factory=Counter)
    files: Counter = field(default_factory=Counter)
    last_assistant: str = ""
    title: str = ""
    source: str = ""
    cost_usd: float = 0.0
    unpriced: bool = False

    def total(self, key: str) -> int:
        return sum(usage.get(key, 0) for usage in self.usage_by_model.values())


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def iter_records(path: Path) -> Iterator[dict[str, Any]]:
    """Yield JSON objects from a JSONL file, skipping blank or malformed lines."""
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                yield record


def _blocks(content: Any) -> list[dict[str, Any]]:
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if isinstance(content, list):
        return [block for block in content if isinstance(block, dict)]
    return []


def _text_of(blocks: list[dict[str, Any]]) -> str:
    parts = [b.get("text", "") for b in blocks if b.get("type") == "text" and isinstance(b.get("text"), str)]
    return "\n".join(part for part in parts if part).strip()


def _is_noise_prompt(text: str) -> bool:
    """Slash-command plumbing and injected caveats are not real prompts."""
    stripped = text.lstrip()
    return (
        not stripped
        or stripped.startswith("<local-command")
        or stripped.startswith("<command-name>")
        or stripped.startswith("Caveat:")
        or stripped.startswith("[Request interrupted")
    )


def _int(value: Any) -> int:
    return value if isinstance(value, int) and value > 0 else 0


def parse_session_file(path: Path, idle_gap_seconds: int = 300) -> Session | None:
    """Parse one transcript. Returns None if it contains no user or assistant turns."""
    session = Session(id=path.stem, source=str(path))
    last_usage: dict[str, tuple[str, dict[str, int]]] = {}  # message id -> (model, usage)
    stamps: list[datetime] = []
    seen_turns = 0

    for record in iter_records(path):
        kind = record.get("type")
        if kind == "summary" and isinstance(record.get("summary"), str):
            session.title = record["summary"]
            continue
        if kind not in ("user", "assistant"):
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        seen_turns += 1

        session.id = str(record.get("sessionId") or session.id)
        session.project = session.project or str(record.get("cwd") or "")
        session.branch = session.branch or str(record.get("gitBranch") or "")
        raw_ts = record.get("timestamp")
        moment = parse_timestamp(raw_ts)
        if moment is not None:
            stamps.append(moment)
        blocks = _blocks(message.get("content"))
        sidechain = bool(record.get("isSidechain"))

        if kind == "user":
            for block in blocks:
                if block.get("type") == "tool_result" and block.get("is_error"):
                    session.tool_errors += 1
            if sidechain or record.get("isMeta") or any(b.get("type") == "tool_result" for b in blocks):
                if sidechain:
                    session.sidechain_msgs += 1
                continue
            text = _text_of(blocks)
            if not _is_noise_prompt(text):
                session.prompts.append((str(raw_ts or ""), text[:MAX_TEXT]))
            continue

        # assistant
        if sidechain:
            session.sidechain_msgs += 1
        else:
            session.assistant_msgs += 1
        msg_id = str(message.get("id") or f"anon-{seen_turns}")
        usage = message.get("usage")
        if isinstance(usage, dict):
            normalized = {
                "input": _int(usage.get("input_tokens")),
                "output": _int(usage.get("output_tokens")),
                "cache_write": _int(usage.get("cache_creation_input_tokens")),
                "cache_read": _int(usage.get("cache_read_input_tokens")),
            }
            # Streamed responses repeat the same message id; the last record is complete.
            last_usage[msg_id] = (str(message.get("model") or "unknown"), normalized)
        for block in blocks:
            if block.get("type") != "tool_use":
                continue
            name = str(block.get("name") or "unknown")
            session.tools[name] += 1
            tool_input = block.get("input")
            if name in EDIT_TOOLS and isinstance(tool_input, dict):
                target = tool_input.get("file_path") or tool_input.get("notebook_path")
                if isinstance(target, str) and target:
                    session.files[target] += 1
        if not sidechain:
            text = _text_of(blocks)
            if text:
                session.last_assistant = text[:MAX_TEXT]

    if seen_turns == 0:
        return None

    for model, usage in last_usage.values():
        bucket = session.usage_by_model.setdefault(model, {key: 0 for key in PRICE_KEYS})
        for key in PRICE_KEYS:
            bucket[key] += usage[key]

    if stamps:
        stamps.sort()
        session.start = stamps[0].isoformat()
        session.end = stamps[-1].isoformat()
        active = 0.0
        for earlier, later in zip(stamps, stamps[1:]):
            gap = (later - earlier).total_seconds()
            if gap <= idle_gap_seconds:
                active += gap
        session.active_seconds = int(active)
    return session


def finalize_cost(session: Session, prices: dict[str, dict[str, float]]) -> Session:
    session.cost_usd, session.unpriced = estimate_cost(session.usage_by_model, prices)
    return session


def project_label(cwd: str, fallback: str = "(unknown)") -> str:
    """Short, readable project name from a working directory path."""
    cleaned = (cwd or "").replace("\\", "/").rstrip("/")
    return cleaned.rsplit("/", 1)[-1] or fallback

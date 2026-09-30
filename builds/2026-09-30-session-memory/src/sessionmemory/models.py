from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Message:
    role: str  # "user" or "assistant"
    text: str
    ts: str = ""


@dataclass
class Session:
    id: str  # "<source>:<native id>"
    source: str  # "claude-code" | "claude-ai" | "chatgpt"
    project: str
    title: str
    started: str = ""
    ended: str = ""
    branch: str = ""
    path: str = ""
    messages: list[Message] = field(default_factory=list)
    files: list[str] = field(default_factory=list)  # files edited (Claude Code)

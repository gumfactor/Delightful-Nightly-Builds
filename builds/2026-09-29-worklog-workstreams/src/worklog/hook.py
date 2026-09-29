"""Automatic capture from a Claude Code session (Stop / SessionEnd hook).

Only metadata is persisted: the first prompt's first line (as the objective), files the agent edited,
test-runner commands with pass/fail, and commits made during the session. The transcript itself is
read, never stored, and its content is treated as untrusted data.
"""
import json
import re
from pathlib import Path
from typing import Any, Optional

from .checkpoint import capture
from .ledger import Ledger, utc_now
from .project import Project, WorklogError, git

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
TEST_COMMAND = re.compile(r"\b(pytest|npm (?:run )?test|npx (?:playwright|vitest|jest)|vitest|jest|cargo test|go test)\b")
MAX_OBJECTIVE = 160


def _text_of(content: Any) -> Optional[str]:
    """User-authored text of a message, or None when it is a tool result / injected wrapper."""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
        text = "\n".join(parts)
    else:
        return None
    text = text.strip()
    if not text or text.startswith("<"):
        return None
    return text


def parse_transcript(path: Path, root: Path) -> dict:
    """Extract objective, edited files, test runs and time bounds from a JSONL transcript."""
    objective, first_ts, last_ts = None, None, None
    files: list[str] = []
    tests: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        raise WorklogError(f"cannot read transcript: {exc}") from exc
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict) or entry.get("isSidechain"):
            continue
        stamp = entry.get("timestamp")
        if isinstance(stamp, str):
            first_ts, last_ts = first_ts or stamp, stamp
        message = entry.get("message") if isinstance(entry.get("message"), dict) else {}
        content = message.get("content")
        if entry.get("type") == "user" and objective is None:
            text = _text_of(content)
            if text:
                objective = text.splitlines()[0][:MAX_OBJECTIVE]
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use":
                tool_input = block.get("input") if isinstance(block.get("input"), dict) else {}
                if block.get("name") in EDIT_TOOLS:
                    target = tool_input.get("file_path") or tool_input.get("notebook_path")
                    rel = _relative(target, root)
                    if rel and rel not in files:
                        files.append(rel)
                elif block.get("name") == "Bash" and TEST_COMMAND.search(str(tool_input.get("command", ""))):
                    tests[block.get("id", "")] = str(tool_input["command"])[:200]
            elif block.get("type") == "tool_result" and block.get("tool_use_id") in tests:
                tests[block["tool_use_id"]] = (tests[block["tool_use_id"]], "failed" if block.get("is_error") else "passed")
    validation = [{"command": item[0], "result": item[1]} for item in tests.values() if isinstance(item, tuple)]
    return {"objective": objective, "files": files, "validation": validation, "first_ts": first_ts,
            "last_ts": last_ts}


def _relative(target: Any, root: Path) -> Optional[str]:
    if not isinstance(target, str):
        return None
    try:
        return str(Path(target).resolve().relative_to(root.resolve()))
    except (ValueError, OSError):
        return None


def build_checkpoint(project: Project, payload: dict) -> dict:
    transcript = Path(str(payload.get("transcript_path", "")))
    if transcript.suffix != ".jsonl" or not transcript.is_file():
        raise WorklogError("hook payload has no readable .jsonl transcript_path")
    parsed = parse_transcript(transcript, project.root)
    started = parsed["first_ts"] or utc_now()
    commits = git(project.root, "log", "--format=%H", "--max-count=50", f"--since={started}", check=False).split()
    return {
        "provider": "claude-code",
        "session_id": payload.get("session_id") or transcript.stem,
        "timestamp": parsed["last_ts"] or utc_now(),
        "objective": parsed["objective"] or "(claude-code session; no prompt found)",
        "files": parsed["files"],
        "validation": parsed["validation"],
        "source_refs": [{"commit": sha} for sha in commits],
        "status": "in_progress",
        "auto": True,
    }


def run_hook(project: Project, ledger: Ledger, stdin_text: str) -> dict:
    """Entry point for `worklog hook`. Raises WorklogError on unusable payloads."""
    try:
        payload = json.loads(stdin_text)
    except json.JSONDecodeError as exc:
        raise WorklogError(f"hook stdin is not JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise WorklogError("hook stdin must be a JSON object")
    return capture(project, ledger, build_checkpoint(project, payload))

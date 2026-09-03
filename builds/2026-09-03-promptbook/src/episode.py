"""Derive deterministic "what happened next" signals for a prompt turn.

An episode is the slice of a session's raw lines between one prompt turn and the next
(or end of file). This module walks that slice, matches each ``tool_use`` block to its
corresponding ``tool_result`` by ``id``/``tool_use_id``, and reduces the whole episode to a
small set of booleans/counts that ``score.py`` turns into an effectiveness score.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.extract import RawLine

EDIT_TOOL_NAMES = {"Edit", "Write", "NotebookEdit"}

TEST_COMMAND_RE = re.compile(
    r"\b("
    r"pytest|py\.test|python\s+-m\s+pytest|"
    r"npm\s+(run\s+)?test|yarn\s+test|pnpm\s+test|"
    r"jest|vitest|playwright\s+test|npx\s+playwright\s+test|"
    r"go\s+test|cargo\s+test|mvn\s+test|gradle\s+test"
    r")\b",
    re.IGNORECASE,
)
GIT_COMMIT_RE = re.compile(r"\bgit\s+commit\b", re.IGNORECASE)
TEST_FAIL_RE = re.compile(r"(\d+)\s+failed", re.IGNORECASE)
TEST_PASS_RE = re.compile(r"(\d+)\s+passed|\ball tests passed\b|^ok$", re.IGNORECASE | re.MULTILINE)
ERROR_TEXT_RE = re.compile(r"\bTraceback \(most recent call last\)|^Error:", re.IGNORECASE | re.MULTILINE)


@dataclass
class Episode:
    tools_used: set[str] = field(default_factory=set)
    files_edited: set[str] = field(default_factory=set)
    bash_commands: list[str] = field(default_factory=list)
    test_run: bool = False
    test_passed: bool | None = None
    git_commit: bool = False
    had_error: bool = False
    unresolved_error: bool = False


def _tool_result_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return ""


def build_episode(lines: list[RawLine], start_index: int, end_index: int) -> Episode:
    """Build an Episode from raw lines with ``start_index <= line.index < end_index``."""
    episode = Episode()

    # tool_use_id -> (tool_name, input) for matching later tool_result blocks
    pending_tool_use: dict[str, tuple[str, dict]] = {}
    last_error_line_index: int | None = None
    success_after_error = False

    for raw_line in lines:
        if not (start_index <= raw_line.index < end_index):
            continue
        obj = raw_line.obj
        line_type = obj.get("type")
        message = obj.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue

        if line_type == "assistant":
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                name = block.get("name")
                tool_input = block.get("input") or {}
                tool_id = block.get("id")
                if not isinstance(name, str):
                    continue
                episode.tools_used.add(name)
                if tool_id:
                    pending_tool_use[str(tool_id)] = (name, tool_input if isinstance(tool_input, dict) else {})

                if name in EDIT_TOOL_NAMES:
                    file_path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
                    if isinstance(file_path, str):
                        episode.files_edited.add(file_path)

                if name == "Bash":
                    command = tool_input.get("command") if isinstance(tool_input, dict) else None
                    if isinstance(command, str):
                        episode.bash_commands.append(command)
                        if TEST_COMMAND_RE.search(command):
                            episode.test_run = True
                        if GIT_COMMIT_RE.search(command):
                            episode.git_commit = True
                            if last_error_line_index is not None:
                                success_after_error = True

        elif line_type == "user":
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    continue
                tool_use_id = block.get("tool_use_id")
                tool_name = None
                if isinstance(tool_use_id, str) and tool_use_id in pending_tool_use:
                    tool_name = pending_tool_use[tool_use_id][0]

                is_error = bool(block.get("is_error"))
                text = _tool_result_text(block.get("content"))

                error_here = is_error or bool(ERROR_TEXT_RE.search(text))
                if error_here:
                    episode.had_error = True
                    last_error_line_index = raw_line.index
                    success_after_error = False
                    continue

                if episode.test_run and (tool_name == "Bash"):
                    fail_match = TEST_FAIL_RE.search(text)
                    pass_match = TEST_PASS_RE.search(text)
                    if fail_match and int(fail_match.group(1)) > 0:
                        episode.test_passed = False
                    elif pass_match and episode.test_passed is not True:
                        episode.test_passed = True
                        if last_error_line_index is not None:
                            success_after_error = True

                if tool_name in EDIT_TOOL_NAMES and last_error_line_index is not None:
                    success_after_error = True

    episode.unresolved_error = episode.had_error and not success_after_error
    return episode


def episode_bounds(prompt_line_indices: list[int], target_line_index: int, total_lines: int) -> tuple[int, int]:
    """Return (start, end) line-index bounds for the episode following a given prompt."""
    later = [i for i in prompt_line_indices if i > target_line_index]
    end = min(later) if later else total_lines
    return target_line_index, end

"""Ties extraction, episode analysis, classification, and scoring together for `ingest`."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.classify import classify
from src.episode import build_episode, episode_bounds
from src.extract import extract_prompts, iter_session_files, read_jsonl_lines
from src.score import score_episode
from src.storage import StoredPrompt, get_last_line_count, set_last_line_count, upsert_prompt


class IngestResult:
    def __init__(self) -> None:
        self.files_scanned = 0
        self.files_with_new_lines = 0
        self.prompts_seen = 0
        self.prompts_inserted = 0

    def as_dict(self) -> dict:
        return {
            "files_scanned": self.files_scanned,
            "files_with_new_lines": self.files_with_new_lines,
            "prompts_seen": self.prompts_seen,
            "prompts_inserted": self.prompts_inserted,
        }


def ingest_directory(conn: sqlite3.Connection, claude_dir: Path) -> IngestResult:
    result = IngestResult()
    for session_file in iter_session_files(claude_dir):
        result.files_scanned += 1
        file_key = str(session_file)
        last_line_count = get_last_line_count(conn, file_key)

        lines = read_jsonl_lines(session_file)
        total_line_count = len(lines)
        if total_line_count <= last_line_count:
            continue
        result.files_with_new_lines += 1

        all_prompts = extract_prompts(lines)
        new_prompts = [p for p in all_prompts if p.line_index >= last_line_count]
        prompt_line_indices = [p.line_index for p in all_prompts]

        for prompt in new_prompts:
            result.prompts_seen += 1
            start, end = episode_bounds(prompt_line_indices, prompt.line_index, total_line_count)
            episode = build_episode(lines, start, end)
            task_type = classify(prompt.prompt_text)
            score = score_episode(episode)

            stored = StoredPrompt(
                prompt_uuid=prompt.prompt_uuid,
                session_id=prompt.session_id,
                project=prompt.project,
                git_branch=prompt.git_branch,
                entrypoint=prompt.entrypoint,
                timestamp=prompt.timestamp,
                prompt_text=prompt.prompt_text,
                task_type=task_type,
                score=score,
                tools_used=sorted(episode.tools_used),
                files_edited=len(episode.files_edited),
                test_run=episode.test_run,
                test_passed=episode.test_passed,
                git_commit=episode.git_commit,
                had_error=episode.had_error,
            )
            if upsert_prompt(conn, stored):
                result.prompts_inserted += 1

        set_last_line_count(
            conn, file_key, total_line_count, datetime.now(timezone.utc).isoformat()
        )

    conn.commit()
    return result

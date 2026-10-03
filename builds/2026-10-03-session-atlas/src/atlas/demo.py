"""Generate a synthetic Claude Code log tree so the explorer can be tried without real logs."""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECTS = {
    "/work/canada-list-pipeline": [
        "Classify these 40 products as Canadian-made or not and flag the uncertain ones",
        "The ingestion script fails on rows with unicode apostrophes, fix the CSV reader",
        "Add a dedupe step for businesses sharing a phone number",
        "Write tests for the province normaliser",
    ],
    "/work/neuro-lab-stats": [
        "Fit a Bayesian mixed model for the empathy task reaction times with brms",
        "Convert this SPSS syntax to R and keep the variable labels",
        "Plot posterior distributions for the stress condition effect",
    ],
    "/work/kwyeter-app": [
        "Add a venue noise-level card to the Flutter detail screen",
        "Firebase rules reject anonymous reads, what is wrong in this rule set",
        "Refactor the decibel calibration service and add unit tests",
    ],
    "/work/stress-book": [
        "Tighten chapter 3 on the HPA axis, plain language, no AI-sounding prose",
        "Create a table of coping strategies with evidence strength",
    ],
}
FILE_NAMES = ["main.py", "README.md", "lib/service.dart", "analysis.R", "src/ingest.py", "tests/test_core.py"]


def _line(**fields: object) -> str:
    return json.dumps(fields)


def generate_demo_logs(root: str | Path, days: int = 45, seed: int = 7) -> int:
    """Write synthetic transcripts under root. Returns the number of sessions created."""
    rng = random.Random(seed)
    base = Path(root)
    now = datetime(2026, 10, 3, 18, 0, tzinfo=timezone.utc)
    count = 0
    for offset in range(days):
        day = now - timedelta(days=offset)
        if day.weekday() >= 5 and rng.random() < 0.6:
            continue
        for _ in range(rng.choice([1, 1, 2, 3])):
            cwd, prompts = rng.choice(list(PROJECTS.items()))
            folder = base / cwd.replace("/", "-")
            folder.mkdir(parents=True, exist_ok=True)
            session_id = f"demo-{count:04d}"
            moment = day.replace(hour=rng.choice([9, 10, 13, 14, 15, 20]), minute=rng.randint(0, 50))
            model = rng.choice(["claude-opus-4-1", "claude-sonnet-4-5", "claude-sonnet-4-5", "claude-haiku-4-5"])
            lines = []
            chosen = rng.sample(prompts, k=rng.randint(1, len(prompts)))
            edit_target = f"{cwd}/{rng.choice(FILE_NAMES)}"
            for turn, prompt in enumerate(chosen):
                moment += timedelta(seconds=rng.randint(20, 240))
                lines.append(_line(type="user", sessionId=session_id, cwd=cwd, gitBranch="main",
                                   timestamp=moment.isoformat(), message={"role": "user", "content": prompt}))
                for step in range(rng.randint(2, 9)):
                    moment += timedelta(seconds=rng.randint(5, 90))
                    tool = rng.choice(["Read", "Edit", "Edit", "Bash", "Grep", "Write"])
                    block = {"type": "tool_use", "id": f"t{turn}{step}", "name": tool,
                             "input": {"file_path": edit_target} if tool in ("Edit", "Write") else {"command": "ls"}}
                    msg_id = f"m{count}-{turn}-{step}"
                    usage = {"input_tokens": rng.randint(50, 900), "output_tokens": rng.randint(100, 2500),
                             "cache_creation_input_tokens": rng.randint(0, 4000),
                             "cache_read_input_tokens": rng.randint(5000, 60000)}
                    lines.append(_line(type="assistant", sessionId=session_id, cwd=cwd, timestamp=moment.isoformat(),
                                       message={"id": msg_id, "role": "assistant", "model": model, "usage": usage,
                                                "content": [block]}))
                    moment += timedelta(seconds=rng.randint(1, 20))
                    lines.append(_line(type="user", sessionId=session_id, cwd=cwd, timestamp=moment.isoformat(),
                                       message={"role": "user", "content": [
                                           {"type": "tool_result", "tool_use_id": block["id"],
                                            "is_error": rng.random() < 0.06, "content": "ok"}]}))
                moment += timedelta(seconds=rng.randint(10, 60))
                lines.append(_line(type="assistant", sessionId=session_id, cwd=cwd, timestamp=moment.isoformat(),
                                   message={"id": f"m{count}-{turn}-end", "role": "assistant", "model": model,
                                            "usage": {"input_tokens": 120, "output_tokens": 400},
                                            "content": [{"type": "text", "text": f"Done with: {prompt[:60]}. "
                                                         "Next I would check the edge cases."}]}))
            (folder / f"{session_id}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
            count += 1
    return count

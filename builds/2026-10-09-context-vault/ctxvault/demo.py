"""Generate a small synthetic Claude Code transcript tree for trying the tool."""
from __future__ import annotations

import json
from pathlib import Path

DEMO = {
    "canada-list": [
        ("2026-09-30T14:02:00Z", "fix/dedupe-ingest", [
            "The ingestion pipeline is creating duplicate business entries when the same website appears with and without www. Can you fix the dedupe step?",
            "Normalising hostnames before hashing should fix it. I'll edit dedupe.py to strip www and trailing slashes.",
            "Decision: keep the existing SHA1 key but compute it on the normalised host.",
            "Tests pass. Still unresolved: franchise locations that share one domain are now merged.",
        ], ["/work/canada-list/pipeline/dedupe.py", "/work/canada-list/tests/test_dedupe.py"]),
        ("2026-10-05T16:30:00Z", "main", [
            "Franchise locations sharing a domain are being merged. How should we model that?",
            "Add a location_key from postal code and use (host, location_key) as the identity.",
            "Let's add a postal-code regex for Canadian codes and write the migration next session.",
        ], ["/work/canada-list/pipeline/dedupe.py", "/work/canada-list/pipeline/models.py"]),
    ],
    "kwyeter": [
        ("2026-10-02T10:15:00Z", "main", [
            "Calibrating the decibel meter: microphone gain differs between Android devices. What approach would you suggest?",
            "Use a per-device calibration offset stored in Firebase, measured against a reference tone.",
            "We decided to ship A-weighting first and defer C-weighting.",
        ], ["/work/kwyeter/lib/audio/meter.dart"]),
    ],
}


def write_demo(root: Path) -> int:
    count = 0
    for project, sessions in DEMO.items():
        folder = root / f"-work-{project}"
        folder.mkdir(parents=True, exist_ok=True)
        for n, (ts, branch, turns, files) in enumerate(sessions):
            session_id = f"demo-{project}-{n}"
            lines = []
            for i, text in enumerate(turns):
                role = "user" if i % 2 == 0 else "assistant"
                content = [{"type": "text", "text": text}]
                if role == "assistant" and i // 2 < len(files):
                    content.append({"type": "tool_use", "name": "Edit",
                                    "input": {"file_path": files[i // 2]}})
                lines.append({"type": role, "sessionId": session_id, "cwd": f"/work/{project}",
                              "gitBranch": branch, "timestamp": ts[:-4] + f"{i:02d}Z",
                              "message": {"role": role, "content": content if role == "assistant" else text}})
            (folder / f"{session_id}.jsonl").write_text(
                "\n".join(json.dumps(r) for r in lines) + "\n", encoding="utf-8")
            count += 1
    return count

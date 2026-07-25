"""Local git log/show fallback — no GITHUB_TOKEN required.

Runs against a repo already on disk. Uses list-form subprocess calls only
(never shell=True), and validates repo_path/sha before use, so no
user-controlled string can inject extra git flags or reach a shell.
"""

import re
import subprocess
from pathlib import Path

_SHA_RE = re.compile(r"^[0-9a-fA-F]{4,40}$")
_RECORD_SEP = "\x1e"
_FIELD_SEP = "\x1f"


class LocalGitError(Exception):
    pass


def _validate_repo_path(repo_path):
    path = Path(repo_path)
    if not path.is_dir():
        raise LocalGitError(f"Not a directory: {repo_path}")
    if not (path / ".git").exists():
        raise LocalGitError(f"Not a git repository (no .git found): {repo_path}")
    return str(path)


def _validate_sha(sha):
    if not _SHA_RE.match(sha):
        raise LocalGitError(f"Refusing to use unsafe commit reference: {sha!r}")
    return sha


def get_local_fix_commits(repo_path, since=None, limit=500):
    repo_path = _validate_repo_path(repo_path)
    fmt = f"%H{_FIELD_SEP}%aI{_FIELD_SEP}%s{_RECORD_SEP}"
    cmd = [
        "git",
        "-C",
        repo_path,
        "log",
        f"--max-count={int(limit)}",
        f"--pretty=format:{fmt}",
    ]
    if since:
        cmd.append(f"--since={since}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise LocalGitError(f"git log failed: {result.stderr.strip()}")

    commits = []
    for entry in result.stdout.split(_RECORD_SEP):
        entry = entry.strip()
        if not entry:
            continue
        parts = entry.split(_FIELD_SEP)
        if len(parts) != 3:
            continue
        sha, date, message = parts
        commits.append({"sha": sha, "date": date, "message": message})
    return commits


def get_local_commit_diff(repo_path, sha, max_chars=4000):
    repo_path = _validate_repo_path(repo_path)
    sha = _validate_sha(sha)
    cmd = ["git", "-C", repo_path, "show", "--no-color", "--pretty=format:", sha]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise LocalGitError(f"git show failed: {result.stderr.strip()}")
    return result.stdout[:max_chars]

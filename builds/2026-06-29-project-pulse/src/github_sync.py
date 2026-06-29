import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import List, Optional

API_BASE = "https://api.github.com"


def _make_request(url: str, token: str) -> Optional[object]:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "project-pulse/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 404, 409, 422):
            return None
        raise
    except urllib.error.URLError:
        return None


def parse_commit(raw: dict) -> dict:
    commit_info = raw.get("commit") or {}
    author_info = commit_info.get("author") or {}
    message_full = commit_info.get("message") or ""
    first_line = message_full.split("\n")[0][:200]
    sha_full = raw.get("sha") or ""
    return {
        "sha": sha_full[:8],
        "message": first_line,
        "author": author_info.get("name") or "",
        "committed_at": author_info.get("date") or "",
    }


def fetch_repo_commits(
    owner_repo: str, token: str, since_days: int = 30
) -> List[dict]:
    since_dt = datetime.now(timezone.utc) - timedelta(days=since_days)
    # Use strftime to produce a clean UTC timestamp without the +00:00 suffix,
    # which contains a '+' that must be URL-encoded in query strings.
    since = since_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    page = 1
    commits: List[dict] = []
    while True:
        params = urllib.parse.urlencode({"per_page": 100, "page": page, "since": since})
        url = f"{API_BASE}/repos/{owner_repo}/commits?{params}"
        data = _make_request(url, token)
        if not data or not isinstance(data, list):
            break
        for raw in data:
            commits.append(parse_commit(raw))
        if len(data) < 100:
            break
        page += 1
    return commits


def sync_project(db_path: str, project: dict, token: str) -> int:
    from database import log_activity

    repos = project.get("github_repos") or []
    count = 0
    for repo in repos:
        try:
            commits = fetch_repo_commits(repo, token)
        except Exception:
            continue
        for commit in commits:
            title = f"[{repo}] {commit['message']}" if commit["message"] else f"[{repo}] (no message)"
            result = log_activity(
                db_path=db_path,
                project_id=project["id"],
                source="github",
                event_type="commit",
                title=title,
                detail=f"sha:{commit['sha']} author:{commit['author']}",
                occurred_at=commit["committed_at"] or None,
            )
            if result is not None:
                count += 1
    return count

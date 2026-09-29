"""GitHub collector (REST). Optional: any failure degrades to Git-only operation."""
import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable, Optional

from .ledger import make_event
from .project import Project, github_slug, refs_from_branch, refs_from_text

API = "https://api.github.com"
Fetch = Callable[[str], Any]


class GitHubUnavailable(Exception):
    pass


def make_fetch(token: Optional[str]) -> Fetch:
    """Return a GET-JSON function. The token only ever goes in the Authorization header."""
    def fetch(url: str) -> Any:
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "worklog",
                   "X-GitHub-Api-Version": "2022-11-28"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise GitHubUnavailable(f"GitHub returned HTTP {exc.code} for {url.split('?')[0]}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise GitHubUnavailable(f"GitHub request failed: {exc}") from exc
    return fetch


def _pages(fetch: Fetch, url: str, limit: int = 3) -> list[dict]:
    items: list[dict] = []
    sep = "&" if "?" in url else "?"
    for page in range(1, limit + 1):
        chunk = fetch(f"{url}{sep}per_page=100&page={page}")
        if not isinstance(chunk, list):
            raise GitHubUnavailable("unexpected GitHub response shape")
        items.extend(chunk)
        if len(chunk) < 100:
            break
    return items


def _actor(user: Optional[dict]) -> tuple[str, str]:
    if not user:
        return "human", "unknown"
    login = user.get("login", "unknown")
    return ("agent" if user.get("type") == "Bot" or login.endswith("[bot]") else "human"), login


def collect(project: Project, fetch: Optional[Fetch] = None, since: Optional[str] = None) -> list[dict]:
    """Issues, PRs (open/merge/close), reviews and check runs. Raises GitHubUnavailable on failure."""
    slug = project.config.github_repo or github_slug(project.remote)
    if not slug:
        raise GitHubUnavailable("remote is not a GitHub repository")
    if fetch is None:
        fetch = make_fetch(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"))
    base = f"{API}/repos/{slug}"
    pid = project.project_id
    events: list[dict] = []
    since_q = f"&since={since}" if since else ""

    for item in _pages(fetch, f"{base}/issues?state=all{since_q}"):
        if "pull_request" in item:
            continue  # PRs are handled below with richer data
        number, title = item["number"], item.get("title", "")
        kind, name = _actor(item.get("user"))
        common = dict(project_id=pid, provider="github", etype="issue", actor_kind=kind, actor_name=name,
                      url=item.get("html_url"), keys=[f"gh:{number}", *refs_from_text(item.get("body") or "")])
        events.append(make_event(ts=item["created_at"], ref=f"issue:{number}:opened",
                                 summary=f"Issue #{number} opened: {title}", status="open",
                                 metadata={"number": number, "title": title,
                                           "labels": [lb["name"] for lb in item.get("labels", [])]}, **common))
        if item.get("closed_at"):
            events.append(make_event(ts=item["closed_at"], ref=f"issue:{number}:closed",
                                     summary=f"Issue #{number} closed: {title}", status="completed",
                                     metadata={"number": number, "title": title}, **common))

    head_shas: dict[int, str] = {}
    for pull in _pages(fetch, f"{base}/pulls?state=all"):
        number, title = pull["number"], pull.get("title", "")
        head_ref, head_sha = pull["head"]["ref"], pull["head"]["sha"]
        head_shas[number] = head_sha
        kind, name = _actor(pull.get("user"))
        keys = [f"gh:{number}", f"sha:{head_sha}", f"branch:{head_ref}", *refs_from_branch(head_ref),
                *refs_from_text(pull.get("body") or ""), *refs_from_text(title)]
        common = dict(project_id=pid, provider="github", etype="pr", actor_kind=kind, actor_name=name,
                      url=pull.get("html_url"), keys=keys)
        meta = {"number": number, "title": title, "branch": head_ref, "head_sha": head_sha,
                "base": pull["base"]["ref"], "draft": bool(pull.get("draft"))}
        events.append(make_event(ts=pull["created_at"], ref=f"pr:{number}:opened",
                                 summary=f"PR #{number} opened: {title}", status="open", metadata=meta, **common))
        if pull.get("merged_at"):
            events.append(make_event(ts=pull["merged_at"], ref=f"pr:{number}:merged",
                                     summary=f"PR #{number} merged: {title}", status="completed",
                                     metadata={**meta, "merge_commit": pull.get("merge_commit_sha")}, **common))
        elif pull.get("closed_at"):
            events.append(make_event(ts=pull["closed_at"], ref=f"pr:{number}:closed",
                                     summary=f"PR #{number} closed unmerged: {title}", status="abandoned",
                                     metadata=meta, **common))
        try:
            reviews = fetch(f"{base}/pulls/{number}/reviews?per_page=100")
        except GitHubUnavailable:
            reviews = []
        for review in reviews if isinstance(reviews, list) else []:
            if not review.get("submitted_at"):
                continue
            rkind, rname = _actor(review.get("user"))
            state = review.get("state", "COMMENTED")
            events.append(make_event(
                ts=review["submitted_at"], project_id=pid, provider="github", etype="review",
                ref=f"review:{review['id']}", summary=f"PR #{number} review by {rname}: {state.lower()}",
                actor_kind=rkind, actor_name=rname, status="blocked" if state == "CHANGES_REQUESTED" else "completed",
                url=review.get("html_url"), keys=[f"gh:{number}", f"sha:{head_sha}", f"branch:{head_ref}"],
                metadata={"state": state, "number": number}))
        events.extend(_check_runs(fetch, base, project, head_sha, [f"gh:{number}", f"branch:{head_ref}"]))
    return events


def _check_runs(fetch: Fetch, base: str, project: Project, sha: str, extra_keys: list[str]) -> list[dict]:
    try:
        payload = fetch(f"{base}/commits/{sha}/check-runs?per_page=100")
    except GitHubUnavailable:
        return []
    events = []
    for run in payload.get("check_runs", []) if isinstance(payload, dict) else []:
        if run.get("status") != "completed":
            continue
        conclusion = run.get("conclusion") or "unknown"
        events.append(make_event(
            ts=run.get("completed_at") or run["started_at"], project_id=project.project_id, provider="github",
            etype="ci", ref=f"check:{run['id']}", summary=f"CI {run.get('name', 'check')}: {conclusion}",
            actor_kind="agent", actor_name="github-actions",
            status="completed" if conclusion in ("success", "neutral", "skipped") else "failed",
            url=run.get("html_url"), keys=[f"sha:{sha}", *extra_keys],
            metadata={"conclusion": conclusion, "name": run.get("name"), "head_sha": sha}))
    return events

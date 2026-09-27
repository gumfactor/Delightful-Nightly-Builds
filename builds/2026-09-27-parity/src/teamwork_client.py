"""Read-only client for the Teamwork.com Projects API v1 (tasks.json).

HTTP transport is injected (`http_get`) so tests can substitute a mock
instead of touching the network or monkeypatching urllib internals.
"""
from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from typing import Callable, Optional

PAGE_SIZE = 100


class TeamworkAPIError(RuntimeError):
    """Raised when the Teamwork API returns a non-2xx response or malformed body."""


HttpGet = Callable[[str, dict[str, str]], "HttpResponse"]


class HttpResponse:
    def __init__(self, status: int, body: bytes):
        self.status = status
        self.body = body


def _default_http_get(url: str, headers: dict[str, str]) -> HttpResponse:
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return HttpResponse(response.status, response.read())
    except urllib.error.HTTPError as exc:
        return HttpResponse(exc.code, exc.read())


class TeamworkClient:
    def __init__(
        self,
        domain: str,
        api_key: str,
        http_get: Optional[HttpGet] = None,
    ):
        if not domain or not api_key:
            raise ValueError("Teamwork domain and api_key are both required")
        self.domain = domain.rstrip("/")
        self._auth_header = self._build_auth_header(api_key)
        self._http_get = http_get or _default_http_get

    @staticmethod
    def _build_auth_header(api_key: str) -> str:
        # Teamwork's documented convention: API token as Basic-auth username, any password.
        token = base64.b64encode(f"{api_key}:x".encode("utf-8")).decode("ascii")
        return f"Basic {token}"

    def fetch_open_tasks(self, project_id: int) -> list[dict]:
        """Fetch every non-completed task for one project, following pagination."""
        tasks: list[dict] = []
        page = 1
        while True:
            url = (
                f"https://{self.domain}/projects/{project_id}/tasks.json"
                f"?completed=false&pageSize={PAGE_SIZE}&page={page}"
            )
            response = self._http_get(url, {"Authorization": self._auth_header})
            if response.status != 200:
                raise TeamworkAPIError(
                    f"Teamwork API returned status {response.status} for project {project_id}"
                )
            try:
                payload = json.loads(response.body)
            except json.JSONDecodeError as exc:
                raise TeamworkAPIError("Teamwork API returned malformed JSON") from exc

            raw_tasks = payload.get("todo-items", [])
            for raw in raw_tasks:
                tasks.append(_normalize_task(raw, project_id, self.domain))

            if len(raw_tasks) < PAGE_SIZE:
                break
            page += 1
        return tasks

    def fetch_open_tasks_for_projects(self, project_ids: list[int]) -> list[dict]:
        results: list[dict] = []
        for project_id in project_ids:
            results.extend(self.fetch_open_tasks(project_id))
        return results


def _normalize_task(raw: dict, project_id: int, domain: str) -> dict:
    task_id = raw["id"]
    return {
        "id": str(task_id),
        "title": raw.get("content", ""),
        "completed": bool(raw.get("completed", False)),
        "due_date": raw.get("due-date") or None,
        "project_id": project_id,
        "url": f"https://{domain}/tasks/{task_id}",
    }

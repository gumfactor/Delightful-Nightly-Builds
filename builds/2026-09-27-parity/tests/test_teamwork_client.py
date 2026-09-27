import json

import pytest

from teamwork_client import HttpResponse, TeamworkAPIError, TeamworkClient


def make_page(tasks):
    body = json.dumps({"todo-items": tasks}).encode("utf-8")
    return HttpResponse(200, body)


def task(task_id, content, completed=False, due_date=None):
    return {"id": task_id, "content": content, "completed": completed, "due-date": due_date}


def test_requires_domain_and_api_key():
    with pytest.raises(ValueError):
        TeamworkClient(domain="", api_key="key")
    with pytest.raises(ValueError):
        TeamworkClient(domain="example.teamwork.com", api_key="")


def test_fetch_open_tasks_normalizes_fields():
    calls = []

    def fake_get(url, headers):
        calls.append((url, headers))
        return make_page([task(101, "Finish report", completed=False, due_date="2026-10-01")])

    client = TeamworkClient(domain="example.teamwork.com", api_key="tok", http_get=fake_get)
    tasks = client.fetch_open_tasks(123)

    assert tasks == [
        {
            "id": "101",
            "title": "Finish report",
            "completed": False,
            "due_date": "2026-10-01",
            "project_id": 123,
            "url": "https://example.teamwork.com/tasks/101",
        }
    ]
    assert len(calls) == 1
    assert "Authorization" in calls[0][1]
    assert calls[0][1]["Authorization"].startswith("Basic ")


def test_fetch_open_tasks_paginates_until_partial_page():
    pages = [
        [task(i, f"Task {i}") for i in range(100)],  # full page -> fetch another
        [task(200, "Last task")],                    # partial page -> stop
    ]
    call_count = {"n": 0}

    def fake_get(url, headers):
        page = pages[call_count["n"]]
        call_count["n"] += 1
        return make_page(page)

    client = TeamworkClient(domain="example.teamwork.com", api_key="tok", http_get=fake_get)
    tasks = client.fetch_open_tasks(123)

    assert call_count["n"] == 2
    assert len(tasks) == 101
    assert tasks[-1]["title"] == "Last task"


def test_completed_tasks_are_not_filtered_client_side_but_query_excludes_them():
    # The client relies on the API's completed=false query param; verify it's actually sent.
    captured_url = {}

    def fake_get(url, headers):
        captured_url["url"] = url
        return make_page([])

    client = TeamworkClient(domain="example.teamwork.com", api_key="tok", http_get=fake_get)
    client.fetch_open_tasks(999)
    assert "completed=false" in captured_url["url"]


def test_non_200_status_raises_teamwork_api_error():
    def fake_get(url, headers):
        return HttpResponse(401, b'{"error": "unauthorized"}')

    client = TeamworkClient(domain="example.teamwork.com", api_key="badkey", http_get=fake_get)
    with pytest.raises(TeamworkAPIError):
        client.fetch_open_tasks(123)


def test_malformed_json_raises_teamwork_api_error():
    def fake_get(url, headers):
        return HttpResponse(200, b"not json")

    client = TeamworkClient(domain="example.teamwork.com", api_key="tok", http_get=fake_get)
    with pytest.raises(TeamworkAPIError):
        client.fetch_open_tasks(123)


def test_fetch_open_tasks_for_projects_combines_all_projects():
    def fake_get(url, headers):
        if "/projects/1/" in url:
            return make_page([task(1, "Project 1 task")])
        return make_page([task(2, "Project 2 task")])

    client = TeamworkClient(domain="example.teamwork.com", api_key="tok", http_get=fake_get)
    tasks = client.fetch_open_tasks_for_projects([1, 2])
    titles = {t["title"] for t in tasks}
    assert titles == {"Project 1 task", "Project 2 task"}

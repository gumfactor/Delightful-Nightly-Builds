import json
import sys
import threading
from pathlib import Path
from urllib import request

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sessionmemory import parsers  # noqa: E402
from sessionmemory.server import App, create_server  # noqa: E402
from sessionmemory.store import Store  # noqa: E402

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def write_jsonl(path: Path, records: list) -> Path:
    path.write_text("\n".join(r if isinstance(r, str) else json.dumps(r) for r in records) + "\n")
    return path


def cc_record(kind, content, ts="2026-09-01T10:00:00Z", **extra):
    return {"type": kind, "sessionId": "s1", "cwd": "/work/demo", "gitBranch": "main", "timestamp": ts,
            "message": {"role": kind, "content": content}, **extra}


@pytest.fixture
def store(tmp_path):
    db = Store(tmp_path / "test.db")
    yield db
    db.close()


@pytest.fixture
def demo_store(store):
    store.ingest(parsers.discover([EXAMPLES]))
    return store


@pytest.fixture
def live_server(demo_store, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")  # never used: HTTP is faked below
    posts = []

    def fake_post(url, headers, body, timeout=90):
        posts.append(body)
        return {"content": [{"type": "text", "text": '{"title": "AI title", "summary": "AI sum", "decisions": ["d1"], "open_items": ["o1"]}'}]}

    app = App(demo_store, [EXAMPLES], ai_post=fake_post)
    server = create_server(app, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]

    def call(path, data=None, headers=None):
        req = request.Request(f"http://127.0.0.1:{port}{path}", method="POST" if data is not None else "GET",
                              data=json.dumps(data).encode() if data is not None else None, headers=headers or {})
        try:
            with request.urlopen(req) as resp:
                return resp.status, resp.read()
        except request.HTTPError as err:
            return err.code, err.read()

    call.posts = posts
    call.port = port
    yield call
    server.shutdown()
    server.server_close()

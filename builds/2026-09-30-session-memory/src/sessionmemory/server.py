"""Local JSON API + static UI. Binds to loopback only."""
from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, unquote, urlparse

from . import brief as brief_mod
from . import parsers
from .store import Store
from .summarize import SummaryError, ai_summary

STATIC_DIR = Path(__file__).parent / "static"
HOST = "127.0.0.1"
MAX_BODY = 64 * 1024


class App:
    """Shared state for request handlers."""

    def __init__(self, store: Store, scan_paths: list[Path] | None = None,
                 ai_post: Callable[..., dict[str, Any]] | None = None) -> None:
        self.store = store
        self.scan_paths = scan_paths
        self.ai_post = ai_post
        self.lock = threading.Lock()

    def ingest(self) -> dict[str, int]:
        with self.lock:
            return self.store.ingest(parsers.discover(self.scan_paths))


def make_handler(app: App) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "SessionMemory/1.0"

        def log_message(self, *args: Any) -> None:  # keep the terminal quiet
            return

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, payload: Any, status: int = 200) -> None:
            self._send(status, json.dumps(payload).encode(), "application/json; charset=utf-8")

        def _error(self, status: int, message: str) -> None:
            self._json({"error": message}, status)

        def _host_ok(self) -> bool:
            # Reject DNS-rebinding style requests: only loopback Host headers are served.
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
            return host in ("127.0.0.1", "localhost", "::1")

        def do_GET(self) -> None:  # noqa: N802
            if not self._host_ok():
                return self._error(HTTPStatus.FORBIDDEN, "forbidden host")
            url = urlparse(self.path)
            query = {k: v[0] for k, v in parse_qs(url.query).items()}
            store = app.store
            with app.lock:
                if url.path in ("/", "/index.html"):
                    return self._send(200, (STATIC_DIR / "index.html").read_bytes(), "text/html; charset=utf-8")
                if url.path == "/api/status":
                    return self._json({**store.stats(), "ai_available": _has_key()})
                if url.path == "/api/projects":
                    return self._json(store.projects())
                if url.path == "/api/sessions":
                    return self._json(store.sessions(query.get("project"), query.get("source")))
                if url.path == "/api/search":
                    return self._json(store.search(query.get("q", ""), query.get("project"), query.get("source")))
                if url.path.startswith("/api/session/"):
                    session_id = unquote(url.path[len("/api/session/"):])
                    session = store.session(session_id)
                    if not session:
                        return self._error(404, "session not found")
                    session["summary"] = brief_mod.summary_for(store, session_id)
                    return self._json(session)
                if url.path == "/api/brief":
                    project = query.get("project", "")
                    if not project:
                        return self._error(400, "project is required")
                    days = int(query["days"]) if query.get("days", "").isdigit() else None
                    markdown = (store.get_brief(project, "ai") if query.get("kind") == "ai"
                                else brief_mod.build_brief(store, project, days=days))
                    if markdown is None:
                        return self._error(404, "no AI brief yet")
                    return self._json({"markdown": markdown})
            self._error(404, "not found")

        def do_POST(self) -> None:  # noqa: N802
            if not self._host_ok():
                return self._error(HTTPStatus.FORBIDDEN, "forbidden host")
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self._error(413, "body too large")
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self._error(400, "invalid JSON")
            if not isinstance(body, dict):
                return self._error(400, "expected a JSON object")
            path = urlparse(self.path).path
            try:
                if path == "/api/ingest":
                    return self._json(app.ingest())
                if path == "/api/summarize":
                    with app.lock:
                        session = app.store.session_object(str(body.get("session_id", "")))
                        if not session:
                            return self._error(404, "session not found")
                        kwargs = {"post": app.ai_post} if app.ai_post else {}
                        result = ai_summary(session, **kwargs)
                        app.store.save_summary(session.id, "ai", result)
                        return self._json({"kind": "ai", **result})
                if path == "/api/ai_brief":
                    project = str(body.get("project", ""))
                    if not project:
                        return self._error(400, "project is required")
                    with app.lock:
                        markdown = brief_mod.ai_brief(app.store, project, post=app.ai_post)
                    return self._json({"markdown": markdown})
            except SummaryError as err:
                return self._error(400, str(err))
            self._error(404, "not found")

    return Handler


def _has_key() -> bool:
    import os
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def create_server(app: App, port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((HOST, port), make_handler(app))




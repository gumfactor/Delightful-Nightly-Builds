"""Localhost-only JSON API + static single-page UI."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from . import store
from .brief import build_brief
from .summarize import SummarizeError, anthropic_complete, summarize_pending, summarize_session

STATIC = Path(__file__).parent / "static"
CSRF_HEADER = "X-Ctxvault"


class App:
    def __init__(self, conn, transcripts_dir: Path, complete=anthropic_complete):
        self.conn = conn
        self.transcripts_dir = Path(transcripts_dir)
        self.complete = complete
        self.lock = threading.Lock()


def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        server_version = "ctxvault"

        def log_message(self, *args) -> None:  # quiet by default
            pass

        def _send(self, status: int, body: bytes, ctype: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, data, status: int = 200) -> None:
            self._send(status, json.dumps(data).encode(), "application/json")

        def _host_ok(self) -> bool:
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
            return host in ("127.0.0.1", "localhost", "::1")

        def do_GET(self) -> None:
            if not self._host_ok():
                return self._json({"error": "bad host"}, 403)
            url = urlparse(self.path)
            query = parse_qs(url.query)
            arg = lambda name: (query.get(name) or [""])[0]  # noqa: E731
            path = url.path
            if path in ("/", "/index.html"):
                return self._send(200, (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
            with app.lock:
                if path == "/api/projects":
                    return self._json(store.list_projects(app.conn))
                if path == "/api/sessions":
                    return self._json(store.list_sessions(app.conn, arg("project") or None))
                if path == "/api/search":
                    return self._json(store.search(app.conn, arg("q"), arg("project") or None))
                if path.startswith("/api/session/"):
                    session = store.get_session(app.conn, unquote(path[len("/api/session/"):]))
                    return self._json(session) if session else self._json({"error": "not found"}, 404)
                if path == "/api/brief":
                    brief = build_brief(app.conn, arg("project"))
                    return self._json({"markdown": brief}) if brief else self._json({"error": "not found"}, 404)
            self._json({"error": "not found"}, 404)

        def do_POST(self) -> None:
            if not self._host_ok() or not self.headers.get(CSRF_HEADER):
                return self._json({"error": "forbidden"}, 403)
            path = urlparse(self.path).path
            with app.lock:
                if path == "/api/reindex":
                    return self._json(store.index_directory(app.conn, app.transcripts_dir))
                try:
                    if path.startswith("/api/summarize/"):
                        sid = unquote(path[len("/api/summarize/"):])
                        return self._json(summarize_session(app.conn, sid, app.complete))
                    if path == "/api/summarize":
                        project = parse_qs(urlparse(self.path).query).get("project", [""])[0] or None
                        return self._json(summarize_pending(app.conn, project, complete=app.complete))
                except SummarizeError as exc:
                    return self._json({"error": str(exc)}, 502)
            self._json({"error": "not found"}, 404)

    return Handler


def make_server(app: App, host: str = "127.0.0.1", port: int = 8765) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(app))

"""Shared test helpers."""
from __future__ import annotations

import json
import urllib.error


class FakeResponse:
    """Minimal stand-in for the object returned by urllib.request.urlopen."""

    def __init__(self, status: int, payload: object):
        self.status = status
        self._body = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False


def raise_url_error(*args, **kwargs):
    raise urllib.error.URLError("simulated network failure")

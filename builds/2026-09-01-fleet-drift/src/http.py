"""Shared HTTP transport used by gh_client, registry, and ai.

A thin, injectable wrapper around ``urllib`` so every module's tests can
supply a fake transport instead of ever touching the real network. Every
caller in this package accepts a ``transport`` parameter defaulting to
:func:`default_transport`.
"""
from __future__ import annotations

import urllib.error
import urllib.request
from typing import Callable, Dict, Optional, Tuple

Transport = Callable[..., Tuple[Optional[int], bytes]]


def default_transport(
    url: str,
    headers: Dict[str, str],
    method: str = "GET",
    data: Optional[bytes] = None,
    timeout: float = 15.0,
) -> Tuple[Optional[int], bytes]:
    """Perform a real HTTP request. Returns ``(status_code, body_bytes)``.

    ``status_code`` is ``None`` only on a connection-level failure (DNS,
    timeout, connection refused) — an HTTP error response still returns its
    real status code with whatever body the server sent.
    """
    request = urllib.request.Request(url, headers=headers, method=method, data=data)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()
    except urllib.error.URLError:
        return None, b""

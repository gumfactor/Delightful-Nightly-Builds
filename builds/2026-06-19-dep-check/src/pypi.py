"""Fetch package metadata from the PyPI JSON API."""
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

_PYPI_URL = "https://pypi.org/pypi/{package}/json"
_TIMEOUT = 10


def fetch_package_info(package_name: str) -> Optional[Dict[str, Any]]:
    """Return parsed PyPI JSON for package_name, or None on any error.

    The returned dict has the shape of the PyPI JSON API response:
    {
        "info": {"version": "...", ...},
        "releases": {"1.0.0": [{"upload_time": "...", "yanked": bool, ...}], ...},
        "urls": [...],
    }
    """
    url = _PYPI_URL.format(package=package_name)
    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None  # Package not on PyPI
        return None
    except Exception:
        return None


def extract_version_info(
    pypi_data: Dict[str, Any],
    pinned_version: Optional[str],
) -> tuple[Optional[str], Optional[str], bool, Optional[str]]:
    """Extract (latest_version, pinned_upload_date, yanked, yanked_reason).

    pinned_upload_date is the ISO upload date string for the pinned version,
    or None if pinned_version is None or not found in releases.
    """
    latest_version = pypi_data.get("info", {}).get("version")
    pinned_upload_date = None
    yanked = False
    yanked_reason = None

    if pinned_version:
        releases = pypi_data.get("releases", {})
        # Try exact match, then normalised (replace hyphens/underscores)
        release_files = releases.get(pinned_version, [])
        if release_files:
            # Use the first file's upload_time
            pinned_upload_date = release_files[0].get("upload_time_iso_8601") or release_files[0].get("upload_time")
            # A release is yanked if any of its files is yanked
            if any(f.get("yanked", False) for f in release_files):
                yanked = True
                yanked_reason = next(
                    (f.get("yanked_reason") for f in release_files if f.get("yanked")),
                    None,
                )

    return latest_version, pinned_upload_date, yanked, yanked_reason

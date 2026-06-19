"""Parse requirements files into Requirement objects."""
import re
import configparser
from typing import List
from src.models import Requirement

# Matches: name[extras]specifier ; marker  # comment
# Groups: (name)(extras)(specifier)(version)
_REQ_RE = re.compile(
    r"""
    ^
    \s*
    ([\w][\w.\-]*)          # package name (group 1)
    (?:\[[\w,\s]*\])?       # optional extras — consumed but not captured
    \s*
    (                        # specifier group (group 2)
        [><=!~]{1,3}         # operator
        \s*
        [\w.*]+              # version
        (?:\s*,\s*[><=!~]{1,3}\s*[\w.*]+)*  # additional specifiers
    )?
    \s*
    (?:;[^#]*)?             # optional environment marker — consumed
    (?:\#.*)?               # optional inline comment
    $
    """,
    re.VERBOSE,
)

# Extracts a single ==version pin from a specifier string
_EXACT_PIN_RE = re.compile(r"==\s*([\w.]+)")


def _normalise_name(name: str) -> str:
    """Canonicalise a package name: lowercase, underscores → hyphens."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirements_txt(text: str, source_file: str = "requirements.txt") -> List[Requirement]:
    """Parse a requirements.txt file body into a list of Requirements.

    Skips blank lines, comment-only lines, and entries that look like URLs
    or editable installs (-e, -r, http://, git+).
    """
    results = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        # Skip URL-style or flag-style entries
        if line.startswith(("-e", "-r", "http://", "https://", "git+")):
            continue

        match = _REQ_RE.match(line)
        if not match:
            continue

        raw_name, specifier = match.group(1), match.group(2)
        name = _normalise_name(raw_name)
        specifier = specifier.strip() if specifier else None

        pinned_version = None
        if specifier:
            pin_match = _EXACT_PIN_RE.search(specifier)
            if pin_match:
                pinned_version = pin_match.group(1)

        results.append(Requirement(
            name=name,
            pinned_version=pinned_version,
            specifier=specifier,
            source_file=source_file,
        ))
    return results


def parse_setup_cfg(text: str, source_file: str = "setup.cfg") -> List[Requirement]:
    """Parse install_requires from a setup.cfg body."""
    cfg = configparser.ConfigParser()
    cfg.read_string(text)
    try:
        raw = cfg.get("options", "install_requires")
    except (configparser.NoSectionError, configparser.NoOptionError):
        return []

    # install_requires is a newline-delimited block; each line is a PEP 508 dep
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    return parse_requirements_txt("\n".join(lines), source_file=source_file)


def parse_pipfile(text: str, source_file: str = "Pipfile") -> List[Requirement]:
    """Parse [packages] and [dev-packages] from a Pipfile body.

    Handles: requests = "*", requests = "==2.28.0", requests = {version = "==2.28.0"}
    """
    results = []
    in_packages = False

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if re.match(r"^\[(packages|dev-packages)\]", line, re.IGNORECASE):
            in_packages = True
            continue
        if line.startswith("[") and in_packages:
            in_packages = False
            continue
        if not in_packages or not line or line.startswith("#"):
            continue

        # key = value
        kv_match = re.match(r'^([\w.\-]+)\s*=\s*(.+)$', line)
        if not kv_match:
            continue

        raw_name = kv_match.group(1)
        value = kv_match.group(2).strip().strip('"\'')
        name = _normalise_name(raw_name)

        # value may be "*" or "==2.28.0" or {version = "==2.28.0", ...}
        specifier = None
        pinned_version = None

        if value == "*":
            pass  # unpinned
        elif value.startswith("{"):
            # Inline table: extract version key
            ver_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', value)
            if ver_match:
                specifier = ver_match.group(1)
        else:
            specifier = value

        if specifier:
            pin_match = _EXACT_PIN_RE.search(specifier)
            if pin_match:
                pinned_version = pin_match.group(1)

        results.append(Requirement(
            name=name,
            pinned_version=pinned_version,
            specifier=specifier,
            source_file=source_file,
        ))

    return results

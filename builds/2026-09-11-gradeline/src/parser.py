"""Submission loading.

Two supported input shapes:
  - a folder of one .txt/.md file per student (filename stem = identifier)
  - a single file with `=== NAME ===` delimited sections
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass


class ParseError(ValueError):
    pass


@dataclass
class Submission:
    identifier: str
    text: str


_DELIMITER_RE = re.compile(r"^===\s*(.+?)\s*===\s*$", re.MULTILINE)

_TEXT_EXTENSIONS = (".txt", ".md")


def load_from_folder(folder: str) -> list[Submission]:
    if not os.path.isdir(folder):
        raise ParseError(f"Not a directory: {folder}")
    submissions = []
    for name in sorted(os.listdir(folder)):
        stem, ext = os.path.splitext(name)
        if ext.lower() not in _TEXT_EXTENSIONS:
            continue
        full_path = os.path.join(folder, name)
        if not os.path.isfile(full_path):
            continue
        with open(full_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        submissions.append(Submission(identifier=stem, text=text))
    if not submissions:
        raise ParseError(f"No .txt/.md files found in {folder}")
    return submissions


def load_from_delimited_file(path: str) -> list[Submission]:
    if not os.path.isfile(path):
        raise ParseError(f"Not a file: {path}")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    matches = list(_DELIMITER_RE.finditer(content))
    if not matches:
        raise ParseError(
            "No '=== NAME ===' delimiters found. Each student section must "
            "start with a line like '=== Jane Doe ==='."
        )
    submissions = []
    for i, match in enumerate(matches):
        identifier = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        text = content[start:end].strip()
        submissions.append(Submission(identifier=identifier, text=text))
    return submissions


def load_submissions(path: str) -> list[Submission]:
    if os.path.isdir(path):
        return load_from_folder(path)
    return load_from_delimited_file(path)

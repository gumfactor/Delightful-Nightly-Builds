#!/usr/bin/env python3
"""Protocol Forge — IRB/ethics protocol drafting & compliance assistant.

Usage:
    python3 protocol_forge.py init study.json
    python3 protocol_forge.py check study.json
    python3 protocol_forge.py draft study.json --out draft.md
    python3 protocol_forge.py approve 1
    python3 protocol_forge.py list
    python3 protocol_forge.py show 1

See Manual.md for the full command reference and study JSON field guide.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

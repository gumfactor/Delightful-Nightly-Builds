#!/usr/bin/env python3
"""Rotation Radar entry point.

Usage:
    python main.py [--benchmark SPY] [--sectors XLK XLF ...] [--period 9mo]
                    [--ratio-window 10] [--momentum-window 10] [--tail-length 10]
                    [--no-ai] [--output rotation_radar.html] [--db-path rotation_radar.db]

See Manual.md for details.
"""

from src.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

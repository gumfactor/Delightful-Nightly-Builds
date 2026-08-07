#!/usr/bin/env python3
"""Waymark entry point: python main.py <command> ..."""

import sys

from src.cli import main

if __name__ == "__main__":
    sys.exit(main())

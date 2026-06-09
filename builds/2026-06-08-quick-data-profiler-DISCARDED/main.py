"""
Quick Data Profiler — CLI entry point.
Usage: python3 main.py <file> [--top N] [--sample N] [--format text|json]
"""

import argparse
import sys
from pathlib import Path

# Allow running from the build folder or from anywhere with the folder on PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from src.profiler import profile_file, format_text, format_json


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="dataprofile",
        description="Profile a CSV or JSON/JSONL file: types, nulls, distributions, top values.",
    )
    parser.add_argument(
        "file",
        help="Path to the CSV, JSON, or JSONL file to profile.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        metavar="N",
        help="Number of top values to show for low-cardinality columns (default: 5).",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=3,
        metavar="N",
        help="Number of sample values to show per column (default: 3).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: 'text' (default) or 'json'.",
    )

    args = parser.parse_args()

    try:
        profile = profile_file(args.file, top_n=args.top, sample_n=args.sample)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(format_json(profile))
    else:
        print(format_text(profile))

    return 0


if __name__ == "__main__":
    sys.exit(main())

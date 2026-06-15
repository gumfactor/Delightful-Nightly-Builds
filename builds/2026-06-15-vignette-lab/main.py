#!/usr/bin/env python3
"""Vignette Lab — CLI entry point for the psychological scenario generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from the build folder root without installing as a package
sys.path.insert(0, str(Path(__file__).parent))

from src.generator import generate_vignettes, list_themes
from src.formatter import format_participant, format_researcher, format_stdout


def cmd_list(_args: argparse.Namespace) -> int:
    themes = list_themes()
    print("\nAvailable themes:\n")
    for key, info in themes.items():
        print(f"  {key:<10}  {info['label']}")
        print(f"  {'':10}  {info['description']}")
        print(
            f"  {'':10}  "
            f"{info['settings']} settings × {info['events']} events × "
            f"{len(info)} characters ≈ {info['combinations']} combinations"
        )
        print()
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    try:
        vignettes = generate_vignettes(
            theme=args.theme,
            count=args.count,
            seed=args.seed,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        prefix = args.output
        p_path = Path(f"{prefix}_participant.md")
        r_path = Path(f"{prefix}_researcher.md")
        p_path.write_text(format_participant(vignettes), encoding="utf-8")
        r_path.write_text(format_researcher(vignettes), encoding="utf-8")
        print(f"Wrote {len(vignettes)} vignette(s):")
        print(f"  Participant version → {p_path}")
        print(f"  Researcher version  → {r_path}")
    else:
        print(format_stdout(vignettes, researcher=args.researcher))

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vignette-lab",
        description="Generate psychological scenario vignettes for research and teaching.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    list_p = sub.add_parser("list", help="Show available themes and element counts")
    list_p.set_defaults(func=cmd_list)

    # generate
    gen_p = sub.add_parser("generate", help="Generate a set of vignettes")
    gen_p.add_argument(
        "--theme", required=True,
        help="Scenario theme: stress | empathy | moral",
    )
    gen_p.add_argument(
        "--count", type=int, default=5,
        help="Number of vignettes to generate (default: 5)",
    )
    gen_p.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducible output",
    )
    gen_p.add_argument(
        "--output", default=None,
        help="Output file prefix. Writes <prefix>_participant.md and <prefix>_researcher.md",
    )
    gen_p.add_argument(
        "--researcher", action="store_true",
        help="When printing to stdout, include manipulation checks and notes",
    )
    gen_p.set_defaults(func=cmd_generate)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

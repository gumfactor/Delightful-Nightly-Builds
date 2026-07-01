"""Safe, opt-in auto-fix for zero-padding inconsistencies.

Scope is deliberately narrow: only the filename's entity values are
corrected (never directory names), a rename is only ever planned when the
target does not already exist, and every destination path is verified to
resolve inside the dataset root before any filesystem call is made.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from .bids_rules import ParsedFile


@dataclass
class RenamePlan:
    old_relpath: str
    new_relpath: str
    entity: str
    reason: str


@dataclass
class FixResult:
    plan: RenamePlan
    status: str  # "applied" | "planned" | "skipped_exists" | "skipped_unsafe"


def _rebuild_relpath(f: ParsedFile, key: str, new_value: str) -> str:
    old = PurePosixPath(f.relpath)
    new_entities = dict(f.entities)
    new_entities[key] = new_value
    parts = [f"{k}-{v}" for k, v in new_entities.items()]
    new_filename = "_".join(parts)
    if f.suffix:
        new_filename += "_" + f.suffix
    new_filename += f.extension
    if old.parent == PurePosixPath("."):
        return new_filename
    return str(old.parent / new_filename)


def compute_padding_fixes(files: list[ParsedFile]) -> list[RenamePlan]:
    plans: list[RenamePlan] = []
    for key in ("sub", "ses", "run"):
        widths: dict[int, list[ParsedFile]] = {}
        for f in files:
            value = f.entities.get(key)
            if value and value.isdigit():
                widths.setdefault(len(value), []).append(f)
        if len(widths) <= 1:
            continue
        # Tie-break on width itself (prefer the wider, more conventional
        # zero-padded form) so an even split never picks arbitrarily.
        majority_width = max(widths, key=lambda w: (len(widths[w]), w))
        for width, group in widths.items():
            if width == majority_width:
                continue
            for f in group:
                old_value = f.entities[key]
                new_value = old_value.zfill(majority_width)
                new_relpath = _rebuild_relpath(f, key, new_value)
                if new_relpath == f.relpath:
                    continue
                plans.append(
                    RenamePlan(
                        old_relpath=f.relpath,
                        new_relpath=new_relpath,
                        entity=key,
                        reason=(
                            f"Pad '{key}-{old_value}' to '{key}-{new_value}' to match "
                            f"the dataset's dominant width ({majority_width} digits)"
                        ),
                    )
                )
    return plans


def apply_fixes(plans: list[RenamePlan], root: Path, dry_run: bool = True) -> list[FixResult]:
    root_resolved = root.resolve()
    results: list[FixResult] = []
    for plan in plans:
        src = (root / plan.old_relpath).resolve()
        dst = (root / plan.new_relpath).resolve()

        if root_resolved not in dst.parents and dst != root_resolved:
            results.append(FixResult(plan, "skipped_unsafe"))
            continue
        if not str(dst).startswith(str(root_resolved)):
            results.append(FixResult(plan, "skipped_unsafe"))
            continue
        if dst.exists():
            results.append(FixResult(plan, "skipped_exists"))
            continue
        if dry_run:
            results.append(FixResult(plan, "planned"))
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        results.append(FixResult(plan, "applied"))
    return results

"""Freshness and conflict checks: never present stale or inferred state as confirmed-current."""
import re
from datetime import datetime, timezone
from typing import Optional

from .correlate import Workstream
from .project import Project, git

STALE_AFTER_DAYS = 14
STOPWORDS = {"the", "and", "for", "with", "that", "this", "from", "into", "add", "make", "when", "then", "also"}
OVERLAP_THRESHOLD = 0.6


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9_]{3,}", text.lower()) if w not in STOPWORDS}


def _tip(project: Project, branch: Optional[str]) -> Optional[str]:
    if not branch:
        return None
    for ref in (branch, f"origin/{branch}"):
        sha = git(project.root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False).strip()
        if sha:
            return sha
    return None


def _has_commit(project: Project, sha: str) -> bool:
    return bool(git(project.root, "cat-file", "-t", sha, check=False).strip())


def _age_days(ts: str, now: datetime) -> float:
    return (now - datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)).total_seconds() / 86400


def check(project: Project, ws: Workstream, now: Optional[datetime] = None) -> list[dict]:
    """Return findings: {level: 'stale'|'warn'|'info', text, evidence:[event ids]}."""
    now = now or datetime.now(timezone.utc)
    findings: list[dict] = []
    checkpoints = ws.by_type("checkpoint")
    for cp in checkpoints:
        meta, label = cp["metadata"], f"checkpoint {cp['id'][4:12]} ({cp['provider']})"
        head, branch = meta.get("head"), meta.get("branch")
        tip = _tip(project, branch)
        if branch and tip is None:
            findings.append({"level": "stale", "evidence": [cp["id"]],
                             "text": f"{label}: recorded branch '{branch}' no longer exists (merged or deleted?)"})
        elif head and tip and head != tip:
            if _has_commit(project, head):
                ahead = git(project.root, "rev-list", "--count", f"{head}..{tip}", check=False).strip() or "?"
                text = f"{label}: recorded at {head[:8]}, '{branch}' is now {tip[:8]} (+{ahead} commit(s) since)"
            else:
                text = f"{label}: recorded head {head[:8]} is not in this repo; '{branch}' is now {tip[:8]}"
            findings.append({"level": "stale", "text": text, "evidence": [cp["id"]]})
        elif _age_days(cp["ts"], now) > STALE_AFTER_DAYS:
            findings.append({"level": "warn", "evidence": [cp["id"]],
                             "text": f"{label}: {int(_age_days(cp['ts'], now))} days old (branch unchanged)"})

        later = [e for e in ws.events if e["ts"] > cp["ts"] and e["id"] != cp["id"]]
        closers = [e for e in later if e["ref"].endswith((":merged", ":closed"))]
        for event in closers:
            findings.append({"level": "stale", "evidence": [cp["id"], event["id"]],
                             "text": f"{label}: superseded by later event — {event['summary']}"})
        ci = [e for e in later if e["type"] == "ci"]
        if ci:
            newest = ci[-1]
            findings.append({"level": "info", "evidence": [cp["id"], newest["id"]],
                             "text": f"{label}: {len(ci)} CI result(s) since; latest — {newest['summary']}"})

    if checkpoints:
        latest = checkpoints[-1]
        for step in latest["metadata"].get("next_steps", []):
            step_tokens = _tokens(step)
            if len(step_tokens) < 2:
                continue
            for event in ws.events:
                if event["ts"] <= latest["ts"] or event["type"] not in ("commit", "decision"):
                    continue
                overlap = len(step_tokens & _tokens(event["summary"])) / len(step_tokens)
                if overlap >= OVERLAP_THRESHOLD:
                    findings.append({"level": "warn", "evidence": [latest["id"], event["id"]],
                                     "text": f"inferred: next step '{step}' may already be done — later "
                                             f"{event['type']} {event['ref'][:8]}: {event['summary']}"})
                    break
    return findings


def is_stale(findings: list[dict]) -> bool:
    return any(f["level"] == "stale" for f in findings)

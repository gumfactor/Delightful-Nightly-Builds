"""Aggregate sessions into metrics and findings."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .parse import ScanStats, Session, Turn
from .pricing import PriceTable

ACTIVE_GAP = timedelta(minutes=5)
READ_THRASH_MIN = 3
RETRY_LOOP_MIN = 3
BIG_CONTEXT_TOKENS = 150_000
LOW_CACHE_RATIO = 0.5
LOW_CACHE_MIN_TOKENS = 200_000
ERROR_RATE_THRESHOLD = 0.25
ERROR_RATE_MIN_CALLS = 10
FILE_TOOLS = {"Read"}
COMMAND_TOOLS = {"Bash"}


def turn_cost(turn: Turn, prices: PriceTable) -> float | None:
    return prices.cost(turn.model, turn.input, turn.output, turn.cache_write, turn.cache_read)


def _cache_ratio(cache_read: int, context: int) -> float:
    return cache_read / context if context else 0.0


def active_seconds(turns: list[Turn]) -> float:
    total = timedelta()
    for previous, current in zip(turns, turns[1:]):
        gap = current.ts - previous.ts
        if gap <= ACTIVE_GAP:
            total += gap
    return total.total_seconds()


def _session_findings(session: Session) -> list[dict]:
    findings: list[dict] = []
    sid = session.id

    def add(kind: str, severity: str, message: str) -> None:
        findings.append({"kind": kind, "severity": severity, "session": sid, "project": session.project, "message": message})

    calls = [(name, key, tool_id) for turn in session.turns for tool_id, name, key in turn.tools]
    reads = Counter(key for name, key, _ in calls if name in FILE_TOOLS and key)
    for path, count in reads.items():
        if count >= READ_THRASH_MIN:
            add("read_thrash", "warn", f"Read {path} {count} times in one session; consider a summary note or narrower reads.")
    failures = Counter(key for name, key, tool_id in calls if name in COMMAND_TOOLS and key and session.results.get(tool_id))
    for command, count in failures.items():
        if count >= RETRY_LOOP_MIN:
            add("retry_loop", "high", f"Command failed {count} times: {command[:80]}")
    context_in = sum(t.context for t in session.turns)
    cache_read = sum(t.cache_read for t in session.turns)
    if context_in >= LOW_CACHE_MIN_TOKENS and _cache_ratio(cache_read, context_in) < LOW_CACHE_RATIO:
        ratio = _cache_ratio(cache_read, context_in)
        add("low_cache", "warn", f"Cache hit ratio {ratio:.0%} over {context_in:,} input tokens; long idle gaps or edited prompt prefixes likely.")
    peak = max((t.context for t in session.turns), default=0)
    if peak >= BIG_CONTEXT_TOKENS:
        add("big_context", "warn", f"Context reached {peak:,} tokens; split the task or compact earlier.")
    resolved = [session.results[tool_id] for _, _, tool_id in calls if tool_id in session.results]
    if len(resolved) >= ERROR_RATE_MIN_CALLS and sum(resolved) / len(resolved) > ERROR_RATE_THRESHOLD:
        add("high_error_rate", "warn", f"{sum(resolved)} of {len(resolved)} tool calls errored ({sum(resolved) / len(resolved):.0%}).")
    return findings


def analyze(sessions: list[Session], stats: ScanStats, prices: PriceTable, tz_name: str = "America/Toronto",
            since: datetime | None = None) -> dict:
    tz = ZoneInfo(tz_name)
    by_day: dict[str, dict] = defaultdict(lambda: _bucket())
    by_model: dict[str, dict] = defaultdict(lambda: _bucket())
    by_project: dict[str, dict] = defaultdict(lambda: _bucket())
    tools: Counter = Counter()
    tool_errors: Counter = Counter()
    session_rows: list[dict] = []
    findings: list[dict] = []
    unpriced: set[str] = set()
    totals = _bucket()
    saved = 0.0
    sidechain_tokens = 0

    for session in sessions:
        turns = [t for t in session.turns if since is None or t.ts >= since]
        if not turns:
            continue
        scoped = Session(session.id, session.project, turns, session.results)
        row = _bucket()
        session_unpriced = False
        for turn in turns:
            cost = turn_cost(turn, prices)
            if cost is None:
                unpriced.add(turn.model)
                session_unpriced = True
            day = turn.ts.astimezone(tz).strftime("%Y-%m-%d")
            for bucket in (totals, row, by_day[day], by_model[turn.model], by_project[turn.project]):
                _add(bucket, turn, cost or 0.0)
            saved += prices.cache_savings(turn.model, turn.cache_read)
            if turn.sidechain:
                sidechain_tokens += turn.input + turn.output + turn.cache_write + turn.cache_read
            for tool_id, name, _ in turn.tools:
                tools[name] += 1
                if scoped.results.get(tool_id):
                    tool_errors[name] += 1
        row.update(
            id=session.id, project=session.project, start=turns[0].ts.astimezone(tz).strftime("%Y-%m-%d %H:%M"),
            active_min=round(active_seconds(turns) / 60, 1), peak_context=max(t.context for t in turns),
            cache_hit=_cache_ratio(row["cache_read"], row["input"] + row["cache_write"] + row["cache_read"]),
            unpriced=session_unpriced,
        )
        session_rows.append(row)
        findings.extend(_session_findings(scoped))

    for model in sorted(unpriced):
        findings.append({"kind": "unpriced_model", "severity": "info", "session": "", "project": "",
                         "message": f"No price for model {model!r}; its cost is excluded. Add it to pricing.json."})
    order = {"high": 0, "warn": 1, "info": 2}
    findings.sort(key=lambda f: order[f["severity"]])
    all_tokens = totals["input"] + totals["output"] + totals["cache_write"] + totals["cache_read"]
    totals.update(
        sessions=len(session_rows), saved_by_cache=saved,
        cache_hit=_cache_ratio(totals["cache_read"], totals["input"] + totals["cache_write"] + totals["cache_read"]),
        sidechain_share=sidechain_tokens / all_tokens if all_tokens else 0.0,
        active_min=round(sum(r["active_min"] for r in session_rows), 1),
    )
    return {
        "totals": totals,
        "by_day": [dict(day=k, **v) for k, v in sorted(by_day.items())],
        "by_model": sorted((dict(model=k, **v) for k, v in by_model.items()), key=lambda r: -r["cost"]),
        "by_project": sorted((dict(project=k, **v) for k, v in by_project.items()), key=lambda r: -r["cost"]),
        "sessions": sorted(session_rows, key=lambda r: -r["cost"]),
        "tools": [{"tool": k, "calls": v, "errors": tool_errors[k]} for k, v in tools.most_common()],
        "findings": findings,
        "unpriced_models": sorted(unpriced),
        "scan": vars(stats).copy(),
        "timezone": tz_name,
    }


def _bucket() -> dict:
    return {"turns": 0, "input": 0, "output": 0, "cache_write": 0, "cache_read": 0, "cost": 0.0}


def _add(bucket: dict, turn: Turn, cost: float) -> None:
    bucket["turns"] += 1
    bucket["input"] += turn.input
    bucket["output"] += turn.output
    bucket["cache_write"] += turn.cache_write
    bucket["cache_read"] += turn.cache_read
    bucket["cost"] += cost

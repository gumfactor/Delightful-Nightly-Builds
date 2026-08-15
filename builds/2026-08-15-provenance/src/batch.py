"""CSV-in, CSV-out batch orchestration: resolve → classify → cache → write."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from typing import Callable, Optional

from src import ai_enrich, rules, store, wikidata

OUTPUT_FIELDS_APPENDED = ["verdict", "confidence", "evidence", "wikidata_qid", "ai_note"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_input_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [row for row in reader]


def write_output_csv(path: str, rows: list[dict], input_fieldnames: list[str]) -> None:
    fieldnames = list(input_fieldnames) + [
        field for field in OUTPUT_FIELDS_APPENDED if field not in input_fieldnames
    ]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def resolve_business(name: str) -> dict:
    """Resolve a single business name against Wikidata and classify it.

    Never touches the cache — pure network-in, classification-out. Callers
    decide whether to check the cache first (that's ``classify_batch``'s job).
    """
    qid = wikidata.search_entity(name)
    resolved = rules.empty_resolution()

    if qid:
        claims = wikidata.get_claims(qid)
        resolved["own_country"] = claims["country"]
        if claims["headquarters"]:
            resolved["headquarters_country"] = wikidata.get_claims(claims["headquarters"])["country"]
        if claims["parent_org"]:
            resolved["parent_country"] = wikidata.get_claims(claims["parent_org"])["country"]
        if claims["owned_by"]:
            resolved["owner_country"] = wikidata.get_claims(claims["owned_by"])["country"]

    verdict, confidence, evidence = rules.classify(resolved)
    return {"qid": qid, "verdict": verdict, "confidence": confidence, "evidence": evidence}


def classify_batch(
    input_rows: list[dict],
    conn,
    *,
    refresh: bool = False,
    ai_enrich_enabled: bool = False,
    api_key: Optional[str] = None,
    now_fn: Optional[Callable[[], str]] = None,
) -> tuple[list[dict], dict]:
    """Classify every row in a batch, cache-first unless refresh is set.

    Returns (output_rows, stats). Rows with a blank ``name`` are skipped and
    counted in stats["skipped"] rather than raising.
    """
    now_fn = now_fn or _utc_now_iso
    stats = {
        "total": 0,
        "canadian": 0,
        "foreign": 0,
        "uncertain": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "skipped": 0,
    }
    output_rows = []

    for row in input_rows:
        name = (row.get("name") or "").strip()
        if not name:
            stats["skipped"] += 1
            continue

        stats["total"] += 1
        cached = None if refresh else store.get_latest(conn, name)

        if cached is not None:
            stats["cache_hits"] += 1
            verdict = cached["verdict"]
            confidence = cached["confidence"]
            evidence = cached["evidence"]
            qid = cached["wikidata_qid"]
            ai_note = cached["ai_note"]
        else:
            stats["cache_misses"] += 1
            result = resolve_business(name)
            verdict, confidence, evidence, qid = (
                result["verdict"],
                result["confidence"],
                result["evidence"],
                result["qid"],
            )
            ai_note = None
            if ai_enrich_enabled and verdict == rules.VERDICT_UNCERTAIN:
                ai_note = ai_enrich.enrich(name, evidence, verdict, api_key=api_key)
            store.save_resolution(
                conn,
                business_name=name,
                website=row.get("website"),
                wikidata_qid=qid,
                verdict=verdict,
                confidence=confidence,
                evidence=evidence,
                ai_note=ai_note,
                resolved_at=now_fn(),
            )

        stats[verdict] = stats.get(verdict, 0) + 1
        output_rows.append(
            {
                **row,
                "verdict": verdict,
                "confidence": confidence,
                "evidence": evidence,
                "wikidata_qid": qid or "",
                "ai_note": ai_note or "",
            }
        )

    return output_rows, stats

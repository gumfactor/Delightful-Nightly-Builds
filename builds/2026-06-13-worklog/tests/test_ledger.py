"""Tests for the SQLite event ledger: schema, insert, dedup, and queries."""

import json
import tempfile
from pathlib import Path

import pytest

from src.ledger import (
    init_schema,
    insert_event,
    insert_decision,
    upsert_workstream,
    assign_workstream,
    query_events,
    query_workstreams,
    query_decisions,
    get_latest_event_of_type,
    make_event_id,
)


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test.db"
    init_schema(db_path)
    return db_path


def _make_event(
    project_id="proj-1",
    event_type="commit",
    source_ref="abc123",
    provider="git",
    timestamp="2026-06-13T08:00:00Z",
    summary="Add feature",
    status="completed",
) -> dict:
    return {
        "id": make_event_id(provider, source_ref, event_type),
        "timestamp": timestamp,
        "project_id": project_id,
        "type": event_type,
        "actor_kind": "human",
        "actor_name": "alice",
        "summary": summary,
        "status": status,
        "workstream_id": None,
        "provider": provider,
        "source_ref": source_ref,
        "source_url": None,
        "metadata": {},
    }


class TestSchemaInit:
    def test_schema_creates_tables(self, db):
        """Schema initialisation creates all required tables."""
        import sqlite3
        conn = sqlite3.connect(str(db))
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        conn.close()
        assert "events" in tables
        assert "workstreams" in tables
        assert "decisions" in tables
        assert "schema_version" in tables

    def test_schema_idempotent(self, db):
        """Calling init_schema twice does not raise or duplicate the version row."""
        init_schema(db)  # second call
        import sqlite3
        conn = sqlite3.connect(str(db))
        count = conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()[0]
        conn.close()
        assert count == 1


class TestEventInsert:
    def test_insert_returns_true_for_new_event(self, db):
        evt = _make_event()
        assert insert_event(db, evt) is True

    def test_deduplication_returns_false_for_duplicate(self, db):
        evt = _make_event()
        insert_event(db, evt)
        assert insert_event(db, evt) is False

    def test_same_source_ref_different_type_gives_different_id(self, db):
        evt1 = _make_event(event_type="commit", source_ref="abc123")
        evt2 = _make_event(event_type="issue", source_ref="abc123", provider="github")
        assert evt1["id"] != evt2["id"]
        assert insert_event(db, evt1) is True
        assert insert_event(db, evt2) is True

    def test_query_events_returns_inserted_event(self, db):
        evt = _make_event()
        insert_event(db, evt)
        results = query_events(db, "proj-1")
        assert len(results) == 1
        assert results[0]["summary"] == "Add feature"

    def test_query_events_filters_by_type(self, db):
        insert_event(db, _make_event(event_type="commit", source_ref="c1"))
        insert_event(db, _make_event(event_type="issue", source_ref="i1", provider="github"))
        commits = query_events(db, "proj-1", event_type="commit")
        assert len(commits) == 1
        assert commits[0]["type"] == "commit"

    def test_query_events_filters_by_since(self, db):
        insert_event(db, _make_event(source_ref="old", timestamp="2026-01-01T00:00:00Z"))
        insert_event(db, _make_event(source_ref="new", timestamp="2026-06-13T00:00:00Z"))
        recent = query_events(db, "proj-1", since="2026-06-01T00:00:00Z")
        assert len(recent) == 1
        assert recent[0]["source_ref"] == "new"

    def test_query_events_filters_by_workstream(self, db):
        evt = _make_event(source_ref="ref1")
        insert_event(db, evt)
        assign_workstream(db, evt["id"], "ws_abc")
        results = query_events(db, "proj-1", workstream_id="ws_abc")
        assert len(results) == 1

    def test_get_latest_event_of_type(self, db):
        insert_event(db, _make_event(source_ref="r1", timestamp="2026-06-12T00:00:00Z"))
        insert_event(db, _make_event(source_ref="r2", timestamp="2026-06-13T00:00:00Z"))
        latest = get_latest_event_of_type(db, "proj-1", "commit")
        assert latest is not None
        assert latest["source_ref"] == "r2"


class TestDecisionInsert:
    def test_insert_decision(self, db):
        dec = {
            "id": "dec_test001",
            "event_id": "evt_abc",
            "workstream_id": "ws_001",
            "summary": "Reject coercion",
            "reason": "Data loss risk",
            "alternatives": ["Coerce automatically"],
            "timestamp": "2026-06-13T08:00:00Z",
        }
        assert insert_decision(db, dec) is True

    def test_decision_deduplication(self, db):
        dec = {
            "id": "dec_test002",
            "event_id": "evt_abc",
            "workstream_id": None,
            "summary": "Use SQLite",
            "reason": "Reliable",
            "alternatives": [],
            "timestamp": "2026-06-13T08:00:00Z",
        }
        insert_decision(db, dec)
        assert insert_decision(db, dec) is False

    def test_query_decisions_by_keyword(self, db):
        dec = {
            "id": "dec_kw001",
            "event_id": "evt_001",
            "workstream_id": None,
            "summary": "Reject automatic coercion",
            "reason": "Silent data corruption risk",
            "alternatives": [],
            "timestamp": "2026-06-13T08:00:00Z",
        }
        insert_decision(db, dec)
        results = query_decisions(db, keyword="coercion")
        assert len(results) == 1
        assert "coercion" in results[0]["summary"].lower()


class TestWorkstreams:
    def test_workstream_upsert_and_query(self, db):
        evt = _make_event(source_ref="w1")
        insert_event(db, evt)
        assign_workstream(db, evt["id"], "ws_feature")
        upsert_workstream(db, {"id": "ws_feature", "title": "Feature work", "status": "active", "evidence": []})
        ws_list = query_workstreams(db, "proj-1")
        assert len(ws_list) == 1
        assert ws_list[0]["title"] == "Feature work"
        assert ws_list[0]["event_count"] == 1

import pytest

from worklog.ledger import Ledger, event_id, make_event, to_utc


def _event(ref="abc", summary="one", **kw):
    return make_event(ts="2026-09-01T10:00:00+02:00", project_id="p", etype="commit", provider="git", ref=ref,
                      summary=summary, **kw)


def test_event_ids_are_deterministic_and_source_specific():
    assert event_id("git", "commit", "abc") == event_id("git", "commit", "abc")
    assert event_id("git", "commit", "abc") != event_id("github", "commit", "abc")


def test_timestamps_are_normalised_to_utc():
    assert to_utc("2026-09-01T10:00:00+02:00") == "2026-09-01T08:00:00Z"
    assert to_utc("2026-09-01T10:00:00") == "2026-09-01T10:00:00Z"


def test_reingesting_same_source_record_never_duplicates(ledger):
    assert ledger.ingest([_event()]) == {"inserted": 1, "unchanged": 0, "updated": 0}
    assert ledger.ingest([_event()]) == {"inserted": 0, "unchanged": 1, "updated": 0}
    assert ledger.count("p") == 1


def test_immutable_events_ignore_changed_content_unless_replace(ledger):
    ledger.ingest([_event(summary="first")])
    ledger.ingest([_event(summary="second")])
    assert ledger.events("p")[0]["summary"] == "first"
    assert ledger.ingest([_event(summary="second")], replace=True)["updated"] == 1
    assert ledger.events("p")[0]["summary"] == "second"


def test_failed_batch_rolls_back_atomically(ledger):
    good, bad = _event(ref="good"), _event(ref="bad")
    bad["keys"] = object()  # not JSON serialisable -> raises mid-transaction
    with pytest.raises(TypeError):
        ledger.ingest([good, bad])
    assert ledger.count("p") == 0


def test_summary_is_single_line_and_capped():
    event = _event(summary="line one\nline two " + "x" * 500)
    assert "\n" not in event["summary"] and len(event["summary"]) <= 300


def test_get_event_by_id_prefix_or_commit_sha(ledger):
    event = _event(ref="deadbeefcafe1234")
    ledger.ingest([event])
    assert ledger.get_event(event["id"][:10])["ref"] == "deadbeefcafe1234"
    assert ledger.get_event("deadbeef")["id"] == event["id"]
    assert ledger.get_event("nomatch") is None


def test_filters_by_type_and_since(ledger):
    ledger.ingest([_event(ref="a"), make_event(ts="2026-09-09T00:00:00Z", project_id="p", etype="tag",
                                              provider="git", ref="v1", summary="Tag v1")])
    assert [e["type"] for e in ledger.events("p", etype="tag")] == ["tag"]
    assert len(ledger.events("p", since="2026-09-05T00:00:00Z")) == 1


def test_schema_version_recorded(ledger):
    row = ledger.conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
    assert row["value"] == "1"


def test_purge_removes_project_data_only(ledger):
    other = make_event(ts="2026-09-01T00:00:00Z", project_id="q", etype="commit", provider="git", ref="z", summary="z")
    ledger.ingest([_event(), other])
    ledger.add_override("p", "rename", {"event": "x", "title": "t"})
    assert ledger.purge("p") == 1
    assert ledger.count("q") == 1 and ledger.overrides("p") == []


def test_persisted_ledger_reopens_with_data(tmp_path):
    path = tmp_path / "x.db"
    first = Ledger(path)
    first.ingest([_event()])
    first.close()
    second = Ledger(path)
    assert second.count("p") == 1
    second.close()

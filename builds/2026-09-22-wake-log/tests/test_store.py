from src.store import Store


def make_entry_kwargs(**overrides):
    defaults = dict(
        created_at="2026-10-04T12:00:00+00:00",
        location_name="Stony Lake",
        latitude=44.5,
        longitude=-78.2,
        target_date="2026-10-05",
        window_label="afternoon",
        score=78.5,
        beaufort=3,
        beaufort_name="Gentle Breeze",
        wind_knots=9.5,
        gust_knots=12.0,
        temp_c=21.0,
        precip_probability=10.0,
        cloud_cover=30.0,
        narrative="A fine afternoon on the water.",
        ai_polished=False,
    )
    defaults.update(overrides)
    return defaults


def test_save_and_get_roundtrip(tmp_path):
    with Store(str(tmp_path / "test.db")) as db:
        entry_id = db.save(**make_entry_kwargs())
        entry = db.get(entry_id)
        assert entry is not None
        assert entry.location_name == "Stony Lake"
        assert entry.narrative == "A fine afternoon on the water."
        assert entry.ai_polished is False


def test_get_returns_none_for_missing_id(tmp_path):
    with Store(str(tmp_path / "test.db")) as db:
        assert db.get(999) is None


def test_list_entries_orders_newest_first(tmp_path):
    with Store(str(tmp_path / "test.db")) as db:
        db.save(**make_entry_kwargs(created_at="2026-10-01T00:00:00+00:00", narrative="first"))
        db.save(**make_entry_kwargs(created_at="2026-10-03T00:00:00+00:00", narrative="third"))
        db.save(**make_entry_kwargs(created_at="2026-10-02T00:00:00+00:00", narrative="second"))
        entries = db.list_entries()
        assert [e.narrative for e in entries] == ["third", "second", "first"]


def test_list_entries_respects_limit(tmp_path):
    with Store(str(tmp_path / "test.db")) as db:
        for i in range(5):
            db.save(**make_entry_kwargs(created_at=f"2026-10-0{i+1}T00:00:00+00:00"))
        assert len(db.list_entries(limit=2)) == 2
        assert len(db.list_entries()) == 5


def test_search_matches_narrative_text(tmp_path):
    with Store(str(tmp_path / "test.db")) as db:
        db.save(**make_entry_kwargs(narrative="a gentle breeze off the point"))
        db.save(**make_entry_kwargs(narrative="storm conditions, stayed at the dock"))
        results = db.search("gentle")
        assert len(results) == 1
        assert "gentle" in results[0].narrative


def test_search_matches_location_name(tmp_path):
    with Store(str(tmp_path / "test.db")) as db:
        db.save(**make_entry_kwargs(location_name="Stony Lake"))
        db.save(**make_entry_kwargs(location_name="Georgian Bay"))
        results = db.search("Georgian")
        assert len(results) == 1
        assert results[0].location_name == "Georgian Bay"


def test_search_returns_empty_list_for_no_match(tmp_path):
    with Store(str(tmp_path / "test.db")) as db:
        db.save(**make_entry_kwargs())
        assert db.search("nonexistent-query-xyz") == []


def test_history_for_location_only_returns_matching_location(tmp_path):
    with Store(str(tmp_path / "test.db")) as db:
        db.save(**make_entry_kwargs(location_name="Stony Lake", narrative="entry A"))
        db.save(**make_entry_kwargs(location_name="Georgian Bay", narrative="entry B"))
        db.save(**make_entry_kwargs(location_name="Stony Lake", narrative="entry C"))
        history = db.history_for_location("Stony Lake")
        assert set(history) == {"entry A", "entry C"}


def test_entries_are_append_only_no_update_method_exists(tmp_path):
    with Store(str(tmp_path / "test.db")) as db:
        assert not hasattr(db, "update")
        assert not hasattr(db, "delete")


def test_schema_persists_across_reopening_same_file(tmp_path):
    db_path = str(tmp_path / "persist.db")
    with Store(db_path) as db:
        db.save(**make_entry_kwargs(narrative="persisted entry"))
    with Store(db_path) as db2:
        entries = db2.list_entries()
        assert len(entries) == 1
        assert entries[0].narrative == "persisted entry"

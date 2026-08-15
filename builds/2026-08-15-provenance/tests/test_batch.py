from unittest.mock import patch

import pytest

from src import batch, store

SEARCH_RESULTS = {
    "Acme Canadiana Ltd.": "Q1",
    "Globex Foreign Holdings": "Q2",
    # "Unknown Widget Co" deliberately absent — simulates a business Wikidata has never heard of.
}

CLAIMS_BY_QID = {
    "Q1": {"country": "Q16", "headquarters": None, "parent_org": None, "owned_by": None},  # Canada
    "Q2": {"country": "Q30", "headquarters": None, "parent_org": None, "owned_by": None},  # United States
}


def _fake_search_entity(name):
    return SEARCH_RESULTS.get(name)


def _fake_get_claims(qid):
    return CLAIMS_BY_QID.get(qid, {"country": None, "headquarters": None, "parent_org": None, "owned_by": None})


@pytest.fixture
def conn(tmp_path):
    db_path = str(tmp_path / "test_provenance.db")
    connection = store.connect(db_path)
    yield connection
    connection.close()


@pytest.fixture
def mocked_wikidata():
    with patch("src.batch.wikidata.search_entity", side_effect=_fake_search_entity) as search_mock, \
         patch("src.batch.wikidata.get_claims", side_effect=_fake_get_claims) as claims_mock:
        yield search_mock, claims_mock


def _sample_rows():
    return [
        {"name": "Acme Canadiana Ltd.", "website": "https://acme-canadiana.example"},
        {"name": "Globex Foreign Holdings", "website": "https://globex.example"},
        {"name": "Unknown Widget Co", "website": ""},
    ]


def test_classify_batch_produces_expected_verdict_distribution(conn, mocked_wikidata):
    output_rows, stats = batch.classify_batch(_sample_rows(), conn)
    assert stats["total"] == 3
    assert stats["canadian"] == 1
    assert stats["foreign"] == 1
    assert stats["uncertain"] == 1
    assert stats["cache_misses"] == 3
    assert stats["cache_hits"] == 0

    by_name = {row["name"]: row for row in output_rows}
    assert by_name["Acme Canadiana Ltd."]["verdict"] == "canadian"
    assert by_name["Globex Foreign Holdings"]["verdict"] == "foreign"
    assert by_name["Unknown Widget Co"]["verdict"] == "uncertain"


def test_second_run_over_same_rows_hits_cache_and_issues_no_new_queries(conn, mocked_wikidata):
    search_mock, claims_mock = mocked_wikidata
    batch.classify_batch(_sample_rows(), conn)
    first_call_count = search_mock.call_count

    output_rows, stats = batch.classify_batch(_sample_rows(), conn)

    assert stats["cache_hits"] == 3
    assert stats["cache_misses"] == 0
    assert search_mock.call_count == first_call_count  # no new Wikidata queries on the cached run
    by_name = {row["name"]: row for row in output_rows}
    assert by_name["Acme Canadiana Ltd."]["verdict"] == "canadian"


def test_refresh_flag_forces_re_resolution(conn, mocked_wikidata):
    search_mock, _ = mocked_wikidata
    batch.classify_batch(_sample_rows(), conn)
    first_call_count = search_mock.call_count

    batch.classify_batch(_sample_rows(), conn, refresh=True)

    assert search_mock.call_count > first_call_count
    history = store.get_history(conn, "Acme Canadiana Ltd.")
    assert len(history) == 2  # never overwritten — both versions preserved


def test_rows_missing_name_are_skipped_not_crashed(conn, mocked_wikidata):
    rows = _sample_rows() + [{"name": "", "website": "https://blank.example"}]
    output_rows, stats = batch.classify_batch(rows, conn)
    assert stats["skipped"] == 1
    assert stats["total"] == 3
    assert len(output_rows) == 3


def test_ai_enrich_only_called_for_uncertain_rows(conn, mocked_wikidata):
    with patch("src.batch.ai_enrich.enrich", return_value="ai note") as enrich_mock:
        batch.classify_batch(_sample_rows(), conn, ai_enrich_enabled=True, api_key="fake-key")

    calls = [call.args[0] for call in enrich_mock.call_args_list]
    assert calls == ["Unknown Widget Co"]  # the only uncertain business in the fixture


def test_output_csv_round_trip_preserves_input_columns_and_appends_verdict_columns(conn, mocked_wikidata, tmp_path):
    input_csv = tmp_path / "in.csv"
    input_csv.write_text("name,website,notes\nAcme Canadiana Ltd.,https://acme-canadiana.example,seed\n")

    rows = batch.read_input_csv(str(input_csv))
    output_rows, _stats = batch.classify_batch(rows, conn)

    out_csv = tmp_path / "out.csv"
    batch.write_output_csv(str(out_csv), output_rows, list(rows[0].keys()))

    written_rows = batch.read_input_csv(str(out_csv))
    assert written_rows[0]["name"] == "Acme Canadiana Ltd."
    assert written_rows[0]["notes"] == "seed"
    assert written_rows[0]["verdict"] == "canadian"
    assert "confidence" in written_rows[0]
    assert "evidence" in written_rows[0]

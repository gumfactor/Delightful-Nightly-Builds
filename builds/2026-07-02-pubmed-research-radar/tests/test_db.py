"""Tests for src/db.py — schema, dedup, CRUD, search, stats."""

import pytest

from src import db


@pytest.fixture
def conn(tmp_path):
    connection = db.connect(str(tmp_path / "test_radar.db"))
    yield connection
    connection.close()


SAMPLE_ARTICLE = {
    "pmid": "11111111",
    "title": "Amygdala reactivity predicts empathic accuracy",
    "authors": "Chen Y, Okafor A",
    "journal": "J Affect Neurosci",
    "pub_date": "2026 Jun 15",
    "abstract": "fMRI results show amygdala activity correlates with empathic accuracy.",
    "url": "https://pubmed.ncbi.nlm.nih.gov/11111111/",
}


class TestSchema:
    def test_connect_creates_tables_and_is_idempotent(self, tmp_path):
        db_path = str(tmp_path / "idempotent.db")
        conn1 = db.connect(db_path)
        conn1.close()
        conn2 = db.connect(db_path)  # should not raise on existing schema
        assert db.list_topics(conn2) == []
        conn2.close()


class TestTopics:
    def test_add_and_list_topic(self, conn):
        db.add_topic(conn, "Empathy", "empathy[tiab]")
        topics = db.list_topics(conn)
        assert len(topics) == 1
        assert topics[0]["name"] == "Empathy"
        assert topics[0]["query"] == "empathy[tiab]"

    def test_get_topic_by_name_missing_returns_none(self, conn):
        assert db.get_topic_by_name(conn, "Nonexistent") is None

    def test_remove_topic_deletes_topic_and_its_articles(self, conn):
        topic_id = db.add_topic(conn, "Empathy", "empathy[tiab]")
        db.upsert_article(conn, topic_id, SAMPLE_ARTICLE)

        removed = db.remove_topic(conn, "Empathy")

        assert removed is True
        assert db.list_topics(conn) == []
        assert db.get_stats(conn)["total"] == 0

    def test_remove_nonexistent_topic_returns_false(self, conn):
        assert db.remove_topic(conn, "Nope") is False


class TestArticleDedup:
    def test_upsert_new_article_returns_true(self, conn):
        topic_id = db.add_topic(conn, "Empathy", "empathy[tiab]")
        inserted = db.upsert_article(conn, topic_id, SAMPLE_ARTICLE)
        assert inserted is True
        assert db.get_stats(conn)["total"] == 1

    def test_upsert_same_pmid_twice_does_not_duplicate(self, conn):
        topic_id = db.add_topic(conn, "Empathy", "empathy[tiab]")
        db.upsert_article(conn, topic_id, SAMPLE_ARTICLE)
        inserted_again = db.upsert_article(conn, topic_id, SAMPLE_ARTICLE)

        assert inserted_again is False
        assert db.get_stats(conn)["total"] == 1


class TestScoring:
    def test_set_scoring_updates_article_fields(self, conn):
        topic_id = db.add_topic(conn, "Empathy", "empathy[tiab]")
        db.upsert_article(conn, topic_id, SAMPLE_ARTICLE)

        db.set_scoring(conn, "11111111", 8.5, "Great summary", "fMRI", "ai")

        articles = db.get_articles_by_topic(conn, topic_id)
        assert articles[0]["relevance_score"] == 8.5
        assert articles[0]["ai_summary"] == "Great summary"
        assert articles[0]["scoring_method"] == "ai"

    def test_get_unscored_articles_excludes_scored_ones(self, conn):
        topic_id = db.add_topic(conn, "Empathy", "empathy[tiab]")
        db.upsert_article(conn, topic_id, SAMPLE_ARTICLE)
        assert len(db.get_unscored_articles(conn)) == 1

        db.set_scoring(conn, "11111111", 5.0, None, None, "fallback")
        assert len(db.get_unscored_articles(conn)) == 0

    def test_articles_by_topic_sorted_by_relevance_descending(self, conn):
        topic_id = db.add_topic(conn, "Empathy", "empathy[tiab]")
        second_article = dict(SAMPLE_ARTICLE, pmid="22222222", title="Second article")
        db.upsert_article(conn, topic_id, SAMPLE_ARTICLE)
        db.upsert_article(conn, topic_id, second_article)
        db.set_scoring(conn, "11111111", 3.0, None, None, "fallback")
        db.set_scoring(conn, "22222222", 9.0, None, None, "fallback")

        articles = db.get_articles_by_topic(conn, topic_id)

        assert [a["pmid"] for a in articles] == ["22222222", "11111111"]


class TestSearch:
    def test_search_matches_title_case_insensitive(self, conn):
        topic_id = db.add_topic(conn, "Empathy", "empathy[tiab]")
        db.upsert_article(conn, topic_id, SAMPLE_ARTICLE)

        results = db.search_articles(conn, "AMYGDALA")

        assert len(results) == 1
        assert results[0]["pmid"] == "11111111"

    def test_search_matches_abstract(self, conn):
        topic_id = db.add_topic(conn, "Empathy", "empathy[tiab]")
        db.upsert_article(conn, topic_id, SAMPLE_ARTICLE)

        results = db.search_articles(conn, "fMRI results")

        assert len(results) == 1

    def test_search_no_match_returns_empty(self, conn):
        topic_id = db.add_topic(conn, "Empathy", "empathy[tiab]")
        db.upsert_article(conn, topic_id, SAMPLE_ARTICLE)

        assert db.search_articles(conn, "quantum gravity") == []


class TestStats:
    def test_stats_counts_total_and_per_topic(self, conn):
        topic_id = db.add_topic(conn, "Empathy", "empathy[tiab]")
        db.add_topic(conn, "Stress", "stress[tiab]")
        db.upsert_article(conn, topic_id, SAMPLE_ARTICLE)

        stats = db.get_stats(conn)

        assert stats["total"] == 1
        assert stats["unscored"] == 1
        names_to_counts = {entry["topic"]: entry["count"] for entry in stats["per_topic"]}
        assert names_to_counts == {"Empathy": 1, "Stress": 0}

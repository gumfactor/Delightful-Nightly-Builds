"""Tests for src/cli.py — argument wiring, using a temporary DB and mocked network calls."""

from unittest.mock import MagicMock, patch

import pytest

from src import db
from src.cli import main


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "cli_test.db")


class TestTopicsCommand:
    def test_topics_list_seeds_defaults_on_first_use(self, db_path, capsys):
        exit_code = main(["topics", "list", "--db", db_path])

        assert exit_code == 0
        output = capsys.readouterr().out
        assert "Affective Neuroscience" in output
        assert "Empathy" in output

    def test_topics_add_then_list_shows_new_topic(self, db_path, capsys):
        main(["topics", "add", "Custom Topic", "custom[tiab]", "--db", db_path])
        capsys.readouterr()

        main(["topics", "list", "--db", db_path])
        output = capsys.readouterr().out

        assert "Custom Topic" in output

    def test_topics_add_duplicate_name_fails(self, db_path):
        main(["topics", "add", "Custom Topic", "custom[tiab]", "--db", db_path])
        exit_code = main(["topics", "add", "Custom Topic", "other[tiab]", "--db", db_path])

        assert exit_code == 1

    def test_topics_remove_existing_topic_succeeds(self, db_path):
        main(["topics", "add", "Custom Topic", "custom[tiab]", "--db", db_path])
        exit_code = main(["topics", "remove", "Custom Topic", "--db", db_path])

        assert exit_code == 0

    def test_topics_remove_missing_topic_fails(self, db_path):
        exit_code = main(["topics", "remove", "Nonexistent", "--db", db_path])
        assert exit_code == 1


class TestFetchCommand:
    @patch("src.cli.score_article")
    @patch("src.cli.fetch_articles")
    @patch("src.cli.search_pmids")
    def test_fetch_seeds_topics_stores_articles_and_scores_them(
        self, mock_search, mock_fetch, mock_score, db_path, capsys
    ):
        mock_search.return_value = ["11111111"]
        mock_fetch.return_value = [
            {
                "pmid": "11111111",
                "title": "Test article",
                "authors": "Doe J",
                "journal": "J Test",
                "pub_date": "2026",
                "abstract": "An abstract.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/11111111/",
            }
        ]
        mock_score.return_value = MagicMock(
            relevance_score=7.5, ai_summary=None, methodology_tag=None, scoring_method="fallback"
        )

        exit_code = main(["fetch", "--db", db_path])

        assert exit_code == 0
        conn = db.connect(db_path)
        # The mocked search/fetch return the same PMID for every one of the 5 seeded
        # topics, but articles.pmid is the primary key, so the article is only ever
        # claimed by the first topic that encounters it - total stays at 1, not 5.
        assert db.get_stats(conn)["total"] == 1
        assert db.get_stats(conn)["unscored"] == 0
        conn.close()

    @patch("src.cli.fetch_articles")
    @patch("src.cli.search_pmids")
    def test_fetch_does_not_duplicate_on_second_run(self, mock_search, mock_fetch, db_path):
        mock_search.return_value = ["11111111"]
        mock_fetch.return_value = [
            {
                "pmid": "11111111",
                "title": "Test article",
                "authors": "Doe J",
                "journal": "J Test",
                "pub_date": "2026",
                "abstract": "An abstract.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/11111111/",
            }
        ]

        main(["fetch", "--db", db_path])
        main(["fetch", "--db", db_path])

        conn = db.connect(db_path)
        assert db.get_stats(conn)["total"] == 1
        conn.close()


class TestFetchNetworkFailure:
    @patch("src.cli.search_pmids")
    def test_fetch_skips_topic_on_pubmed_error_instead_of_crashing(self, mock_search, db_path, capsys):
        from src.pubmed import PubMedError

        mock_search.side_effect = PubMedError("simulated network policy rejection")

        exit_code = main(["fetch", "--db", db_path])

        assert exit_code == 0
        assert "Skipping" in capsys.readouterr().err


class TestReportCommand:
    def test_report_writes_html_file(self, db_path, tmp_path, capsys):
        output_path = tmp_path / "radar.html"

        exit_code = main(["report", "--db", db_path, "--output", str(output_path)])

        assert exit_code == 0
        assert output_path.exists()
        assert "PubMed Research Radar" in output_path.read_text(encoding="utf-8")


class TestSearchCommand:
    def test_search_reports_no_matches_on_empty_db(self, db_path, capsys):
        exit_code = main(["search", "empathy", "--db", db_path])

        assert exit_code == 0
        assert "No matches" in capsys.readouterr().out

    def test_search_finds_stored_article(self, db_path, capsys):
        conn = db.connect(db_path)
        topic_id = db.add_topic(conn, "Empathy", "empathy[tiab]")
        db.upsert_article(
            conn,
            topic_id,
            {
                "pmid": "11111111",
                "title": "Empathy and the brain",
                "authors": "Doe J",
                "journal": "J Test",
                "pub_date": "2026",
                "abstract": "Study of empathy.",
                "url": "https://pubmed.ncbi.nlm.nih.gov/11111111/",
            },
        )
        conn.close()

        exit_code = main(["search", "empathy", "--db", db_path])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Empathy and the brain" in output


class TestStatsCommand:
    def test_stats_on_empty_db_reports_zero(self, db_path, capsys):
        exit_code = main(["stats", "--db", db_path])
        output = capsys.readouterr().out

        assert exit_code == 0
        assert "Total articles: 0" in output


class TestArgumentErrors:
    def test_missing_subcommand_raises_systemexit(self, db_path):
        with pytest.raises(SystemExit):
            main([])

    def test_unknown_command_raises_systemexit(self, db_path):
        with pytest.raises(SystemExit):
            main(["bogus-command"])

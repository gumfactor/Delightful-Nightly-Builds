"""Tests for src/pubmed.py — esearch/efetch parsing, no live network calls."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.pubmed import PubMedError, fetch_articles, parse_efetch_xml, search_pmids

FIXTURES = Path(__file__).parent / "fixtures"


def _read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class TestSearchPmids:
    @patch("src.pubmed.requests.get")
    def test_returns_pmid_list_from_esearch_json(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "esearchresult": {"idlist": ["11111111", "22222222"]}
        }
        mock_get.return_value = mock_response

        pmids = search_pmids("empathy[tiab]", days=14, retmax=20)

        assert pmids == ["11111111", "22222222"]
        mock_response.raise_for_status.assert_called_once()

    @patch("src.pubmed.requests.get")
    def test_empty_result_set_returns_empty_list(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"esearchresult": {"idlist": []}}
        mock_get.return_value = mock_response

        assert search_pmids("nonexistent topic xyz", days=14, retmax=20) == []

    @patch("src.pubmed.requests.get")
    def test_malformed_response_raises_pubmed_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"unexpected": "shape"}
        mock_get.return_value = mock_response

        with pytest.raises(PubMedError):
            search_pmids("empathy[tiab]", days=14, retmax=20)

    @patch("src.pubmed.requests.get")
    def test_network_failure_raises_pubmed_error_not_raw_exception(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("simulated proxy rejection")

        with pytest.raises(PubMedError):
            search_pmids("empathy[tiab]", days=14, retmax=20)


class TestParseEfetchXml:
    def test_parses_two_articles_with_full_metadata(self):
        articles = parse_efetch_xml(_read_fixture("efetch_sample.xml"))

        assert len(articles) == 2
        first = articles[0]
        assert first["pmid"] == "11111111"
        assert "Amygdala reactivity" in first["title"]
        assert "amygdala activity correlates" in first["abstract"]
        assert first["authors"] == "Chen Y, Okafor A"
        assert first["journal"] == "J Affect Neurosci"
        assert first["pub_date"] == "2026 Jun 15"
        assert first["url"] == "https://pubmed.ncbi.nlm.nih.gov/11111111/"

    def test_handles_medline_date_fallback(self):
        articles = parse_efetch_xml(_read_fixture("efetch_sample.xml"))
        second = articles[1]
        assert second["pub_date"] == "2026 Spring"

    def test_truncates_author_list_beyond_three_with_et_al(self):
        articles = parse_efetch_xml(_read_fixture("efetch_sample.xml"))
        second = articles[1]
        assert second["authors"] == "Nowak R, Silva M, Park J et al."

    def test_decodes_xml_entities_in_title(self):
        articles = parse_efetch_xml(_read_fixture("efetch_sample.xml"))
        second = articles[1]
        assert "psychopathy & antisocial traits" in second["title"]

    def test_empty_article_set_returns_empty_list(self):
        assert parse_efetch_xml(_read_fixture("efetch_empty.xml")) == []

    def test_malformed_xml_raises_pubmed_error(self):
        with pytest.raises(PubMedError):
            parse_efetch_xml("<not><valid xml")

    def test_article_missing_pmid_is_skipped(self):
        xml = """<?xml version="1.0"?>
        <PubmedArticleSet>
          <PubmedArticle>
            <MedlineCitation>
              <Article><ArticleTitle>No PMID here</ArticleTitle></Article>
            </MedlineCitation>
          </PubmedArticle>
        </PubmedArticleSet>"""
        assert parse_efetch_xml(xml) == []


class TestFetchArticles:
    def test_returns_empty_list_without_calling_api_when_no_pmids(self):
        with patch("src.pubmed.requests.get") as mock_get:
            result = fetch_articles([])
        assert result == []
        mock_get.assert_not_called()

    @patch("src.pubmed.requests.get")
    def test_fetches_and_parses_articles_for_given_pmids(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = _read_fixture("efetch_sample.xml")
        mock_get.return_value = mock_response

        articles = fetch_articles(["11111111", "22222222"])

        assert len(articles) == 2
        called_params = mock_get.call_args.kwargs["params"]
        assert called_params["id"] == "11111111,22222222"

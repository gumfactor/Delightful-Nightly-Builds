import json
import urllib.error

import pytest

from src import pubmed_client


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


_SAMPLE_XML = b"""<?xml version="1.0"?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <Journal>
          <JournalIssue>
            <PubDate><Year>2022</Year></PubDate>
          </JournalIssue>
          <Title>Journal of Affective Science</Title>
        </Journal>
        <ArticleTitle>Empathy and Stress Reactivity in Adults</ArticleTitle>
        <Abstract>
          <AbstractText Label="BACKGROUND">Prior work links empathy to stress.</AbstractText>
          <AbstractText Label="METHODS">A sample of 64 adults (N=64) completed a survey, r = 0.42, p &lt; .01.</AbstractText>
        </Abstract>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>99999999</PMID>
      <Article>
        <Journal>
          <JournalIssue>
            <PubDate><MedlineDate>2019 Spring</MedlineDate></PubDate>
          </JournalIssue>
        </Journal>
        <ArticleTitle>A Study With No Abstract</ArticleTitle>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


def test_search_pmids_parses_idlist(monkeypatch):
    def fake_urlopen(url, timeout=None):
        body = json.dumps({"esearchresult": {"idlist": ["1", "2", "3"]}}).encode("utf-8")
        return _FakeResponse(body)

    monkeypatch.setattr(pubmed_client.urllib.request, "urlopen", fake_urlopen)
    result = pubmed_client.search_pmids("empathy stress", retmax=3)
    assert result == ["1", "2", "3"]


def test_search_pmids_raises_on_malformed_response(monkeypatch):
    def fake_urlopen(url, timeout=None):
        return _FakeResponse(json.dumps({"unexpected": "shape"}).encode("utf-8"))

    monkeypatch.setattr(pubmed_client.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(pubmed_client.PubMedError):
        pubmed_client.search_pmids("empathy")


def test_search_pmids_raises_on_network_error(monkeypatch):
    def fake_urlopen(url, timeout=None):
        raise urllib.error.URLError("blocked by proxy")

    monkeypatch.setattr(pubmed_client.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(pubmed_client.PubMedError):
        pubmed_client.search_pmids("empathy")


def test_fetch_articles_empty_pmid_list_returns_empty_without_network_call(monkeypatch):
    def fake_urlopen(*args, **kwargs):
        raise AssertionError("should never be called for an empty PMID list")

    monkeypatch.setattr(pubmed_client.urllib.request, "urlopen", fake_urlopen)
    assert pubmed_client.fetch_articles([]) == []


def test_fetch_articles_parses_title_abstract_journal_year(monkeypatch):
    def fake_urlopen(url, timeout=None):
        return _FakeResponse(_SAMPLE_XML)

    monkeypatch.setattr(pubmed_client.urllib.request, "urlopen", fake_urlopen)
    articles = pubmed_client.fetch_articles(["12345678", "99999999"])

    # The second article has no <Abstract> at all and must be skipped.
    assert len(articles) == 1
    article = articles[0]
    assert article.pmid == "12345678"
    assert article.title == "Empathy and Stress Reactivity in Adults"
    assert "Prior work links empathy to stress." in article.abstract
    assert "N=64" in article.abstract
    assert article.journal == "Journal of Affective Science"
    assert article.pub_year == 2022


def test_fetch_articles_skips_article_with_no_abstract():
    root_xml = b"""<PubmedArticleSet>
      <PubmedArticle><MedlineCitation><PMID>1</PMID>
        <Article><ArticleTitle>No Abstract Here</ArticleTitle></Article>
      </MedlineCitation></PubmedArticle>
    </PubmedArticleSet>"""
    import xml.etree.ElementTree as ET

    root = ET.fromstring(root_xml)
    article_elem = root.find(".//PubmedArticle")
    assert pubmed_client._parse_article(article_elem) is None


def test_fetch_articles_raises_on_unparseable_xml(monkeypatch):
    def fake_urlopen(url, timeout=None):
        return _FakeResponse(b"not xml at all <<<")

    monkeypatch.setattr(pubmed_client.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(pubmed_client.PubMedError):
        pubmed_client.fetch_articles(["1"])


def test_fetch_articles_raises_on_network_error(monkeypatch):
    def fake_urlopen(url, timeout=None):
        raise urllib.error.URLError("blocked by proxy")

    monkeypatch.setattr(pubmed_client.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(pubmed_client.PubMedError):
        pubmed_client.fetch_articles(["1"])


def test_medline_date_fallback_extracts_year():
    import xml.etree.ElementTree as ET

    xml_bytes = b"""<PubmedArticle><MedlineCitation><PMID>5</PMID>
      <Article>
        <Journal><JournalIssue><PubDate><MedlineDate>2019 Spring</MedlineDate></PubDate></JournalIssue></Journal>
        <ArticleTitle>Title</ArticleTitle>
        <Abstract><AbstractText>Some abstract text.</AbstractText></Abstract>
      </Article>
    </MedlineCitation></PubmedArticle>"""
    article_elem = ET.fromstring(xml_bytes)
    parsed = pubmed_client._parse_article(article_elem)
    assert parsed is not None
    assert parsed.pub_year == 2019

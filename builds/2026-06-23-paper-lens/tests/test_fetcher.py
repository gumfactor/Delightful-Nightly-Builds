"""Tests for fetcher.py — arXiv Atom feed parser."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fetcher import parse_atom_feed, build_query_url, _extract_arxiv_id, _parse_entry
import xml.etree.ElementTree as ET

ATOM_NS = "http://www.w3.org/2005/Atom"

_SINGLE_ENTRY_XML = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2410.00001v2</id>
    <title>  Neural Correlates of Empathy in Forensic Populations  </title>
    <summary>
      This study investigated empathy in psychopathic individuals.
      We used fMRI to measure brain activity during emotional tasks.
    </summary>
    <published>2024-10-15T00:00:00Z</published>
    <author><name>Alice Smith</name></author>
    <author><name>Bob Jones</name></author>
  </entry>
</feed>"""

_MULTI_ENTRY_XML = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2410.00001v1</id>
    <title>First Paper</title>
    <summary>Abstract one.</summary>
    <published>2024-10-01T00:00:00Z</published>
    <author><name>Alice</name></author>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2410.00002v1</id>
    <title>Second Paper</title>
    <summary>Abstract two.</summary>
    <published>2024-10-02T00:00:00Z</published>
    <author><name>Bob</name></author>
  </entry>
</feed>"""

_EMPTY_FEED_XML = b"""<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>"""


def test_parse_single_entry_returns_all_fields():
    papers = parse_atom_feed(_SINGLE_ENTRY_XML)
    assert len(papers) == 1
    p = papers[0]
    assert "arxiv_id" in p
    assert "title" in p
    assert "authors" in p
    assert "abstract" in p
    assert "published_date" in p


def test_parse_entry_strips_url_prefix_from_arxiv_id():
    papers = parse_atom_feed(_SINGLE_ENTRY_XML)
    assert "arxiv.org" not in papers[0]["arxiv_id"]
    assert "/abs/" not in papers[0]["arxiv_id"]


def test_parse_entry_strips_version_suffix_from_arxiv_id():
    papers = parse_atom_feed(_SINGLE_ENTRY_XML)
    # http://arxiv.org/abs/2410.00001v2 → 2410.00001
    assert papers[0]["arxiv_id"] == "2410.00001"


def test_parse_entry_joins_multiple_authors():
    papers = parse_atom_feed(_SINGLE_ENTRY_XML)
    assert "Alice Smith" in papers[0]["authors"]
    assert "Bob Jones" in papers[0]["authors"]
    assert "," in papers[0]["authors"]


def test_parse_entry_strips_whitespace_from_title_and_abstract():
    papers = parse_atom_feed(_SINGLE_ENTRY_XML)
    p = papers[0]
    assert not p["title"].startswith(" ")
    assert not p["title"].endswith(" ")
    assert not p["abstract"].startswith("\n")


def test_parse_empty_feed_returns_empty_list():
    papers = parse_atom_feed(_EMPTY_FEED_XML)
    assert papers == []


def test_parse_multiple_entries_returns_all():
    papers = parse_atom_feed(_MULTI_ENTRY_XML)
    assert len(papers) == 2
    ids = {p["arxiv_id"] for p in papers}
    assert "2410.00001" in ids
    assert "2410.00002" in ids


def test_build_query_url_includes_search_query():
    url = build_query_url("cat:q-bio.NC", 10)
    assert "search_query=" in url
    assert "q-bio.NC" in url


def test_build_query_url_includes_max_results():
    url = build_query_url("cat:cs.AI", 15)
    assert "max_results=15" in url


def test_extract_arxiv_id_strips_version():
    assert _extract_arxiv_id("http://arxiv.org/abs/2410.00001v3") == "2410.00001"


def test_extract_arxiv_id_handles_no_version():
    assert _extract_arxiv_id("http://arxiv.org/abs/2410.00001") == "2410.00001"

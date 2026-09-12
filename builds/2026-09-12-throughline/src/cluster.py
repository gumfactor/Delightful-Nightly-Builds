"""Fully deterministic, stdlib-only thematic clustering of a paper corpus.

Approach: corpus-wide TF-IDF-style keyword scoring per paper, then a
Jaccard-similarity union-find over each paper's top-keyword set. No external
ML libraries — every step is small enough to hand-verify (see BUILD_LOG.md
for a worked example cross-check).
"""
from __future__ import annotations

import math
import re
from collections import Counter

STOPWORDS = frozenset(
    """
    a about above after again against all am an and any are aren't as at be
    because been before being below between both but by can can't cannot
    could couldn't did didn't do does doesn't doing don't down during each
    few for from further had hadn't has hasn't have haven't having he he'd
    he'll he's her here here's hers herself him himself his how how's i i'd
    i'll i'm i've if in into is isn't it it's its itself let's me more most
    mustn't my myself no nor not of off on once only or other ought our ours
    ourselves out over own same shan't she she'd she'll she's should
    shouldn't so some such than that that's the their theirs them themselves
    then there there's these they they'd they'll they're they've this those
    through to too under until up very was wasn't we we'd we'll we're we've
    were weren't what what's when when's where where's which while who who's
    whom why why's with won't would wouldn't you you'd you'll you're you've
    your yours yourself yourselves using use used study paper results data
    based new can may also however between within across among these those
    """.split()
)

TOKEN_RE = re.compile(r"[a-z][a-z\-]{2,}")


def tokenize(text: str) -> list:
    if not text:
        return []
    tokens = TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in STOPWORDS]


def _idf(term: str, doc_freq: dict, n_docs: int) -> float:
    df = doc_freq.get(term, 0)
    return math.log((n_docs + 1) / (df + 1)) + 1.0


def top_keywords_for_paper(
    term_freq: Counter, doc_freq: dict, n_docs: int, top_n: int = 6
) -> list:
    scored = [
        (term, count * _idf(term, doc_freq, n_docs)) for term, count in term_freq.items()
    ]
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return [term for term, _ in scored[:top_n]]


def _field(paper, name):
    """Read a field from either a dataclass (attribute access) or a
    mapping-like object such as sqlite3.Row (`paper[name]`)."""
    if hasattr(paper, "keys"):
        try:
            return paper[name]
        except (KeyError, IndexError):
            return None
    return getattr(paper, name, None)


def _paper_text(paper) -> str:
    title = _field(paper, "title") or ""
    abstract = _field(paper, "abstract")
    return f"{title} {abstract or ''}"


def _paper_id(paper) -> str:
    return _field(paper, "paper_id")


class _UnionFind:
    def __init__(self, items):
        self.parent = {item: item for item in items}

    def find(self, item):
        root = item
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[item] != root:
            self.parent[item], item = root, self.parent[item]
        return root

    def union(self, a, b):
        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            self.parent[root_b] = root_a


def cluster_papers(papers: list, top_n: int = 6, similarity_threshold: float = 0.2) -> list:
    """Group papers into thematic clusters.

    Returns a list of {"label": str, "keywords": [str], "paper_ids": [str]}
    dicts, sorted largest-first then alphabetically by label for stable,
    reproducible output on an unchanged corpus.
    """
    if not papers:
        return []

    paper_ids = [_paper_id(p) for p in papers]
    texts = {pid: _paper_text(p) for pid, p in zip(paper_ids, papers)}
    term_freqs = {pid: Counter(tokenize(text)) for pid, text in texts.items()}

    doc_freq: dict = {}
    for tf in term_freqs.values():
        for term in tf:
            doc_freq[term] = doc_freq.get(term, 0) + 1

    n_docs = len(papers)
    keywords = {
        pid: top_keywords_for_paper(term_freqs[pid], doc_freq, n_docs, top_n)
        for pid in paper_ids
    }

    uf = _UnionFind(paper_ids)
    for i in range(len(paper_ids)):
        for j in range(i + 1, len(paper_ids)):
            a, b = paper_ids[i], paper_ids[j]
            set_a, set_b = set(keywords[a]), set(keywords[b])
            if not set_a or not set_b:
                continue
            jaccard = len(set_a & set_b) / len(set_a | set_b)
            if jaccard >= similarity_threshold:
                uf.union(a, b)

    groups: dict = {}
    for pid in paper_ids:
        groups.setdefault(uf.find(pid), []).append(pid)

    clusters = []
    for member_ids in groups.values():
        vote = Counter()
        for pid in member_ids:
            for term in keywords[pid]:
                vote[term] += term_freqs[pid][term] * _idf(term, doc_freq, n_docs)
        ranked = sorted(vote.items(), key=lambda pair: (-pair[1], pair[0]))
        label_terms = [term for term, _ in ranked[:3]] or ["(uncategorized)"]
        all_keywords = [term for term, _ in ranked]
        clusters.append(
            {
                "label": " / ".join(label_terms),
                "keywords": all_keywords,
                "paper_ids": sorted(member_ids, key=paper_ids.index),
            }
        )

    clusters.sort(key=lambda c: (-len(c["paper_ids"]), c["label"]))
    return clusters

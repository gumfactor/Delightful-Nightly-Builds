from collections import Counter

from src import cluster as cluster_mod
from src.semantic_scholar import Paper


def make_paper(paper_id, title, abstract=None):
    return Paper(paper_id, title, abstract, None, None, 0, None)


def test_tokenize_lowercases_strips_stopwords_and_short_tokens():
    text = "The Cat sat on a mat, using real data."
    # "the"/"using"/"data" are stopwords; "on"/"a" are below the 3-char minimum.
    assert cluster_mod.tokenize(text) == ["cat", "sat", "mat", "real"]


def test_tokenize_empty_string_returns_empty_list():
    assert cluster_mod.tokenize("") == []
    assert cluster_mod.tokenize(None) == []


def test_top_keywords_for_paper_orders_by_score_then_alphabetically():
    # All three terms have identical document frequency (1), so ranking is
    # purely by term frequency, with alphabetical order breaking ties.
    term_freq = Counter({"alpha": 3, "beta": 1, "gamma": 1})
    doc_freq = {"alpha": 1, "beta": 1, "gamma": 1}
    result = cluster_mod.top_keywords_for_paper(term_freq, doc_freq, n_docs=1, top_n=3)
    assert result == ["alpha", "beta", "gamma"]


def test_cluster_papers_empty_list():
    assert cluster_mod.cluster_papers([]) == []


def test_cluster_papers_single_paper_forms_one_cluster():
    papers = [make_paper("p1", "Alpha Bravo Charlie")]
    clusters = cluster_mod.cluster_papers(papers, top_n=4)
    assert len(clusters) == 1
    assert clusters[0]["paper_ids"] == ["p1"]
    assert len(clusters[0]["keywords"]) > 0


def test_cluster_papers_groups_by_hand_verified_jaccard_overlap():
    # Hand-verified overlap (see BUILD_LOG.md): with top_n=4 every paper's
    # 4 unique words are all taken, so no TF-IDF tie-break ambiguity affects
    # which words are "top" - only the Jaccard math below applies.
    # P1 & P3 share {alpha, bravo} -> Jaccard 2/6 = 0.333 (merge, >= 0.2)
    # P1 & P2 share {delta}        -> Jaccard 1/7 = 0.143 (no merge)
    # P2 & P3 share {}             -> Jaccard 0            (no merge)
    p1 = make_paper("p1", "Alpha Bravo Charlie Delta")
    p2 = make_paper("p2", "Delta Hotel India Juliet")
    p3 = make_paper("p3", "Alpha Bravo Echo Foxtrot")

    clusters = cluster_mod.cluster_papers([p1, p2, p3], top_n=4, similarity_threshold=0.2)

    assert len(clusters) == 2
    sizes = sorted(len(c["paper_ids"]) for c in clusters)
    assert sizes == [1, 2]

    pair_cluster = next(c for c in clusters if len(c["paper_ids"]) == 2)
    singleton_cluster = next(c for c in clusters if len(c["paper_ids"]) == 1)
    assert set(pair_cluster["paper_ids"]) == {"p1", "p3"}
    assert singleton_cluster["paper_ids"] == ["p2"]


def test_cluster_papers_below_threshold_stays_singletons():
    p1 = make_paper("p1", "Alpha Bravo Charlie Delta")
    p2 = make_paper("p2", "Delta Hotel India Juliet")
    # Same pair as above but with a stricter threshold than their 0.143 overlap.
    clusters = cluster_mod.cluster_papers([p1, p2], top_n=4, similarity_threshold=0.2)
    assert len(clusters) == 2
    assert all(len(c["paper_ids"]) == 1 for c in clusters)


def test_cluster_papers_is_deterministic_across_runs():
    papers = [
        make_paper("p1", "Cortisol Reactivity to Acute Stress",
                   "We measured cortisol reactivity following acute psychosocial stress exposure in adults."),
        make_paper("p2", "Stress Coping and Cortisol Response",
                   "This study examines coping strategies and cortisol response to stress in a community sample."),
        make_paper("p3", "Regex Pattern Matching for Log Analysis",
                   "We propose a regex based pattern matching approach for analyzing log files efficiently."),
    ]
    first_run = cluster_mod.cluster_papers(papers)
    second_run = cluster_mod.cluster_papers(papers)
    assert first_run == second_run


def test_cluster_papers_realistic_corpus_groups_by_theme():
    # Full hand-verified worked example, see BUILD_LOG.md for the arithmetic:
    # the two stress/cortisol papers share {cortisol, stress} (Jaccard 0.2),
    # the two regex papers share {matching, pattern} (Jaccard 0.2), and the
    # boat-design paper shares nothing with either group.
    stress_a = make_paper(
        "stress_a", "Cortisol Reactivity to Acute Stress",
        "We measured cortisol reactivity following acute psychosocial stress exposure in adults.",
    )
    stress_b = make_paper(
        "stress_b", "Stress Coping and Cortisol Response",
        "This study examines coping strategies and cortisol response to stress in a community sample.",
    )
    regex_a = make_paper(
        "regex_a", "Regex Pattern Matching for Log Analysis",
        "We propose a regex based pattern matching approach for analyzing log files efficiently.",
    )
    regex_b = make_paper(
        "regex_b", "Automated Pattern Matching with Regular Expressions",
        "This paper presents automated regex pattern matching techniques for text extraction.",
    )
    boat = make_paper(
        "boat", "Boat Hull Design Optimization",
        "We explore boat hull design optimization for improved fuel efficiency.",
    )

    clusters = cluster_mod.cluster_papers([stress_a, stress_b, regex_a, regex_b, boat])

    assert len(clusters) == 3
    groups = {frozenset(c["paper_ids"]) for c in clusters}
    assert frozenset({"stress_a", "stress_b"}) in groups
    assert frozenset({"regex_a", "regex_b"}) in groups
    assert frozenset({"boat"}) in groups


def test_cluster_papers_accepts_plain_dict_rows():
    # storage.list_papers() returns sqlite3.Row objects, which -- like plain
    # dicts -- expose .keys()/[] but not attribute access; verify both work.
    rows = [
        {"paper_id": "d1", "title": "Alpha Bravo Charlie", "abstract": None},
        {"paper_id": "d2", "title": "Alpha Bravo Delta", "abstract": None},
    ]
    clusters = cluster_mod.cluster_papers(rows, top_n=3, similarity_threshold=0.2)
    assert len(clusters) == 1
    assert set(clusters[0]["paper_ids"]) == {"d1", "d2"}

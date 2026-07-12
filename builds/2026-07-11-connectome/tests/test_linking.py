import linking


def test_score_pair_no_shared_concepts_returns_zero():
    score, shared = linking.score_pair(
        {"golf": 1.0}, {"sourdough": 1.0}, doc_freq={"golf": 1, "sourdough": 1}, total_notes=2
    )
    assert score == 0.0
    assert shared == []


def test_score_pair_rarer_shared_concept_scores_higher():
    doc_freq = {"common": 10, "rare": 1}
    score_common, _ = linking.score_pair(
        {"common": 1.0}, {"common": 1.0}, doc_freq=doc_freq, total_notes=10
    )
    score_rare, _ = linking.score_pair(
        {"rare": 1.0}, {"rare": 1.0}, doc_freq=doc_freq, total_notes=10
    )
    assert score_rare > score_common


def test_score_pair_shared_concepts_sorted_by_contribution_descending():
    doc_freq = {"rare": 1, "common": 20}
    _, shared = linking.score_pair(
        {"rare": 1.0, "common": 1.0},
        {"rare": 1.0, "common": 1.0},
        doc_freq=doc_freq,
        total_notes=20,
    )
    assert shared[0] == "rare"


def test_compute_links_produces_no_self_links():
    note_concepts = {1: {"a": 1.0}, 2: {"a": 1.0}}
    doc_freq = {"a": 2}
    links = linking.compute_links(note_concepts, doc_freq, total_notes=2)
    for link in links:
        assert link.note_a != link.note_b


def test_compute_links_symmetric_ordering():
    note_concepts = {5: {"a": 1.0}, 2: {"a": 1.0}}
    doc_freq = {"a": 2}
    links = linking.compute_links(note_concepts, doc_freq, total_notes=2)
    assert len(links) == 1
    assert links[0].note_a < links[0].note_b


def test_compute_links_excludes_pairs_with_no_shared_concepts():
    note_concepts = {1: {"golf": 1.0}, 2: {"sourdough": 1.0}, 3: {"golf": 1.0}}
    doc_freq = {"golf": 2, "sourdough": 1}
    links = linking.compute_links(note_concepts, doc_freq, total_notes=3)
    pairs = {(link.note_a, link.note_b) for link in links}
    assert (1, 3) in pairs
    assert (1, 2) not in pairs
    assert (2, 3) not in pairs


def test_related_to_orients_results_with_query_note_first():
    links = [linking.Link(1, 2, 0.5, ["a"])]
    related = linking.related_to(2, links)
    assert related[0].note_a == 2
    assert related[0].note_b == 1


def test_related_to_returns_empty_for_note_with_no_links():
    links = [linking.Link(1, 2, 0.5, ["a"])]
    assert linking.related_to(99, links) == []


def test_related_to_respects_top_n():
    links = [linking.Link(1, i, float(i), ["a"]) for i in range(2, 10)]
    related = linking.related_to(1, links, top_n=3)
    assert len(related) == 3
    scores = [link.score for link in related]
    assert scores == sorted(scores, reverse=True)

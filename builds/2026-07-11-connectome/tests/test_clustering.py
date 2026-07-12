import json
import urllib.error
from unittest.mock import MagicMock, patch

import clustering
import linking


def test_compute_clusters_empty_notes_returns_empty_dict():
    assert clustering.compute_clusters([], []) == {}


def test_compute_clusters_single_note_no_links_is_its_own_cluster():
    notes = [{"id": 1}]
    clusters = clustering.compute_clusters(notes, [])
    assert clusters == {1: 1}


def test_compute_clusters_groups_notes_above_threshold():
    notes = [{"id": 1}, {"id": 2}]
    links = [linking.Link(1, 2, 0.8, ["a"])]
    clusters = clustering.compute_clusters(notes, links, threshold=0.5)
    assert clusters[1] == clusters[2]


def test_compute_clusters_keeps_notes_separate_below_threshold():
    notes = [{"id": 1}, {"id": 2}]
    links = [linking.Link(1, 2, 0.2, ["a"])]
    clusters = clustering.compute_clusters(notes, links, threshold=0.5)
    assert clusters[1] != clusters[2]


def test_compute_clusters_is_transitive_through_a_shared_member():
    # A-B strong, B-C strong, no direct A-C link — all three should still
    # end up in the same cluster via B.
    notes = [{"id": 1}, {"id": 2}, {"id": 3}]
    links = [
        linking.Link(1, 2, 0.9, ["a"]),
        linking.Link(2, 3, 0.9, ["b"]),
    ]
    clusters = clustering.compute_clusters(notes, links, threshold=0.5)
    assert clusters[1] == clusters[2] == clusters[3]


def test_compute_clusters_default_threshold_is_the_median_score():
    # Scores [0.2, 0.5, 0.8] -> median 0.5. Only the 0.5 and 0.8 links qualify.
    notes = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]
    links = [
        linking.Link(1, 2, 0.2, ["a"]),
        linking.Link(2, 3, 0.5, ["b"]),
        linking.Link(3, 4, 0.8, ["c"]),
    ]
    clusters = clustering.compute_clusters(notes, links)
    assert clusters[1] != clusters[2]
    assert clusters[2] == clusters[3] == clusters[4]


def test_cluster_members_groups_by_root():
    clusters = {1: 1, 2: 1, 3: 3}
    members = clustering.cluster_members(clusters)
    assert sorted(members[1]) == [1, 2]
    assert members[3] == [3]


def test_cluster_top_terms_ranks_by_summed_weight_and_respects_cap():
    note_concepts = {
        1: {"rare": 5.0, "common": 1.0},
        2: {"rare": 5.0, "other": 2.0, "extra": 0.5},
    }
    top = clustering.cluster_top_terms([1, 2], note_concepts)
    assert top[0] == "rare"
    assert len(top) <= clustering.MAX_NAME_CONCEPTS


def test_name_clusters_deterministic_joins_top_terms_title_cased():
    clusters = {1: 1, 2: 1}
    note_concepts = {1: {"workflow": 3.0}, 2: {"context": 2.0}}
    names = clustering.name_clusters_deterministic(clusters, note_concepts)
    assert names[1] == "Workflow / Context"


def test_name_clusters_deterministic_uses_uncategorized_when_no_concepts():
    clusters = {1: 1}
    names = clustering.name_clusters_deterministic(clusters, {})
    assert names[1] == clustering.UNCATEGORIZED


def test_relabel_with_claude_returns_deterministic_unchanged_without_api_key():
    deterministic = {1: "Workflow / Context"}
    result = clustering.relabel_with_claude(deterministic, {1: ["workflow", "context"]}, api_key=None)
    assert result == deterministic


def _mock_response(status, body_dict):
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.read.return_value = json.dumps(body_dict).encode("utf-8")
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = False
    return mock_response


def test_relabel_with_claude_uses_ai_names_on_full_success():
    deterministic = {1: "Workflow / Context", 2: "Golf / Swing"}
    terms = {1: ["workflow", "context"], 2: ["golf", "swing"]}
    fake = _mock_response(200, {
        "content": [{"text": json.dumps({"1": "AI Agent Workflows", "2": "Golf Technique"})}]
    })
    with patch("clustering.urllib.request.urlopen", return_value=fake):
        result = clustering.relabel_with_claude(deterministic, terms, api_key="fake-key")
    assert result == {1: "AI Agent Workflows", 2: "Golf Technique"}


def test_relabel_with_claude_falls_back_per_cluster_on_partial_response():
    deterministic = {1: "Workflow / Context", 2: "Golf / Swing"}
    terms = {1: ["workflow", "context"], 2: ["golf", "swing"]}
    # Response only names cluster 1; cluster 2 must keep its deterministic name.
    fake = _mock_response(200, {"content": [{"text": json.dumps({"1": "AI Agent Workflows"})}]})
    with patch("clustering.urllib.request.urlopen", return_value=fake):
        result = clustering.relabel_with_claude(deterministic, terms, api_key="fake-key")
    assert result[1] == "AI Agent Workflows"
    assert result[2] == "Golf / Swing"


def test_relabel_with_claude_falls_back_entirely_on_network_error():
    deterministic = {1: "Workflow / Context"}
    with patch("clustering.urllib.request.urlopen", side_effect=urllib.error.URLError("blocked")):
        result = clustering.relabel_with_claude(deterministic, {1: ["workflow"]}, api_key="fake-key")
    assert result == deterministic


def test_relabel_with_claude_falls_back_entirely_on_malformed_json():
    deterministic = {1: "Workflow / Context"}
    fake = _mock_response(200, {"content": [{"text": "not json ["}]})
    with patch("clustering.urllib.request.urlopen", return_value=fake):
        result = clustering.relabel_with_claude(deterministic, {1: ["workflow"]}, api_key="fake-key")
    assert result == deterministic


def test_relabel_with_claude_falls_back_entirely_on_non_200_status():
    deterministic = {1: "Workflow / Context"}
    fake = _mock_response(500, {})
    with patch("clustering.urllib.request.urlopen", return_value=fake):
        result = clustering.relabel_with_claude(deterministic, {1: ["workflow"]}, api_key="fake-key")
    assert result == deterministic


def test_assign_subcategories_empty_notes_returns_empty_dict():
    assert clustering.assign_subcategories([], [], {}) == {}


def test_assign_subcategories_without_api_key_uses_deterministic_names():
    notes = [{"id": 1}, {"id": 2}]
    links = [linking.Link(1, 2, 0.9, ["a"])]
    note_concepts = {1: {"workflow": 3.0}, 2: {"context": 2.0}}
    result = clustering.assign_subcategories(notes, links, note_concepts)
    assert result[1] == result[2] == "Workflow / Context"


def test_assign_subcategories_with_api_key_uses_relabeled_names():
    notes = [{"id": 1}, {"id": 2}]
    links = [linking.Link(1, 2, 0.9, ["a"])]
    note_concepts = {1: {"workflow": 3.0}, 2: {"context": 2.0}}
    root = clustering.compute_clusters(notes, links)[1]
    fake = _mock_response(200, {"content": [{"text": json.dumps({str(root): "AI Workflows"})}]})
    with patch("clustering.urllib.request.urlopen", return_value=fake):
        result = clustering.assign_subcategories(notes, links, note_concepts, api_key="fake-key")
    assert result[1] == result[2] == "AI Workflows"

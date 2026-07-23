from src.duplicates import (
    find_all_duplicate_clusters,
    find_exact_duplicate_clusters,
    find_near_duplicate_clusters,
)
from src.qc_engine import RowRecord

HEADER = ["business_name", "category", "province", "website"]


def make_record(index, name, province="ON", website="example.ca", category="Retail"):
    return RowRecord(
        row_index=index,
        raw_fields={
            "business_name": name,
            "category": category,
            "province": province,
            "website": website,
        },
        flags=[],
    )


def test_find_exact_duplicate_clusters_groups_identical_rows():
    records = [
        make_record(1, "Acme Co", website="acme.ca"),
        make_record(2, "Acme Co", website="acme.ca"),
        make_record(3, "Beta Inc", website="beta.ca"),
    ]
    clusters = find_exact_duplicate_clusters(records, HEADER)
    assert len(clusters) == 1
    assert clusters[0].row_indices == [1, 2]
    assert clusters[0].match_basis == "exact_row"
    assert clusters[0].similarity_score == 1.0


def test_find_exact_duplicate_clusters_no_false_positive():
    records = [make_record(1, "Acme Co"), make_record(2, "Beta Inc")]
    assert find_exact_duplicate_clusters(records, HEADER) == []


def test_find_near_duplicate_clusters_by_legal_suffix_and_province():
    records = [
        make_record(1, "Northern Lights Bakery Inc", province="ON", website="nlbakery.ca"),
        make_record(2, "Northern Lights Bakery", province="ON", website="nlbakery.com"),
    ]
    clusters = find_near_duplicate_clusters(records, HEADER)
    assert len(clusters) == 1
    assert clusters[0].row_indices == [1, 2]
    assert clusters[0].similarity_score >= 0.85


def test_find_near_duplicate_clusters_requires_corroboration():
    # Similar name but different province AND different website domain — no corroboration.
    records = [
        make_record(1, "Northern Lights Bakery", province="ON", website="nlbakery.ca"),
        make_record(2, "Northern Lights Bakery", province="BC", website="totallydifferent.ca"),
    ]
    clusters = find_near_duplicate_clusters(records, HEADER)
    assert clusters == []


def test_find_near_duplicate_clusters_no_false_positive_for_distinct_names():
    records = [
        make_record(1, "Riverside Print Shop", province="YT"),
        make_record(2, "Maple Ridge Roasters", province="YT"),
    ]
    clusters = find_near_duplicate_clusters(records, HEADER)
    assert clusters == []


def test_find_near_duplicate_clusters_by_website_domain():
    records = [
        make_record(1, "Acme Hardware Co", province="ON", website="acmehardware.ca"),
        make_record(2, "Acme Hardware", province="BC", website="acmehardware.ca"),
    ]
    clusters = find_near_duplicate_clusters(records, HEADER)
    assert len(clusters) == 1
    assert clusters[0].row_indices == [1, 2]


def test_find_all_duplicate_clusters_does_not_double_count_exact_matches():
    records = [
        make_record(1, "Acme Co", website="acme.ca"),
        make_record(2, "Acme Co", website="acme.ca"),
    ]
    clusters = find_all_duplicate_clusters(records, HEADER)
    assert len(clusters) == 1
    assert clusters[0].match_basis == "exact_row"

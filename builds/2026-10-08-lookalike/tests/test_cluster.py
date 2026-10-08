import unittest

from tests.helpers import rec
from lookalike import cluster
from lookalike.cluster import Decisions, DecisionsError, analyze, parse_decisions


def trio():
    a = rec("1", name="Maple Hearth Bakery", website="maplehearth.ca", phone="416-555-0101",
            address="12 Queen St W", postal_code="M5H 2N2", province="ON", city="Toronto", category="Bakery")
    b = rec("2", name="Maple Hearth Bakery Inc.", website="https://www.maplehearth.ca", phone="(416) 555-0101",
            address="12 Queen Street West", postal_code="M5H2N2", province="ON", city="Toronto", category="Cafe",
            email="hi@maplehearth.ca")
    c = rec("3", name="Mapel Hearth Bakry", phone="416 555 0101", province="ON", city="Toronto")
    return a, b, c


class ClusterTests(unittest.TestCase):
    def test_duplicates_cluster_and_review_pair_remains(self):
        analysis = analyze(list(trio()))
        merged = [c for c in analysis.clusters if c.status == "merged"]
        self.assertEqual([c.members for c in merged], [["1", "2"]])
        self.assertEqual({frozenset((p.a, p.b)) for p in analysis.review_pairs},
                         {frozenset(("1", "3")), frozenset(("2", "3"))})

    def test_same_decision_pulls_row_into_cluster(self):
        analysis = analyze(list(trio()), Decisions(same={frozenset(("1", "3"))}))
        self.assertEqual(sorted(analysis.clusters[0].members), ["1", "2", "3"])

    def test_different_decision_removes_pair(self):
        a, b, c = trio()
        analysis = analyze([a, b], Decisions(different={frozenset(("1", "2"))}))
        self.assertEqual(analysis.clusters, [])

    def test_different_decision_contradicted_by_chain_flags_cluster(self):
        a, b, c = trio()
        decisions = Decisions(same={frozenset(("1", "2")), frozenset(("2", "3"))}, different={frozenset(("1", "3"))})
        analysis = analyze([a, b, c], decisions)
        self.assertEqual(analysis.clusters[0].status, "needs_review")
        self.assertTrue(any(f.startswith("decision_conflict") for f in analysis.clusters[0].flags))

    def test_weak_chain_is_not_auto_merged(self):
        a = rec("a", name="Alpha Print Shop", phone="613-555-0100", website="alphaprint.ca", province="ON")
        b = rec("b", name="Alpha Print Shop", phone="613-555-0100", website="alphaprint.ca",
                email="x@alphaprint.ca", address="1 Main St", postal_code="K1A 0A1")
        c = rec("c", name="Alpha Print Shop", email="x@alphaprint.ca", address="1 Main St", postal_code="K1A 0A1",
                province="BC")
        analysis = analyze([a, b, c])
        flagged = [cl for cl in analysis.clusters if cl.status == "needs_review"]
        self.assertTrue(flagged and any(f.startswith("weak_chain") for f in flagged[0].flags))
        self.assertEqual(flagged[0].merged, {})

    def test_survivorship_prefers_frequent_then_complete_and_records_provenance(self):
        a, b, _c = trio()
        merged, provenance, representative = cluster.merge_records([a, b])
        self.assertEqual(merged["email"], "hi@maplehearth.ca")
        self.assertEqual(provenance["email"], "2")
        self.assertEqual(set(merged["category"].split("; ")), {"Bakery", "Cafe"})
        self.assertEqual(provenance["category"], "union")
        self.assertIn(representative, {"1", "2"})

    def test_decisions_parsing_validation(self):
        parsed = parse_decisions({"same": [["1", "2"]], "different": [[3, 4]]})
        self.assertIn(frozenset(("3", "4")), parsed.different)
        with self.assertRaises(DecisionsError):
            parse_decisions({"same": [["1", "2"]], "different": [["2", "1"]]})
        with self.assertRaises(DecisionsError):
            parse_decisions({"same": [["1"]]})
        with self.assertRaises(DecisionsError):
            parse_decisions([])


if __name__ == "__main__":
    unittest.main()

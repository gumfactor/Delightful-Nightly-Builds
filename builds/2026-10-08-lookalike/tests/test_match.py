import unittest

from tests.helpers import rec
from lookalike import match


class MatchTests(unittest.TestCase):
    def setUp(self):
        self.base = rec("1", name="Maple Leaf Bakery", website="https://www.mapleleaf.ca", phone="416-555-0100",
                        address="12 Queen St W", city="Toronto", province="ON", postal_code="M5H 2N2")

    def test_formatting_variants_are_duplicates(self):
        other = rec("2", name="Maple Leaf Bakery Inc.", website="mapleleaf.ca/contact", phone="(416) 555-0100",
                    address="12 Queen Street West, Suite 3", city="Toronto", province="Ontario", postal_code="m5h2n2")
        result = match.score_pair(self.base, other)
        self.assertEqual(result.label, "duplicate")
        self.assertTrue(any("same phone" in r[0] for r in result.reasons))

    def test_same_brand_other_city_is_branch_not_duplicate(self):
        branch = rec("3", name="Maple Leaf Bakery", website="https://www.mapleleaf.ca", phone="905-555-0199",
                     address="900 Main St", city="Mississauga", province="ON", postal_code="L5B 1A1")
        self.assertEqual(match.score_pair(self.base, branch).label, "branch")

    def test_same_name_different_domains_and_provinces_is_distinct(self):
        far = rec("4", name="Maple Leaf Bakery", website="https://mapleleafbakes.ca", phone="604-555-0111",
                  address="1 Robson St", city="Vancouver", province="BC", postal_code="V6G 1C3")
        self.assertEqual(match.score_pair(self.base, far).label, "distinct")

    def test_typo_name_plus_phone_only_goes_to_review(self):
        weak = rec("5", name="Mapel Leaf Bakry", phone="416-555-0100", province="ON")
        self.assertEqual(match.score_pair(self.base, weak).label, "review")

    def test_different_unit_same_building_penalized(self):
        a = rec("6", name="Dr Lee Dental", address="Suite 100, 50 King St", postal_code="M5H 1A1", province="ON")
        b = rec("7", name="Dr Lee Dental", address="Suite 200, 50 King St", postal_code="M5H 1A1", province="ON")
        result = match.score_pair(a, b)
        self.assertTrue(any("different units" in r[0] for r in result.reasons))

    def test_blocking_finds_phone_pair_with_dissimilar_names_but_skips_unrelated(self):
        a = rec("a", name="Zeta Plumbing", phone="613-555-0100")
        b = rec("b", name="Quick Drain Services", phone="613-555-0100")
        c = rec("c", name="Unrelated Florist", phone="613-555-0999")
        pairs = match.candidate_pairs([a, b, c])
        self.assertEqual(pairs, {(0, 1)})

    def test_oversized_block_is_skipped(self):
        records = [rec(str(i), name=f"{chr(97 + i % 26)}{chr(97 + i // 26)}corp{chr(110 + i % 7)}", website="https://shared.ca")
                   for i in range(match.MAX_BLOCK + 1)]
        self.assertEqual(match.candidate_pairs(records), set())

    def test_score_is_symmetric(self):
        other = rec("2", name="Maple Leaf Bakery Inc", phone="416-555-0100")
        self.assertEqual(match.score_pair(self.base, other).score, match.score_pair(other, self.base).score)


if __name__ == "__main__":
    unittest.main()

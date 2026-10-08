import unittest

from tests import helpers  # noqa: F401
from lookalike import similarity as sim


class SimilarityTests(unittest.TestCase):
    def test_identical_and_empty(self):
        self.assertEqual(sim.jaro_winkler("maple", "maple"), 1.0)
        self.assertEqual(sim.jaro_winkler("", ""), 0.0)

    def test_known_jaro_winkler_value(self):
        # classic reference pair
        self.assertAlmostEqual(sim.jaro_winkler("martha", "marhta"), 0.9611, places=3)

    def test_typo_scores_high_unrelated_low(self):
        self.assertGreater(sim.jaro_winkler("maple hearth bakery", "maple hearth bakry"), 0.95)
        self.assertLess(sim.jaro_winkler("maple hearth bakery", "northern lights outfitters"), 0.6)

    def test_word_order_robust(self):
        self.assertGreaterEqual(sim.name_similarity(["bakery", "maple"], ["maple", "bakery"]), 0.99)

    def test_empty_tokens_zero(self):
        self.assertEqual(sim.name_similarity([], ["a"]), 0.0)


if __name__ == "__main__":
    unittest.main()

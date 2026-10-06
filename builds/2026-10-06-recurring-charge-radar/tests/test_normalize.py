import unittest

import helpers  # noqa: F401
from recurring.normalize import display_name, merchant_key


class NormalizeTests(unittest.TestCase):
    def test_store_number_and_location_stripped(self):
        self.assertEqual(merchant_key("GOODLIFE FITNESS #4412 TORONTO ON"), "goodlife fitness")

    def test_same_merchant_different_references_share_key(self):
        self.assertEqual(
            merchant_key("SPOTIFY P1A2B3C4 STOCKHOLM"), merchant_key("SPOTIFY P9Z8Y7X6 STOCKHOLM")
        )

    def test_pos_prefix_and_processor_tag_removed(self):
        self.assertEqual(merchant_key("POS PURCHASE LOBLAWS #123 TORONTO ON"), "loblaws")
        self.assertEqual(merchant_key("SQ *BLUE BOTTLE COFFEE"), "blue bottle coffee")

    def test_domain_suffix_and_phone_removed(self):
        self.assertEqual(display_name("NETFLIX.COM 866-579-7172 CA"), "Netflix")

    def test_display_name_title_cases_shouting(self):
        self.assertEqual(display_name("ROGERS WIRELESS"), "Rogers Wireless")

    def test_empty_after_cleaning_falls_back_to_raw(self):
        self.assertEqual(display_name("#1234"), "#1234")

    def test_numbers_inside_names_survive(self):
        self.assertIn("365", merchant_key("MICROSOFT*365 PERSONAL"))


if __name__ == "__main__":
    unittest.main()

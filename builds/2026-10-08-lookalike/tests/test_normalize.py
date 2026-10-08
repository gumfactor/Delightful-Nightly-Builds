import unittest

from tests import helpers  # noqa: F401
from lookalike import normalize as nz


class NormalizeTests(unittest.TestCase):
    def test_name_drops_legal_suffix_article_and_accents(self):
        self.assertEqual(nz.name_key("The Café Dubé Ltée."), "cafe dube")

    def test_name_ampersand_equals_and(self):
        self.assertEqual(nz.name_key("Salt & Pepper Inc"), nz.name_key("Salt and Pepper"))

    def test_name_that_is_only_a_suffix_is_not_emptied(self):
        self.assertEqual(nz.name_key("Inc"), "inc")

    def test_domain_strips_scheme_www_path(self):
        self.assertEqual(nz.registered_domain("https://www.shop.Maple.ca/about?x=1"), "maple.ca")

    def test_domain_for_bare_host_and_email(self):
        self.assertEqual(nz.registered_domain("maple.ca"), "maple.ca")
        self.assertEqual(nz.registered_domain("hi@maple.ca"), "maple.ca")

    def test_social_and_marketplace_hosts_are_not_identity(self):
        self.assertEqual(nz.registered_domain("https://www.facebook.com/mapleleaf"), "")
        self.assertEqual(nz.registered_domain("https://shop.myshopify.com"), "")

    def test_garbage_domain_is_empty(self):
        self.assertEqual(nz.registered_domain("not a url"), "")
        self.assertEqual(nz.registered_domain(""), "")

    def test_phone_variants_and_extension(self):
        for raw in ("416-555-0100", "(416) 555 0100", "+1 416.555.0100 ext 22", "1-416-555-0100"):
            self.assertEqual(nz.phone_digits(raw), "4165550100", raw)

    def test_invalid_phone_rejected(self):
        self.assertEqual(nz.phone_digits("555-0100"), "")
        self.assertEqual(nz.phone_digits("016-555-0100"), "")

    def test_postal_code_canonical(self):
        self.assertEqual(nz.postal_code("m5h-2n2"), "M5H2N2")
        self.assertEqual(nz.postal_code("12345"), "")

    def test_province_names_and_codes(self):
        self.assertEqual(nz.province_code("Québec"), "QC")
        self.assertEqual(nz.province_code("ontario"), "ON")
        self.assertEqual(nz.province_code("Narnia"), "")

    def test_street_expansion_and_unit_extraction(self):
        self.assertEqual(nz.street_parts("Unit 5, 123 Queen St. W., Toronto"), ("123 queen street west", "5"))
        self.assertEqual(nz.street_parts("5-123 Queen Street West"), ("123 queen street west", "5"))

    def test_email_validation(self):
        self.assertEqual(nz.normalize_email(" Hi@Maple.CA "), "hi@maple.ca")
        self.assertEqual(nz.normalize_email("nope"), "")


if __name__ == "__main__":
    unittest.main()

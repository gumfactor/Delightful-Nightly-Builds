import csv
import io
import tempfile
import unittest
from pathlib import Path

from tests.helpers import rec
from lookalike import report
from lookalike.cluster import analyze


class ReportTests(unittest.TestCase):
    def test_deduped_rows_collapse_cluster_and_keep_provenance_columns(self):
        a = rec("1", name="Acme Widgets", phone="416-555-0100", website="acme.ca")
        b = rec("2", name="Acme Widgets Inc", phone="416-555-0100", website="www.acme.ca", email="a@acme.ca")
        c = rec("3", name="Zed Co", phone="613-555-0000")
        rows = report.deduped_rows(analyze([a, b, c]))
        self.assertEqual(len(rows), 2)
        merged = next(r for r in rows if r["merged_from"])
        self.assertEqual(merged["merged_from"], "1;2")
        self.assertEqual(merged["email"], "a@acme.ca")

    def test_html_escapes_untrusted_content(self):
        a = rec("1", name="<script>alert(1)</script> Cafe", phone="416-555-0100", province="ON")
        b = rec("2", name="Script Cafe", phone="416-555-0100", province="ON", description='"><img src=x onerror=alert(2)>')
        page = report.render_html(analyze([a, b]))
        self.assertNotIn("<script>alert(1)", page)
        self.assertNotIn("<img src=x", page)
        self.assertIn("&lt;script&gt;alert(1)", page)

    def test_html_is_self_contained_and_mobile_ready(self):
        page = report.render_html(analyze([rec("1", name="A One"), rec("2", name="B Two")]))
        self.assertIn('name="viewport"', page)
        self.assertNotIn("http://", page.replace("http://www.w3.org", ""))
        self.assertNotIn('src="http', page)
        self.assertIn("prefers-color-scheme:dark", page)

    def test_csv_formula_injection_neutralized_but_phones_kept(self):
        self.assertEqual(report.csv_safe("=HYPERLINK(\"x\")"), "'=HYPERLINK(\"x\")")
        self.assertEqual(report.csv_safe("+1 416 555 0100"), "+1 416 555 0100")
        self.assertEqual(report.csv_safe("Acme"), "Acme")

    def test_written_csv_roundtrips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "o.csv"
            report.write_csv(path, [{"id": "1", "name": "A, \"B\""}, {"id": "2", "extra": "x"}])
            rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
        self.assertEqual(rows[0]["name"], 'A, "B"')
        self.assertEqual(rows[1]["extra"], "x")


if __name__ == "__main__":
    unittest.main()

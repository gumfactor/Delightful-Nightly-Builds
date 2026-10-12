import csv
import tempfile
import unittest
from pathlib import Path

from edgar_fin import exports, report
from edgar_fin.extract import extract_company

from helpers import DEMO_COMPANIES


def companies():
    return [extract_company(s["payload"], t, s["cik"], 5) for t, s in DEMO_COMPANIES.items()]


class ExportTests(unittest.TestCase):
    def test_long_csv_has_header_and_rows_for_every_ticker(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "long.csv"
            exports.write_long_csv(companies(), path)
            rows = list(csv.DictReader(path.read_text().splitlines()))
        self.assertEqual(set(rows[0]), set(exports.LONG_HEADER))
        self.assertEqual({r["ticker"] for r in rows}, set(DEMO_COMPANIES))
        revenue = [r for r in rows if r["ticker"] == "NWND" and r["metric"] == "revenue" and r["fiscal_year"] == "2019"]
        self.assertEqual(len(revenue), 0)  # 2019 is outside the 5-year window
        self.assertEqual(len([r for r in rows if r["ticker"] == "NWND" and r["metric"] == "revenue"]), 5)

    def test_wide_csv_has_one_column_per_year(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "w.csv"
            company = companies()[0]
            exports.write_wide_csv(company, path)
            header = next(csv.reader(path.read_text().splitlines()))
        self.assertEqual(header, ["metric", *map(str, company["years"])])

    def test_summary_csv_one_row_per_company(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s.csv"
            exports.write_summary_csv(companies(), path)
            rows = list(csv.DictReader(path.read_text().splitlines()))
        self.assertEqual(len(rows), 3)

    def test_filename_sanitised_against_path_traversal(self):
        self.assertEqual(exports.safe_filename("../../etc/passwd"), "______etc_passwd")


class ReportTests(unittest.TestCase):
    def test_report_contains_every_ticker_and_chart_hook(self):
        page = report.render(companies())
        for ticker in DEMO_COMPANIES:
            self.assertIn(f'id="co-{ticker}"', page)
        self.assertIn("chart.js@4.4.4", page)
        self.assertIn('data-testid="metric-select"', page)

    def test_hostile_company_name_is_escaped(self):
        data = companies()
        data[0]["name"] = '<img src=x onerror=alert(1)></script><script>alert(2)</script>'
        page = report.render(data)
        self.assertNotIn("<img src=x", page)
        self.assertEqual(page.count("</script>"), 2)  # only our own two script tags

    def test_json_embedding_escapes_angle_brackets(self):
        self.assertNotIn("<", report.json_for_script({"a": "</script>"}))

    def test_ai_commentary_is_escaped_and_rendered(self):
        page = report.render(companies(), commentary="Growth <b>fast</b>.\n\nSecond.")
        self.assertIn("Growth &lt;b&gt;fast&lt;/b&gt;.", page)
        self.assertNotIn("<b>fast</b>", page)

    def test_demo_banner_and_dark_mode_present(self):
        page = report.render(companies(), demo=True)
        self.assertIn("synthetic", page)
        self.assertIn("prefers-color-scheme: dark", page)
        self.assertIn('name="viewport"', page)

    def test_formatters(self):
        self.assertEqual(report.fmt("revenue", 1.5e9), "$1.50B")
        self.assertEqual(report.fmt("revenue", -2.5e6), "-$2.50M")
        self.assertEqual(report.fmt("net_margin", 0.1234), "12.3%")
        self.assertEqual(report.fmt("debt_to_equity", 0.5), "0.50×")
        self.assertEqual(report.fmt("revenue", None), "–")

    def test_errors_listed(self):
        page = report.render(companies(), errors=["ZZZ: unknown"])
        self.assertIn("ZZZ: unknown", page)


if __name__ == "__main__":
    unittest.main()

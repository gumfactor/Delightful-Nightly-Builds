import unittest

from edgar_fin.metrics import cagr, derive, growth, safe_div, summarize
from edgar_fin.extract import extract_company

from helpers import DEMO_COMPANIES


class MetricsTests(unittest.TestCase):
    def test_safe_div_handles_zero_and_none(self):
        self.assertIsNone(safe_div(1, 0))
        self.assertIsNone(safe_div(None, 2))
        self.assertEqual(safe_div(1, 4), 0.25)

    def test_growth_undefined_for_non_positive_base(self):
        self.assertIsNone(growth(10, 0))
        self.assertIsNone(growth(10, -5))
        self.assertAlmostEqual(growth(110, 100), 0.1)

    def test_cagr_matches_known_value(self):
        self.assertAlmostEqual(cagr(100, 200, 5), 2 ** 0.2 - 1)
        self.assertIsNone(cagr(-1, 5, 3))
        self.assertIsNone(cagr(1, 5, 0))

    def test_roe_and_leverage_skipped_for_negative_equity(self):
        metrics = {"net_income": {2020: 10}, "equity": {2020: -50}, "long_term_debt": {2020: 100}}
        derived = derive(metrics, [2020])
        self.assertNotIn(2020, derived["roe"])
        self.assertNotIn(2020, derived["debt_to_equity"])

    def test_margins_and_returns(self):
        metrics = {"revenue": {2020: 200}, "gross_profit": {2020: 100}, "operating_income": {2020: 40},
                   "net_income": {2020: 20}, "equity": {2020: 100}, "total_assets": {2020: 400},
                   "long_term_debt": {2020: 50}}
        derived = derive(metrics, [2020])
        self.assertAlmostEqual(derived["gross_margin"][2020], 0.5)
        self.assertAlmostEqual(derived["operating_margin"][2020], 0.2)
        self.assertAlmostEqual(derived["net_margin"][2020], 0.1)
        self.assertAlmostEqual(derived["roe"][2020], 0.2)
        self.assertAlmostEqual(derived["roa"][2020], 0.05)
        self.assertAlmostEqual(derived["debt_to_equity"][2020], 0.5)

    def test_summary_cagr_spans_available_years(self):
        spec = DEMO_COMPANIES["NWND"]
        company = extract_company(spec["payload"], "NWND", spec["cik"], years=5)
        summary = summarize(company)
        self.assertEqual(summary["latest_year"], 2024)
        self.assertAlmostEqual(summary["revenue_cagr"], 0.12, places=6)

    def test_summary_on_empty_company_is_all_none(self):
        summary = summarize(extract_company({"facts": {}}, "X", 1))
        self.assertIsNone(summary["revenue"])
        self.assertIsNone(summary["revenue_cagr"])


if __name__ == "__main__":
    unittest.main()

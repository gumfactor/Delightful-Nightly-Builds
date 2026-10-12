import unittest
from datetime import date

from edgar_fin.extract import extract_company, fiscal_year

from helpers import annual, flow, instant


class ExtractTests(unittest.TestCase):
    def test_quarterly_and_ytd_facts_are_ignored(self):
        payload = annual({"Revenues": [
            flow(2022, 400, start="2022-01-01", end="2022-03-31", form="10-Q"),
            flow(2022, 900, start="2022-01-01", end="2022-09-30"),  # 9-month YTD in a 10-K: not annual
            flow(2022, 1200)]})
        company = extract_company(payload, "T", 1)
        self.assertEqual(company["metrics"]["revenue"], {2022: 1200.0})

    def test_ten_q_form_is_excluded_even_if_duration_is_annual(self):
        payload = annual({"Revenues": [flow(2022, 5, form="10-Q"), flow(2023, 7)]})
        self.assertEqual(extract_company(payload, "T", 1)["metrics"]["revenue"], {2023: 7.0})

    def test_restatement_latest_filing_wins(self):
        payload = annual({"Revenues": [flow(2021, 100, filed="2022-02-01"),
                                       flow(2021, 110, filed="2023-02-01", form="10-K/A")]})
        self.assertEqual(extract_company(payload, "T", 1)["metrics"]["revenue"][2021], 110.0)

    def test_alias_fallback_merges_tags_per_year(self):
        payload = annual({
            "SalesRevenueNet": [flow(2016, 50), flow(2017, 60)],
            "RevenueFromContractWithCustomerExcludingAssessedTax": [flow(2018, 80), flow(2019, 90)]})
        revenue = extract_company(payload, "T", 1)["metrics"]["revenue"]
        self.assertEqual(revenue, {2016: 50.0, 2017: 60.0, 2018: 80.0, 2019: 90.0})

    def test_higher_priority_alias_wins_when_both_present(self):
        payload = annual({"Revenues": [flow(2020, 10)], "SalesRevenueNet": [flow(2020, 99)]})
        self.assertEqual(extract_company(payload, "T", 1)["metrics"]["revenue"][2020], 10.0)

    def test_gross_profit_falls_back_to_revenue_minus_cost(self):
        payload = annual({"Revenues": [flow(2020, 100)], "CostOfRevenue": [flow(2020, 60)]})
        company = extract_company(payload, "T", 1)
        self.assertEqual(company["metrics"]["gross_profit"][2020], 40.0)
        self.assertAlmostEqual(company["derived"]["gross_margin"][2020], 0.4)

    def test_capex_sign_is_normalised_and_fcf_computed(self):
        payload = annual({"Revenues": [flow(2020, 100)],
                          "NetCashProvidedByUsedInOperatingActivities": [flow(2020, 30)],
                          "PaymentsToAcquirePropertyPlantAndEquipment": [flow(2020, -8)]})
        company = extract_company(payload, "T", 1)
        self.assertEqual(company["metrics"]["capex"][2020], 8.0)
        self.assertEqual(company["derived"]["free_cash_flow"][2020], 22.0)

    def test_window_keeps_last_n_years_but_growth_uses_prior_year(self):
        payload = annual({"Revenues": [flow(y, 100 * (1.1 ** i)) for i, y in enumerate(range(2018, 2024))]})
        company = extract_company(payload, "T", 1, years=3)
        self.assertEqual(company["years"], [2021, 2022, 2023])
        self.assertAlmostEqual(company["derived"]["revenue_growth"][2021], 0.1)
        self.assertNotIn(2020, company["metrics"]["revenue"])

    def test_january_year_end_is_labelled_with_prior_year(self):
        self.assertEqual(fiscal_year(date(2024, 1, 31)), 2023)
        self.assertEqual(fiscal_year(date(2024, 12, 31)), 2024)
        self.assertEqual(fiscal_year(date(2024, 9, 28)), 2024)

    def test_balance_sheet_instant_values_and_eps_unit(self):
        payload = annual({"Assets": [instant(2020, 500)]})
        payload["facts"]["us-gaap"]["EarningsPerShareDiluted"] = {
            "units": {"USD/shares": [flow(2020, 1.25)]}}
        company = extract_company(payload, "T", 1)
        self.assertEqual(company["metrics"]["total_assets"][2020], 500.0)
        self.assertEqual(company["metrics"]["eps_diluted"][2020], 1.25)

    def test_empty_payload_yields_no_years(self):
        company = extract_company({"facts": {}}, "zzz", 5)
        self.assertEqual(company["years"], [])
        self.assertEqual(company["ticker"], "ZZZ")

    def test_malformed_dates_are_skipped_not_fatal(self):
        payload = annual({"Revenues": [{"start": "bad", "end": "worse", "val": 1, "form": "10-K"}, flow(2020, 5)]})
        self.assertEqual(extract_company(payload, "T", 1)["metrics"]["revenue"], {2020: 5.0})


if __name__ == "__main__":
    unittest.main()

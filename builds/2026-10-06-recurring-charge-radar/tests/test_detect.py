import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

import helpers
from recurring.demo import demo_transactions
from recurring.detect import add_months, advance, classify_cadence, detect, segment_levels
from recurring.models import Transaction
from recurring.rules import Rules, RulesError, load_rules


def txns(desc, dates, amount=10.0):
    amounts = amount if isinstance(amount, list) else [amount] * len(dates)
    return [Transaction(d, desc, a, "t.csv") for d, a in zip(dates, amounts)]


class CadenceTests(unittest.TestCase):
    def test_each_cadence_classified(self):
        self.assertEqual(classify_cadence([7, 7, 8])[0], "weekly")
        self.assertEqual(classify_cadence([14, 14, 14])[0], "biweekly")
        self.assertEqual(classify_cadence([30, 31, 28, 31])[0], "monthly")
        self.assertEqual(classify_cadence([91, 92])[0], "quarterly")
        self.assertEqual(classify_cadence([365])[0], "annual")

    def test_irregular_gaps_have_no_cadence(self):
        self.assertIsNone(classify_cadence([1, 45, 3, 120]))

    def test_month_end_clamping(self):
        self.assertEqual(add_months(date(2026, 1, 31), 1), date(2026, 2, 28))
        self.assertEqual(advance(date(2026, 1, 31), "annual"), date(2027, 1, 31))


class DetectTests(unittest.TestCase):
    def test_fixed_monthly_subscription(self):
        found = detect(helpers.monthly("SPOTIFY STOCKHOLM", 12.99))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].cadence, "monthly")
        self.assertEqual(found[0].status, "active")
        self.assertEqual(found[0].annual_cost, round(12.99 * 365 / 30, 2))

    def test_date_drift_around_weekends_still_monthly(self):
        dates = [date(2026, 1, 5), date(2026, 2, 6), date(2026, 3, 5), date(2026, 4, 7), date(2026, 5, 5)]
        self.assertEqual(detect(txns("GYM", dates))[0].cadence, "monthly")

    def test_coffee_shop_not_flagged(self):
        start = date(2026, 1, 1)
        offsets = [0, 1, 3, 8, 9, 15, 16, 17, 24, 30, 31, 40]
        dates = [start + timedelta(days=o) for o in offsets]
        amounts = [4.5, 6.2, 5.1, 7.0, 4.8, 9.1, 5.5, 6.0, 4.9, 5.2, 8.1, 6.6]
        self.assertEqual(detect(txns("STARBUCKS", dates, amounts)), [])

    def test_two_charges_not_enough_unless_annual(self):
        self.assertEqual(detect(txns("X", [date(2026, 1, 1), date(2026, 2, 1)])), [])
        found = detect(txns("DOMAIN RENEWAL", [date(2025, 9, 22), date(2026, 9, 22)], 20.18))
        self.assertEqual(found[0].cadence, "annual")

    def test_variable_utility_bill_flagged_variable(self):
        amounts = [92.1, 140.5, 77.0, 118.2, 101.9, 85.4]
        series = detect(txns("HYDRO", [add_months(date(2026, 1, 26), i) for i in range(6)], amounts))[0]
        self.assertTrue(series.variable)
        self.assertEqual(series.price_changes, [])

    def test_frequent_variable_spending_rejected(self):
        dates = [date(2026, 1, 3) + timedelta(days=7 * i) for i in range(8)]
        amounts = [60, 140, 85, 200, 45, 120, 95, 150]
        self.assertEqual(detect(txns("GROCER", dates, amounts)), [])

    def test_ignore_rule_drops_merchant(self):
        rules = Rules(ignore=["spotify"])
        self.assertEqual(detect(helpers.monthly("SPOTIFY", 12.99), rules), [])

    def test_alias_merges_different_descriptors(self):
        rows = helpers.monthly("ACME CORP 111", 9.99, count=3)
        rows += helpers.monthly("ACME*BILLING 222", 9.99, start=date(2026, 4, 5), count=3)
        found = detect(rows, Rules(aliases={"acme": "Acme"}))
        self.assertEqual([s.merchant for s in found], ["Acme"])
        self.assertEqual(len(found[0].charges), 6)

    def test_two_subscriptions_same_merchant_split_by_amount(self):
        rows = helpers.monthly("APPLE.COM/BILL", 1.99) + helpers.monthly("APPLE.COM/BILL", 14.99)
        found = detect(rows)
        self.assertEqual(sorted(s.typical_amount for s in found), [1.99, 14.99])


class PriceChangeTests(unittest.TestCase):
    def test_price_hike_detected_with_delta(self):
        amounts = [20.99] * 4 + [23.99] * 3
        series = detect(txns("NETFLIX", [add_months(date(2026, 1, 3), i) for i in range(7)], amounts))[0]
        self.assertEqual(len(series.price_changes), 1)
        change = series.price_changes[0]
        self.assertEqual((change.old, change.new, change.delta), (20.99, 23.99, 3.0))
        self.assertEqual(change.percent, 14.3)
        self.assertEqual(series.typical_amount, 23.99)

    def test_hike_on_latest_charge_flagged_immediately(self):
        amounts = [10.0] * 5 + [12.0]
        series = detect(txns("SAAS", [add_months(date(2026, 1, 1), i) for i in range(6)], amounts))[0]
        self.assertEqual(series.price_changes[0].new, 12.0)

    def test_small_fx_noise_is_not_a_price_change(self):
        amounts = [27.40, 27.62, 27.18, 27.55, 27.31]
        series = detect(txns("OPENAI", [add_months(date(2026, 1, 14), i) for i in range(5)], amounts))[0]
        self.assertEqual(series.price_changes, [])

    def test_one_off_spike_is_noise_not_price_change(self):
        changes, noisy = segment_levels(txns("X", [add_months(date(2026, 1, 1), i) for i in range(4)],
                                             [10.0, 25.0, 10.0, 10.0]))
        self.assertEqual(changes, [])
        self.assertEqual(noisy, 1)


class LifecycleTests(unittest.TestCase):
    def test_stopped_charges_become_lapsed_with_no_next_date(self):
        rows = helpers.monthly("DROPBOX", 13.5, start=date(2025, 6, 6), count=8)
        rows.append(Transaction(date(2026, 10, 1), "OTHER", 1.0))
        series = detect(rows)[0]
        self.assertEqual(series.status, "lapsed")
        self.assertIsNone(series.next_expected)

    def test_charges_after_cancellation_are_zombie(self):
        rows = helpers.monthly("GYM", 14.97, start=date(2026, 1, 1), count=9)
        series = detect(rows, Rules(cancelled={"Gym": date(2026, 6, 1)}))[0]
        self.assertEqual(series.status, "zombie")

    def test_cancelled_and_quiet_is_cancelled(self):
        rows = helpers.monthly("GYM", 14.97, start=date(2026, 1, 1), count=5)
        series = detect(rows, Rules(cancelled={"Gym": date(2026, 5, 15)}))[0]
        self.assertEqual(series.status, "cancelled")

    def test_next_expected_never_in_the_past(self):
        rows = helpers.monthly("X", 5.0, start=date(2026, 1, 5), count=6)
        series = detect(rows, as_of=date(2026, 6, 20))[0]
        self.assertGreaterEqual(series.next_expected, date(2026, 6, 20))


class RulesTests(unittest.TestCase):
    def _write(self, content):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "rules.json"
        path.write_text(content, encoding="utf-8")
        return path

    def test_valid_rules_load(self):
        rules = load_rules(self._write(json.dumps({"ignore": ["x"], "cancelled": {"Gym": "2026-06-01"}})))
        self.assertEqual(rules.cancelled["Gym"], date(2026, 6, 1))

    def test_bad_date_is_actionable_error(self):
        with self.assertRaises(RulesError) as ctx:
            load_rules(self._write(json.dumps({"cancelled": {"Gym": "June 1"}})))
        self.assertIn("YYYY-MM-DD", str(ctx.exception))

    def test_invalid_json_and_missing_file(self):
        with self.assertRaises(RulesError):
            load_rules(self._write("{nope"))
        with self.assertRaises(RulesError):
            load_rules("/no/such/rules.json")


class DemoDetectionTests(unittest.TestCase):
    def test_demo_seeds_found_and_noise_rejected(self):
        found = {s.merchant: s for s in detect(demo_transactions(), Rules(cancelled={"Goodlife Fitness": date(2026, 7, 1)}))}
        names = " ".join(found)
        for expected in ("Netflix", "Spotify", "Openai", "Anthropic", "Rogers", "Github", "Namecheap", "Toronto Hydro"):
            self.assertIn(expected, names)
        self.assertNotIn("Starbucks", names)
        self.assertNotIn("Loblaws", names)
        self.assertNotIn("Amazon", names)  # a single annual charge is not yet a pattern
        self.assertEqual(found["Goodlife Fitness"].status, "zombie")
        self.assertEqual(found["Netflix"].price_changes[0].delta, 3.0)
        self.assertEqual(found["Dropbox"].status, "lapsed")


if __name__ == "__main__":
    unittest.main()

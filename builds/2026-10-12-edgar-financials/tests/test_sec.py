import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from edgar_fin.sec import SecClient, SecError, user_agent_from_env

from helpers import DEMO_COMPANIES, FakeSec, no_sleep

UA = "Test Suite test@example.com"


class SecTests(unittest.TestCase):
    def client(self, fake, cache=None, **kwargs):
        return SecClient(UA, cache_dir=cache, fetch=fake, sleep=no_sleep, **kwargs)

    def test_resolve_known_ticker_case_insensitive(self):
        fake = FakeSec(DEMO_COMPANIES)
        cik, title = self.client(fake).resolve("nwnd")
        self.assertEqual(cik, 9000001)
        self.assertIn("Northwind", title)

    def test_unknown_ticker_raises_clear_error(self):
        with self.assertRaisesRegex(SecError, "Unknown ticker 'NOPE'"):
            self.client(FakeSec(DEMO_COMPANIES)).resolve("NOPE")

    def test_user_agent_header_is_sent(self):
        fake = FakeSec(DEMO_COMPANIES)
        self.client(fake).resolve("NWND")
        self.assertEqual(fake.requests[0][1]["User-Agent"], UA)

    def test_user_agent_without_email_is_rejected(self):
        with self.assertRaises(SecError):
            SecClient("just-a-name", fetch=FakeSec())

    def test_missing_env_user_agent_message(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(SecError, "EDGAR_USER_AGENT"):
                user_agent_from_env()

    def test_cache_prevents_second_network_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = FakeSec(DEMO_COMPANIES)
            self.client(fake, Path(tmp)).company_facts(9000001)
            first = len(fake.requests)
            self.client(fake, Path(tmp)).company_facts(9000001)
            self.assertEqual(len(fake.requests), first)

    def test_refresh_bypasses_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake = FakeSec(DEMO_COMPANIES)
            self.client(fake, Path(tmp)).company_facts(9000001)
            self.client(fake, Path(tmp), refresh=True).company_facts(9000001)
            self.assertEqual(len(fake.requests), 2)

    def test_corrupt_cache_is_redownloaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "CIK0009000001.json").write_text("{not json")
            data = self.client(FakeSec(DEMO_COMPANIES), Path(tmp)).company_facts(9000001)
            self.assertIn("facts", data)

    def test_retries_on_429_then_succeeds(self):
        fake = FakeSec(DEMO_COMPANIES, fail_times=2, fail_code=429)
        self.assertIn("facts", self.client(fake).company_facts(9000002))
        self.assertEqual(len(fake.requests), 3)

    def test_gives_up_after_retries(self):
        fake = FakeSec(DEMO_COMPANIES, fail_times=10, fail_code=503)
        with self.assertRaisesRegex(SecError, "after 3 attempts"):
            self.client(fake).company_facts(9000002)

    def test_404_is_reported_without_retry(self):
        fake = FakeSec(DEMO_COMPANIES)
        with self.assertRaisesRegex(SecError, "404"):
            self.client(fake).company_facts(1234)
        self.assertEqual(len(fake.requests), 1)


if __name__ == "__main__":
    unittest.main()

"""Shared test helpers: fake SEC transport and small payload builders."""
import json
import urllib.error

from edgar_fin.demo import DEMO_COMPANIES, DEMO_YEARS, make_payload  # noqa: F401


def annual(tag_entries):
    """Wrap entries as a companyfacts us-gaap payload with USD units."""
    return {"facts": {"us-gaap": {tag: {"units": {"USD": entries}} for tag, entries in tag_entries.items()}}}


def flow(year, value, form="10-K", filed=None, start=None, end=None):
    return {"start": start or f"{year}-01-01", "end": end or f"{year}-12-31", "val": value,
            "form": form, "filed": filed or f"{year + 1}-02-01"}


def instant(year, value, form="10-K", filed=None, end=None):
    return {"end": end or f"{year}-12-31", "val": value, "form": form, "filed": filed or f"{year + 1}-02-01"}


class FakeSec:
    """Callable transport serving ticker list and companyfacts, recording requests."""

    def __init__(self, companies=None, fail_times=0, fail_code=429):
        self.companies = companies or {}
        self.requests = []
        self.fail_times = fail_times
        self.fail_code = fail_code

    def __call__(self, url, headers):
        self.requests.append((url, headers))
        if self.fail_times > 0:
            self.fail_times -= 1
            raise urllib.error.HTTPError(url, self.fail_code, "err", {}, None)
        if url.endswith("company_tickers.json"):
            return json.dumps({str(i): {"cik_str": c["cik"], "ticker": t, "title": c["payload"]["entityName"]}
                               for i, (t, c) in enumerate(self.companies.items())}).encode()
        for ticker, company in self.companies.items():
            if url.endswith(f"CIK{company['cik']:010d}.json"):
                return json.dumps(company["payload"]).encode()
        raise urllib.error.HTTPError(url, 404, "not found", {}, None)


def no_sleep(_seconds):
    return None

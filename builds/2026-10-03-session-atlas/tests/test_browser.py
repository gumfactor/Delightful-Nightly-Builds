"""Browser smoke tests for the generated explorer (skipped when Chromium is unavailable)."""
import glob
import os

import pytest

from conftest import user, write_jsonl
from atlas.demo import generate_demo_logs
from atlas.pricing import DEFAULT_PRICES
from atlas.report import write_report
from atlas.store import Store

playwright_sync = pytest.importorskip("playwright.sync_api")


def _chromium_path():
    """Prefer an explicit CHROMIUM_PATH, then a Playwright-managed browser; None lets Playwright decide."""
    explicit = os.environ.get("CHROMIUM_PATH")
    if explicit:
        return explicit
    for pattern in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome",):
        found = sorted(glob.glob(pattern))
        if found:
            return found[-1]
    return None


@pytest.fixture(scope="module")
def page(tmp_path_factory):
    root = tmp_path_factory.mktemp("browser")
    generate_demo_logs(root / "logs", days=30, seed=3)
    write_jsonl(root / "logs" / "-evil" / "x.jsonl", [user("2026-10-01T10:00:00Z", "<img src=x onerror=\"window.__pwned=1\"> zebra")])
    store = Store(root / "t.db")
    store.index_directory(root / "logs", DEFAULT_PRICES)
    report = write_report(store, root / "r.html", tz_offset_hours=-4)
    store.close()
    with playwright_sync.sync_playwright() as pw:
        try:
            browser = pw.chromium.launch(executable_path=_chromium_path())
        except Exception as exc:  # no browser installed
            pytest.skip(f"chromium unavailable: {exc}")
        pg = browser.new_page(viewport={"width": 390, "height": 800})
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(report.as_uri())
        pg.errors = errors
        yield pg
        browser.close()


def test_page_loads_without_js_errors_and_shows_kpis(page):
    assert page.errors == []
    assert page.locator("[data-testid=kpis] .kpi").count() >= 8


def test_charts_render(page):
    assert page.locator("[data-testid=daybar]").count() > 5
    assert page.locator("[data-testid=heat] rect").count() == 7 * 24


def test_no_horizontal_page_scroll_on_phone_width(page):
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")


def test_search_filters_sessions_live(page):
    total = page.locator("[data-testid=session-row]").count()
    page.fill("[data-testid=search]", "zebra")
    assert page.locator("[data-testid=session-row]").count() == 1 < total
    page.fill("[data-testid=search]", "qqqqnomatch")
    assert page.locator("[data-testid=session-row]").count() == 0
    page.click("#clear")


def test_hostile_prompt_renders_as_text_not_html(page):
    page.fill("[data-testid=search]", "zebra")
    page.locator("[data-testid=session-row]").first.click()
    assert "<img src=x" in page.locator("[data-testid=prompt-list]").inner_text()
    assert page.evaluate("window.__pwned") is None
    page.click("#clear")


def test_project_row_click_filters_and_detail_shows_resume_prompt(page):
    page.locator("[data-testid=project-row]").first.click()
    assert page.locator("[data-testid=session-row]").count() < int(page.locator("[data-testid=count]").inner_text().split(" of ")[1].split()[0])
    page.locator("[data-testid=session-row]").first.click()
    assert "Resuming earlier work" in page.locator("[data-testid=resume]").inner_text()
    page.click("#clear")

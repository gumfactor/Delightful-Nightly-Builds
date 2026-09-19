// @ts-check
const path = require('node:path');
const { test, expect } = require('@playwright/test');

const NORMAL_FIXTURE = 'file://' + path.join(__dirname, 'fixtures', 'dashboard_normal.html');
const HOSTILE_FIXTURE = 'file://' + path.join(__dirname, 'fixtures', 'dashboard_hostile.html');

test.describe('Grant Horizon dashboard', () => {
  test('renders hero stats matching the fixture data exactly', async ({ page }) => {
    await page.goto(NORMAL_FIXTURE);
    const heroText = await page.locator('#hero').innerText();
    // Fixture: $100k + $300k + $50k = $450k across 3 rows, 2 topics.
    expect(heroText).toContain('$450,000');
    expect(heroText).toContain('3');
    expect(heroText).toContain('2');
  });

  test('falls back to a DOM table when the Chart.js CDN is unreachable', async ({ page }) => {
    // This container's own network policy blocks the CDN, so this exercises
    // the real fallback path, not a simulated one.
    const consoleErrors = [];
    page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });
    await page.goto(NORMAL_FIXTURE);
    await page.waitForTimeout(400);

    await expect(page.locator('#trendFallback')).toHaveClass(/active/);
    await expect(page.locator('#institutionsFallback')).toHaveClass(/active/);
    expect(await page.locator('#trendFallback tr').count()).toBeGreaterThan(0);
  });

  test('search box filters the project table', async ({ page }) => {
    await page.goto(NORMAL_FIXTURE);
    expect(await page.locator('#projectsBody tr').count()).toBe(3);
    await page.fill('#searchBox', 'cortisol');
    expect(await page.locator('#projectsBody tr').count()).toBe(1);
    await expect(page.locator('#projectsBody tr').first()).toContainText('Cortisol reactivity');
  });

  test('clicking a sortable column header sorts and updates aria-sort', async ({ page }) => {
    await page.goto(NORMAL_FIXTURE);
    const awardHeader = page.locator('th[data-key="award_amount"]');
    // Default sort is award_amount descending.
    await expect(awardHeader).toHaveAttribute('aria-sort', 'descending');
    let firstRowAward = await page.locator('#projectsBody tr').first().locator('td').nth(2).innerText();
    expect(firstRowAward).toBe('$300,000');

    await awardHeader.click();
    await expect(awardHeader).toHaveAttribute('aria-sort', 'ascending');
    firstRowAward = await page.locator('#projectsBody tr').first().locator('td').nth(2).innerText();
    expect(firstRowAward).toBe('$50,000');
  });

  test('sortable headers are keyboard-operable (Enter and Space)', async ({ page }) => {
    await page.goto(NORMAL_FIXTURE);
    const topicHeader = page.locator('th[data-key="topic"]');
    await expect(topicHeader).toHaveAttribute('tabindex', '0');
    await expect(topicHeader).toHaveAttribute('role', 'button');

    await topicHeader.focus();
    await page.keyboard.press('Enter');
    await expect(topicHeader).toHaveClass(/sorted/);
    await expect(topicHeader).toHaveAttribute('aria-sort', 'descending');

    await page.keyboard.press(' ');
    await expect(topicHeader).toHaveAttribute('aria-sort', 'ascending');
  });

  test('zero horizontal overflow at a 375px mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 800 });
    await page.goto(NORMAL_FIXTURE);
    await page.waitForTimeout(200);
    const scrollWidth = await page.evaluate(() => document.documentElement.scrollWidth);
    const clientWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(scrollWidth).toBe(clientWidth);
  });

  test('hostile project title, institution, PI name, and briefing render as inert text', async ({ page }) => {
    const dialogs = [];
    const pageErrors = [];
    page.on('dialog', (d) => { dialogs.push(d.message()); d.dismiss(); });
    page.on('pageerror', (e) => pageErrors.push(e.message));

    await page.goto(HOSTILE_FIXTURE);
    await page.waitForTimeout(400);

    const flags = await page.evaluate(() => ({
      xss: window.__xss, xss2: window.__xss2, xss3: window.__xss3,
      xss4: window.__xss4, xss5: window.__xss5,
    }));
    expect(flags).toEqual({});

    expect(await page.locator('script').count()).toBe(3);
    expect(await page.locator('img').count()).toBe(0);
    expect(dialogs).toEqual([]);
    expect(pageErrors).toEqual([]);

    const titleCell = await page.locator('#projectsBody tr td').nth(3).innerText();
    expect(titleCell).toContain('<script>window.__xss=true;</script>');
  });
});

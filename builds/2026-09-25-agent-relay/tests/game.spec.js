const { test, expect } = require('@playwright/test');
const path = require('path');

const URL = 'file://' + path.join(__dirname, '..', 'index.html');

async function gotoFresh(page) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e)));
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });
  await page.goto(URL);
  return errors;
}

// Completes whatever level is currently in view-play by always taking the
// first ready task and dropping it on the first available lane. Doesn't aim
// for optimal — just a fast, shape-agnostic way to reach a valid complete
// schedule so Submit becomes enabled.
async function placeAllTasksGreedily(page) {
  for (let guard = 0; guard < 30; guard++) {
    const submitBtn = page.getByTestId('btn-submit');
    if (await submitBtn.isEnabled()) return;
    const readyCards = page.locator('#ready-tray [data-testid^="ready-"]');
    if ((await readyCards.count()) === 0) return;
    await readyCards.first().click();
    const lanes = page.locator('[data-testid^="lane-"]');
    const laneCount = await lanes.count();
    for (let i = 0; i < laneCount; i++) {
      const lane = lanes.nth(i);
      if (await lane.isEnabled()) {
        await lane.click();
        break;
      }
    }
  }
  throw new Error('placeAllTasksGreedily did not converge');
}

test.describe('home screen', () => {
  test('loads with the three primary actions visible and zero errors', async ({ page }) => {
    const errors = await gotoFresh(page);
    await expect(page.getByTestId('btn-tutorial')).toBeVisible();
    await expect(page.getByTestId('btn-campaign')).toBeVisible();
    await expect(page.getByTestId('btn-daily')).toBeVisible();
    await expect(page.getByTestId('daily-status')).toContainText('Streak');
    expect(errors).toEqual([]);
  });
});

test.describe('tutorial', () => {
  test('walks through placement and updates the guidance banner at each step', async ({ page }) => {
    await gotoFresh(page);
    await page.getByTestId('btn-tutorial').click();
    await expect(page.getByTestId('tutorial-banner')).toContainText('Clone Repository');

    await page.getByTestId('ready-A').click();
    await page.getByTestId('lane-0').click();
    await expect(page.getByTestId('tutorial-banner')).toContainText('Step 2');

    await page.getByTestId('ready-B').click();
    await page.getByTestId('lane-0').click();
    await expect(page.getByTestId('tutorial-banner')).toContainText('Step 3');

    await page.getByTestId('ready-C').click();
    await page.getByTestId('lane-1').click();
    await expect(page.getByTestId('tutorial-banner')).toContainText('All tasks placed');
    await expect(page.getByTestId('btn-submit')).toBeEnabled();
  });

  test('reaching the true optimal placement earns a Gold grade', async ({ page }) => {
    await gotoFresh(page);
    await page.getByTestId('btn-tutorial').click();

    await page.getByTestId('ready-A').click();
    await page.getByTestId('lane-0').click();
    // B and C must land on different lanes to hit the optimal makespan of 7.
    await page.getByTestId('ready-B').click();
    await page.getByTestId('lane-0').click();
    await page.getByTestId('ready-C').click();
    await page.getByTestId('lane-1').click();

    await expect(page.getByTestId('btn-submit')).toBeEnabled();
    await page.getByTestId('btn-submit').click();

    await expect(page.getByTestId('result-grade')).toContainText('Gold');
    await expect(page.getByTestId('result-summary')).toContainText('Your time: 7m');
    await expect(page.getByTestId('result-summary')).toContainText('Optimal: 7m');
  });

  test('a valid but suboptimal placement shows the correct non-gold grade and exact time', async ({ page }) => {
    await gotoFresh(page);
    await page.getByTestId('btn-tutorial').click();

    // Stack everything on lane 0: fully serial 3+4+3 = 10, optimal is 7 (margin 2) -> bronze.
    await page.getByTestId('ready-A').click();
    await page.getByTestId('lane-0').click();
    await page.getByTestId('ready-B').click();
    await page.getByTestId('lane-0').click();
    await page.getByTestId('ready-C').click();
    await page.getByTestId('lane-0').click();

    await page.getByTestId('btn-submit').click();
    await expect(page.getByTestId('result-grade')).toContainText('Bronze');
    await expect(page.getByTestId('result-summary')).toContainText('Your time: 10m');
    await expect(page.getByTestId('result-summary')).toContainText('(+3m)');
  });
});

test.describe('placement interaction', () => {
  test('selecting a ready task then clicking a lane moves it out of the ready tray', async ({ page }) => {
    await gotoFresh(page);
    await page.getByTestId('btn-tutorial').click();
    await expect(page.getByTestId('ready-A')).toBeVisible();

    await page.getByTestId('ready-A').click();
    await expect(page.getByTestId('ready-A')).toHaveClass(/selected/);
    await page.getByTestId('lane-0').click();

    await expect(page.getByTestId('ready-A')).toHaveCount(0);
    await expect(page.getByTestId('lane-0')).toContainText('Clone Repository');
    await expect(page.getByTestId('live-makespan')).toContainText('Time so far: 3m');
  });

  test('lanes are disabled until a task is selected', async ({ page }) => {
    await gotoFresh(page);
    await page.getByTestId('btn-tutorial').click();
    await expect(page.getByTestId('lane-0')).toBeDisabled();
    await page.getByTestId('ready-A').click();
    await expect(page.getByTestId('lane-0')).toBeEnabled();
  });

  test('Reset clears all placements and returns tasks to Ready', async ({ page }) => {
    await gotoFresh(page);
    await page.getByTestId('btn-tutorial').click();
    await page.getByTestId('ready-A').click();
    await page.getByTestId('lane-0').click();
    await expect(page.getByTestId('ready-A')).toHaveCount(0);

    await page.getByTestId('btn-reset').click();
    await expect(page.getByTestId('ready-A')).toBeVisible();
    await expect(page.getByTestId('live-makespan')).toContainText('Time so far: 0m');
    await expect(page.getByTestId('btn-submit')).toBeDisabled();
  });

  test('Submit stays disabled until every task is placed', async ({ page }) => {
    await gotoFresh(page);
    await page.getByTestId('btn-tutorial').click();
    await expect(page.getByTestId('btn-submit')).toBeDisabled();
    await page.getByTestId('ready-A').click();
    await page.getByTestId('lane-0').click();
    await expect(page.getByTestId('btn-submit')).toBeDisabled();
    await placeAllTasksGreedily(page);
    await expect(page.getByTestId('btn-submit')).toBeEnabled();
  });
});

test.describe('campaign', () => {
  test('only the first level is unlocked initially; completing it unlocks the second', async ({ page }) => {
    await gotoFresh(page);
    await page.getByTestId('btn-campaign').click();
    await expect(page.getByTestId('level-btn-L1')).toBeEnabled();
    await expect(page.getByTestId('level-btn-L2')).toBeDisabled();

    await page.getByTestId('level-btn-L1').click();
    await placeAllTasksGreedily(page);
    await page.getByTestId('btn-submit').click();
    await page.getByTestId('btn-back-menu').click();

    await page.getByTestId('btn-campaign').click();
    await expect(page.getByTestId('level-btn-L2')).toBeEnabled();
  });

  test('Dashboard keeps the best (lowest) makespan across repeated plays, never a worse one', async ({ page }) => {
    await gotoFresh(page);
    await page.getByTestId('btn-campaign').click();
    await page.getByTestId('level-btn-L1').click();

    // Worse: fully serial on lane 0 -> makespan 12.
    await page.getByTestId('ready-A').click();
    await page.getByTestId('lane-0').click();
    await page.getByTestId('ready-B').click();
    await page.getByTestId('lane-0').click();
    await page.getByTestId('ready-C').click();
    await page.getByTestId('lane-0').click();
    await page.getByTestId('ready-D').click();
    await page.getByTestId('lane-0').click();
    await page.getByTestId('btn-submit').click();
    await expect(page.getByTestId('result-summary')).toContainText('Your time: 12m');

    await page.getByTestId('btn-play-again').click();
    // Better: the true optimal assignment -> makespan 9.
    await page.getByTestId('ready-A').click();
    await page.getByTestId('lane-0').click();
    await page.getByTestId('ready-C').click();
    await page.getByTestId('lane-1').click();
    await page.getByTestId('ready-B').click();
    await page.getByTestId('lane-0').click();
    await page.getByTestId('ready-D').click();
    await page.getByTestId('lane-0').click();
    await page.getByTestId('btn-submit').click();
    await expect(page.getByTestId('result-summary')).toContainText('Your time: 9m');
    await expect(page.getByTestId('result-grade')).toContainText('Gold');

    await page.getByTestId('btn-back-menu').click();
    await page.getByTestId('nav-dashboard').click();
    await expect(page.getByTestId('dashboard-L1')).toContainText('9m');
    await expect(page.getByTestId('dashboard-L1')).not.toContainText('12m');
  });
});

test.describe('daily challenge', () => {
  test('completing it once gates further attempts and shows a share string', async ({ page }) => {
    await gotoFresh(page);
    await page.getByTestId('btn-daily').click();
    await placeAllTasksGreedily(page);
    await page.getByTestId('btn-submit').click();

    await expect(page.getByTestId('result-grade')).toBeVisible();
    await expect(page.getByTestId('daily-share')).toContainText('Agent Relay Daily');
    await expect(page.getByTestId('btn-play-again')).not.toBeVisible();

    await page.getByTestId('btn-back-menu').click();
    await expect(page.getByTestId('daily-status')).toContainText("Today's challenge complete");

    // Clicking Daily Challenge again re-shows today's result instead of starting a new attempt.
    await page.getByTestId('btn-daily').click();
    await expect(page.getByTestId('result-grade')).toBeVisible();
    await expect(page.getByTestId('daily-share')).toContainText('Agent Relay Daily');
  });
});

test.describe('mobile layout', () => {
  test('no horizontal overflow at a 375px viewport during play', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 700 });
    await gotoFresh(page);
    await page.getByTestId('btn-tutorial').click();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
});

test.describe('AI Mission Debrief panel', () => {
  test('shows the deterministic fallback note with zero network calls when no key is entered', async ({ page }) => {
    let requestSeen = false;
    await page.route('https://api.anthropic.com/**', (route) => {
      requestSeen = true;
      route.abort();
    });
    await gotoFresh(page);
    await page.getByTestId('btn-tutorial').click();
    await placeAllTasksGreedily(page);
    await page.getByTestId('btn-submit').click();

    await page.getByTestId('btn-get-debrief').click();
    await expect(page.getByTestId('ai-note')).not.toHaveText('');
    await expect(page.getByTestId('ai-note')).not.toHaveText('Thinking…');
    expect(requestSeen).toBe(false);
  });

  test('renders a mocked API response through textContent only', async ({ page }) => {
    await page.route('https://api.anthropic.com/**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ content: [{ text: 'Solid run — the second lane closed the gap nicely.' }] }),
      });
    });
    await gotoFresh(page);
    await page.getByTestId('btn-tutorial').click();
    await placeAllTasksGreedily(page);
    await page.getByTestId('btn-submit').click();

    await page.getByTestId('ai-key-input').fill('sk-test-not-real');
    await page.getByTestId('btn-get-debrief').click();
    await expect(page.getByTestId('ai-note')).toHaveText('Solid run — the second lane closed the gap nicely.');
  });
});

test.describe('full playthrough', () => {
  test('home -> campaign -> level -> submit -> result produces zero console/page errors', async ({ page }) => {
    const errors = await gotoFresh(page);
    await page.getByTestId('btn-campaign').click();
    await page.getByTestId('level-btn-L1').click();
    await placeAllTasksGreedily(page);
    await page.getByTestId('btn-submit').click();
    await expect(page.getByTestId('result-grade')).toBeVisible();
    expect(errors).toEqual([]);
  });
});

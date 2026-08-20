const path = require('path');
const { test, expect } = require('@playwright/test');

// engine.js and course-data.js attach to `globalThis` when there is no
// `window` (i.e. under Node), so requiring them here gives this spec file
// direct access to the exact same physics/scoring logic the browser loads
// via <script> — not a reimplementation, the same file.
require(path.join(__dirname, '..', 'src', 'engine.js'));
require(path.join(__dirname, '..', 'src', 'course-data.js'));
const Engine = global.FairwayEngine;
const Course = global.COURSE;

const PAGE_URL = 'file://' + path.join(__dirname, '..', 'index.html');

async function freshPage(page) {
  await page.goto(PAGE_URL);
  await page.evaluate(() => localStorage.clear());
  await page.reload();
}

// Searches integer power values (100 -> 0) for the first shot that
// satisfies `predicate`, using the real engine — the same search a human
// player does by trial and error, just automated so the test never has to
// hand-derive a "magic number" power value.
function findShotByPower(hole, fromPos, club, predicate) {
  for (let power = 100; power >= 0; power--) {
    const result = Engine.resolveShot(
      { position: fromPos },
      { club, powerPct: power, aimDeg: 0, shape: 'straight', windSpeedMph: 0, windDirectionDeg: 0 },
      hole
    );
    if (predicate(result)) {
      return { power, result };
    }
  }
  return null;
}

function findPuttByPower(hole, fromPos) {
  for (let power = 0; power <= 100; power++) {
    const result = Engine.resolvePutt(fromPos, hole, { powerPct: power, aimDeg: 0 });
    if (result.holed) {
      return { power, result };
    }
  }
  return null;
}

test.describe('Engine — carry distance and power scaling', () => {
  test('carry distance scales linearly with power off documented club bases', () => {
    expect(Engine.computeCarryDistance('driver', 100)).toBeCloseTo(230, 5);
    expect(Engine.computeCarryDistance('driver', 50)).toBeCloseTo(115, 5);
    expect(Engine.computeCarryDistance('pw', 0)).toBeCloseTo(0, 5);
    expect(Engine.computeCarryDistance('eightiron', 100)).toBeCloseTo(145, 5);
  });
});

test.describe('Engine — wind effects', () => {
  test('a headwind (180°) reduces distance and adds no lateral drift', () => {
    const wind = Engine.computeWindEffect(200, 10, 180, 'driver');
    expect(wind.distanceDelta).toBeCloseTo(-15, 5);
    expect(wind.lateralDrift).toBeCloseTo(0, 5);
  });

  test('a tailwind (0°) increases distance', () => {
    const wind = Engine.computeWindEffect(200, 10, 0, 'driver');
    expect(wind.distanceDelta).toBeCloseTo(15, 5);
  });

  test('crosswinds from opposite directions produce opposite-signed lateral drift', () => {
    const leftToRight = Engine.computeWindEffect(200, 10, 90, 'driver');
    const rightToLeft = Engine.computeWindEffect(200, 10, 270, 'driver');
    expect(leftToRight.lateralDrift).toBeGreaterThan(0);
    expect(rightToLeft.lateralDrift).toBeCloseTo(-leftToRight.lateralDrift, 5);
  });
});

test.describe('Engine — elevation, shot shape, and roll', () => {
  test('uphill reduces effective distance, downhill increases it', () => {
    expect(Engine.computeElevationEffect(10)).toBeCloseTo(-3.3, 5);
    expect(Engine.computeElevationEffect(-5)).toBeCloseTo(1.65, 5);
  });

  test('draw curves left (negative), fade curves right (positive), straight has no curve', () => {
    expect(Engine.computeShotShapeCurve('draw', 230, 'driver')).toBeCloseTo(-18, 5);
    expect(Engine.computeShotShapeCurve('fade', 115, 'driver')).toBeCloseTo(9, 5);
    expect(Engine.computeShotShapeCurve('straight', 230, 'driver')).toBe(0);
  });

  test('roll is zero in bunker/water, reduced in rough, full on fairway', () => {
    expect(Engine.computeRoll(200, 'driver', 'bunker')).toBe(0);
    expect(Engine.computeRoll(200, 'driver', 'water')).toBe(0);
    expect(Engine.computeRoll(200, 'driver', 'rough')).toBeCloseTo(200 * 0.15 * 0.4, 5);
    expect(Engine.computeRoll(200, 'driver', 'fairway')).toBeCloseTo(200 * 0.15, 5);
  });
});

test.describe('Engine — lie classification priority', () => {
  const fixtureHole = {
    yardage: 300,
    pin: { x: 0, y: 300 },
    greenRadius: 8,
    zones: [
      { type: 'bunker', xMin: -10, xMax: -2, yMin: 295, yMax: 305 },
      { type: 'water', xMin: 50, xMax: 70, yMin: 100, yMax: 120 },
      { type: 'fairway', xMin: -20, xMax: 20, yMin: 0, yMax: 300 },
      { type: 'rough', xMin: -40, xMax: 40, yMin: -10, yMax: 310 }
    ]
  };

  test('classifies fairway, rough, bunker, and water correctly', () => {
    expect(Engine.classifyLie({ x: 0, y: 150 }, fixtureHole)).toBe('fairway');
    expect(Engine.classifyLie({ x: 30, y: 150 }, fixtureHole)).toBe('rough');
    expect(Engine.classifyLie({ x: 60, y: 110 }, fixtureHole)).toBe('water');
    expect(Engine.classifyLie({ x: -6, y: 299 }, fixtureHole)).toBe('bunker');
  });

  test('the green circle wins over an overlapping fairway rectangle, but a greenside bunker still wins over the green circle', () => {
    // (0, 300) is the pin itself: inside the fairway rectangle (x -20..20,
    // y 0..300) AND inside the green circle. Green must win.
    expect(Engine.classifyLie({ x: 0, y: 300 }, fixtureHole)).toBe('green');
    // (-6, 299) is inside the green circle (distance ~6.1 <= 8) AND inside
    // the bunker rectangle. The bunker must still win.
    expect(Engine.classifyLie({ x: -6, y: 299 }, fixtureHole)).toBe('bunker');
  });

  test('a point far outside every zone and the playing corridor is OB', () => {
    expect(Engine.classifyLie({ x: 200, y: 150 }, fixtureHole)).toBe('ob');
    expect(Engine.classifyLie({ x: 0, y: 500 }, fixtureHole)).toBe('ob');
  });
});

test.describe('Engine — shot resolution, penalties, and putting', () => {
  test('a shot landing in water triggers a stroke-and-distance penalty and does not move the ball', () => {
    const hole = {
      yardage: 200,
      pin: { x: 0, y: 200 },
      greenRadius: 8,
      zones: [{ type: 'water', xMin: -20, xMax: 20, yMin: 90, yMax: 110 }, { type: 'fairway', xMin: -20, xMax: 20, yMin: 0, yMax: 200 }]
    };
    const start = { x: 0, y: 0 };
    const result = Engine.resolveShot(
      { position: start },
      { club: 'eightiron', powerPct: 69, aimDeg: 0, shape: 'straight', windSpeedMph: 0, windDirectionDeg: 0 },
      hole
    );
    expect(result.penalty).toBe(true);
    expect(result.finalLie).toBe('water');
    expect(result.resultPosition).toEqual(start);
  });

  test('a putt within the capture radius holes out; one that overshoots does not', () => {
    const hole = { yardage: 100, pin: { x: 0, y: 100 }, greenRadius: 8, greenBreakYd: 0, zones: [] };
    const closeAttempt = Engine.resolvePutt({ x: 0, y: 96 }, hole, { powerPct: (4 / 15) * 100, aimDeg: 0 });
    expect(closeAttempt.holed).toBe(true);

    const shortAttempt = Engine.resolvePutt({ x: 0, y: 80 }, hole, { powerPct: 10, aimDeg: 0 });
    expect(shortAttempt.holed).toBe(false);
    expect(shortAttempt.distanceToPin).toBeGreaterThan(0.5);
  });
});

test.describe('Engine — scoring and daily seed', () => {
  test('scoreHole maps strokes-to-par into standard golf labels', () => {
    expect(Engine.scoreHole(2, 4).label).toBe('Eagle');
    expect(Engine.scoreHole(3, 4).label).toBe('Birdie');
    expect(Engine.scoreHole(4, 4).label).toBe('Par');
    expect(Engine.scoreHole(5, 4).label).toBe('Bogey');
    expect(Engine.scoreHole(6, 4).label).toBe('Double Bogey');
    expect(Engine.scoreHole(8, 4).label).toBe('Triple Bogey+');
  });

  test('dailySeed is deterministic for the same date and hole, and stays within valid ranges', () => {
    const a = Engine.dailySeed('2026-08-20', 3);
    const b = Engine.dailySeed('2026-08-20', 3);
    expect(a).toEqual(b);
    expect(a.windSpeedMph).toBeGreaterThanOrEqual(0);
    expect(a.windSpeedMph).toBeLessThanOrEqual(20);
    expect(a.windDirectionDeg).toBeGreaterThanOrEqual(0);
    expect(a.windDirectionDeg).toBeLessThan(360);
  });
});

test.describe('Course data integrity', () => {
  test('all 9 holes have valid tee/pin/zone data', () => {
    expect(Course.length).toBe(9);
    Course.forEach((hole) => {
      expect(hole.tee).toEqual({ x: 0, y: 0 });
      expect(hole.pin.y).toBe(hole.yardage);
      expect([3, 4, 5]).toContain(hole.par);
      expect(hole.greenRadius).toBeGreaterThan(0);
      expect(Array.isArray(hole.zones)).toBe(true);
      expect(hole.zones.length).toBeGreaterThan(0);
    });
  });
});

test.describe('UI — mode screen', () => {
  test('loads with mode selection visible and 9 practice holes listed', async ({ page }) => {
    await freshPage(page);
    await expect(page.getByTestId('mode-screen')).toBeVisible();
    await expect(page.getByTestId('mode-daily-btn')).toBeVisible();
    await expect(page.getByTestId('practice-hole-select').locator('option')).toHaveCount(9);
  });
});

test.describe('UI — Daily Round determinism and gating', () => {
  test('the same UTC date produces the same wind on reload', async ({ page }) => {
    await freshPage(page);
    await page.getByTestId('mode-daily-btn').click();
    const firstWind = await page.getByTestId('wind-display').textContent();

    await page.reload();
    await page.getByTestId('mode-daily-btn').click();
    const secondWind = await page.getByTestId('wind-display').textContent();

    expect(firstWind).toBe(secondWind);
  });

  test('a completed Daily Round for today is gated behind a "View Today\'s Result" button', async ({ page }) => {
    await freshPage(page);
    const today = await page.evaluate(() => {
      const d = new Date();
      const pad = (n) => (n < 10 ? '0' + n : String(n));
      return d.getUTCFullYear() + '-' + pad(d.getUTCMonth() + 1) + '-' + pad(d.getUTCDate());
    });
    const fakeRecord = {
      completed: true,
      dateStr: today,
      total: -1,
      scorecard: [{ holeId: 1, name: 'Cedar Opener', par: 4, strokes: 3, label: 'Birdie', delta: -1 }]
    };
    await page.evaluate(
      ({ key, record }) => localStorage.setItem(key, JSON.stringify(record)),
      { key: 'fairwayphysics_daily_' + today, record: fakeRecord }
    );
    await page.reload();

    await expect(page.getByTestId('mode-daily-btn')).toBeHidden();
    await expect(page.getByTestId('daily-completed-message')).toBeVisible();
    await expect(page.getByTestId('view-daily-result-btn')).toBeVisible();

    await page.getByTestId('view-daily-result-btn').click();
    await expect(page.getByTestId('scorecard-panel')).toBeVisible();
    await expect(page.getByTestId('round-total')).toHaveText('-1');
  });

  test('Practice mode remains available and independent even when the Daily Round is already completed', async ({ page }) => {
    await freshPage(page);
    const today = await page.evaluate(() => {
      const d = new Date();
      const pad = (n) => (n < 10 ? '0' + n : String(n));
      return d.getUTCFullYear() + '-' + pad(d.getUTCMonth() + 1) + '-' + pad(d.getUTCDate());
    });
    await page.evaluate(
      ({ key }) =>
        localStorage.setItem(
          key,
          JSON.stringify({ completed: true, dateStr: key, total: 0, scorecard: [] })
        ),
      { key: 'fairwayphysics_daily_' + today }
    );
    await page.reload();

    await page.getByTestId('practice-start-btn').click();
    await expect(page.getByTestId('game-screen')).toBeVisible();
    await expect(page.getByTestId('lie-label')).toHaveText('tee');
    await expect(page.getByTestId('shot-controls')).toBeVisible();
  });
});

test.describe('UI — full hole playthrough', () => {
  test('a searched shot plan holes out on Hole 1 with the score the engine predicts', async ({ page }) => {
    const hole = Course[0];
    const teeShot = Engine.resolveShot(
      { position: hole.tee },
      { club: 'driver', powerPct: 100, aimDeg: 0, shape: 'straight', windSpeedMph: 0, windDirectionDeg: 0 },
      hole
    );
    expect(teeShot.penalty).toBe(false);

    const approach = findShotByPower(hole, teeShot.resultPosition, 'eightiron', (r) => !r.penalty && r.finalLie === 'green');
    expect(approach).not.toBeNull();

    const putt = findPuttByPower(hole, approach.result.resultPosition);
    expect(putt).not.toBeNull();

    const expectedScore = Engine.scoreHole(3, hole.par);

    await freshPage(page);
    await page.getByTestId('practice-hole-select').selectOption('0');
    await page.getByTestId('practice-start-btn').click();

    await page.getByTestId('club-select').selectOption('driver');
    await page.getByTestId('power-slider').fill('100');
    await page.getByTestId('aim-slider').fill('0');
    await page.getByTestId('shape-select').selectOption('straight');
    await page.getByTestId('shot-btn').click();
    await expect(page.getByTestId('stroke-count')).toHaveText('2');
    await expect(page.getByTestId('lie-label')).toHaveText(teeShot.finalLie);

    await page.getByTestId('club-select').selectOption('eightiron');
    await page.getByTestId('power-slider').fill(String(approach.power));
    await page.getByTestId('shot-btn').click();
    await expect(page.getByTestId('lie-label')).toHaveText('green');
    await expect(page.getByTestId('putt-controls')).toBeVisible();
    await expect(page.getByTestId('shot-controls')).toBeHidden();

    await page.getByTestId('putt-power-slider').fill(String(putt.power));
    await page.getByTestId('putt-aim-slider').fill('0');
    await page.getByTestId('putt-btn').click();

    await expect(page.getByTestId('hole-complete-panel')).toBeVisible();
    await expect(page.getByTestId('hole-result-label')).toContainText(expectedScore.label);
    await expect(page.getByTestId('hole-result-label')).toContainText('3 strokes');

    await page.getByTestId('continue-btn').click();
    await expect(page.getByTestId('mode-screen')).toBeVisible();
    const stats = await page.evaluate(() => JSON.parse(localStorage.getItem('fairwayphysics_stats')));
    expect(stats.practiceAttempts).toBe(1);
    expect(stats.totalStrokesByHole[0]).toEqual([3]);
  });

  test('a shot found to land in water applies a stroke-and-distance penalty in the UI', async ({ page }) => {
    const hole = Course[1];
    const penaltyShot = findShotByPower(hole, hole.tee, 'eightiron', (r) => r.penalty && r.finalLie === 'water');
    expect(penaltyShot).not.toBeNull();

    await freshPage(page);
    await page.getByTestId('practice-hole-select').selectOption('1');
    await page.getByTestId('practice-start-btn').click();

    await page.getByTestId('club-select').selectOption('eightiron');
    await page.getByTestId('power-slider').fill(String(penaltyShot.power));
    await page.getByTestId('aim-slider').fill('0');
    await page.getByTestId('shape-select').selectOption('straight');
    await page.getByTestId('shot-btn').click();

    await expect(page.getByTestId('shot-message')).toContainText('Penalty');
    await expect(page.getByTestId('stroke-count')).toHaveText('3');
    await expect(page.getByTestId('lie-label')).toHaveText('tee');
  });
});

test.describe('UI — stats persistence', () => {
  test('injected localStorage stats render correctly after reload', async ({ page }) => {
    await freshPage(page);
    await page.evaluate(() => {
      const stats = {
        roundsCompleted: 4,
        bestRoundScore: -2,
        totalStrokesByHole: [[4, 5], [3], [], [], [], [], [], [], []],
        practiceAttempts: 7
      };
      localStorage.setItem('fairwayphysics_stats', JSON.stringify(stats));
    });
    await page.reload();

    await page.getByTestId('stats-btn').click();
    await expect(page.getByTestId('stats-panel')).toBeVisible();
    await expect(page.getByTestId('rounds-completed')).toHaveText('4');
    await expect(page.getByTestId('best-round-score')).toHaveText('-2');
    await expect(page.getByTestId('practice-attempts')).toHaveText('7');
  });
});

test.describe('UI — AI caddie safety and fallback', () => {
  test('renders a deterministic fallback tip with zero network calls when no API key is set', async ({ page }) => {
    await freshPage(page);
    let apiCalled = false;
    await page.route('https://api.anthropic.com/v1/messages', (route) => {
      apiCalled = true;
      route.abort();
    });

    await page.getByTestId('practice-start-btn').click();
    await page.getByTestId('caddie-btn').click();

    const tipText = await page.getByTestId('caddie-tip').textContent();
    expect(tipText.length).toBeGreaterThan(0);
    expect(apiCalled).toBe(false);
  });

  test('renders a mocked successful API response as the tip text', async ({ page }) => {
    await freshPage(page);
    await page.route('https://api.anthropic.com/v1/messages', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ content: [{ text: 'Lay up short of the water and take your medicine.' }] })
      });
    });

    await page.getByTestId('practice-start-btn').click();
    await page.getByTestId('api-key-input').fill('sk-ant-test-key');
    await page.getByTestId('caddie-btn').click();

    await expect(page.getByTestId('caddie-tip')).toHaveText('Lay up short of the water and take your medicine.');
  });

  test('an injected script/img payload in the caddie response renders as inert text, never executes', async ({ page }) => {
    await freshPage(page);
    const payload = '<img src=x onerror="window.__xssFired=1"></script><script>window.__xssFired2=1</script>';
    await page.route('https://api.anthropic.com/v1/messages', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ content: [{ text: payload }] })
      });
    });

    const dialogs = [];
    page.on('dialog', (d) => {
      dialogs.push(d.message());
      d.dismiss();
    });

    await page.getByTestId('practice-start-btn').click();
    await page.getByTestId('api-key-input').fill('sk-ant-test-key');
    await page.getByTestId('caddie-btn').click();

    await expect(page.getByTestId('caddie-tip')).toHaveText(payload);
    expect(dialogs.length).toBe(0);
    const fired = await page.evaluate(() => Boolean(window.__xssFired || window.__xssFired2));
    expect(fired).toBe(false);
    const injectedImgCount = await page.locator('#caddieTip img').count();
    expect(injectedImgCount).toBe(0);
  });
});

test.describe('UI — canvas rendering', () => {
  test('a fairway zone renders in a visibly distinct color from the surrounding rough, not painted over by it', async ({ page }) => {
    // Regression test: drawCourse used to paint zones in course-data array
    // order, so the broader 'rough' rectangle (declared after 'fairway')
    // fully overpainted the narrower fairway strip on every hole. Fixed by
    // drawing in a fixed hazard-over-corridor priority order regardless of
    // array order — this checks the actual rendered pixels, not just the
    // classifyLie logic, since the bug was in rendering, not lie lookup.
    await freshPage(page);
    await page.getByTestId('practice-hole-select').selectOption('0');
    await page.getByTestId('practice-start-btn').click();

    const colors = await page.evaluate(() => {
      const canvas = document.getElementById('courseCanvas');
      const ctx = canvas.getContext('2d');
      const center = ctx.getImageData(180, 260, 1, 1).data; // hole centerline, mid-fairway
      const edge = ctx.getImageData(20, 260, 1, 1).data; // far left, should stay rough
      return {
        center: [center[0], center[1], center[2]],
        edge: [edge[0], edge[1], edge[2]]
      };
    });

    expect(colors.center).toEqual([76, 175, 107]); // fairway green
    expect(colors.edge).toEqual([127, 159, 95]); // rough green
    expect(colors.center).not.toEqual(colors.edge);
  });
});

test.describe('UI — mobile viewport', () => {
  test('renders the course canvas and shot controls without breaking at 375px width', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 700 });
    await freshPage(page);
    await page.getByTestId('mode-daily-btn').click();

    await expect(page.getByTestId('course-canvas')).toBeVisible();
    await expect(page.getByTestId('shot-controls')).toBeVisible();
    const bodyScrollWidth = await page.evaluate(() => document.body.scrollWidth);
    expect(bodyScrollWidth).toBeLessThanOrEqual(376);
  });
});

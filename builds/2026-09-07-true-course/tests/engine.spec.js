const { test, expect } = require('@playwright/test');
const path = require('path');

const INDEX_URL = `file://${path.resolve(__dirname, '../index.html')}`;

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => localStorage.clear());
  await page.goto(INDEX_URL);
});

/* ================================================================
   Set & Drift — current-triangle course-to-steer
================================================================ */

test('zero current: heading equals track and SOG equals boat speed', async ({ page }) => {
  const result = await page.evaluate(() =>
    TC.courseToSteer({ trackDeg: 90, distanceNm: 20, boatSpeedKts: 8, setDeg: 0, driftKts: 0 })
  );
  expect(result.solvable).toBe(true);
  expect(result.headingDeg).toBeCloseTo(90, 5);
  expect(result.sogKts).toBeCloseTo(8, 5);
});

test('current setting exactly along the track adds directly to SOG with no correction', async ({ page }) => {
  const result = await page.evaluate(() =>
    TC.courseToSteer({ trackDeg: 45, distanceNm: 10, boatSpeedKts: 6, setDeg: 45, driftKts: 2 })
  );
  expect(result.solvable).toBe(true);
  expect(result.correctionDeg).toBeCloseTo(0, 5);
  expect(result.sogKts).toBeCloseTo(8, 5);
});

test('current setting directly against the track subtracts from SOG with no correction', async ({ page }) => {
  const result = await page.evaluate(() =>
    TC.courseToSteer({ trackDeg: 200, distanceNm: 10, boatSpeedKts: 9, setDeg: 20, driftKts: 3 })
  );
  expect(result.solvable).toBe(true);
  expect(result.correctionDeg).toBeCloseTo(0, 5);
  expect(result.sogKts).toBeCloseTo(6, 5);
});

test('cross-current course-to-steer reconstructs a resultant vector pointing exactly along the track', async ({ page }) => {
  const check = await page.evaluate(() => {
    const params = { trackDeg: 70, distanceNm: 15, boatSpeedKts: 7, setDeg: 340, driftKts: 2.5 };
    const result = TC.courseToSteer(params);
    // Independently reconstruct the resultant vector from the computed heading
    // and given current, then verify its bearing matches the desired track.
    const hRad = TC.toRad(result.headingDeg);
    const sRad = TC.toRad(params.setDeg);
    const vx = params.boatSpeedKts * Math.sin(hRad) + params.driftKts * Math.sin(sRad);
    const vy = params.boatSpeedKts * Math.cos(hRad) + params.driftKts * Math.cos(sRad);
    const resultantBearing = TC.normalizeDeg(TC.toDeg(Math.atan2(vx, vy)));
    const resultantSpeed = Math.sqrt(vx * vx + vy * vy);
    return {
      solvable: result.solvable,
      bearingDiff: TC.angularDistance(resultantBearing, params.trackDeg),
      speedDiff: Math.abs(resultantSpeed - result.sogKts),
    };
  });
  expect(check.solvable).toBe(true);
  expect(check.bearingDiff).toBeLessThan(0.01);
  expect(check.speedDiff).toBeLessThan(0.01);
});

test('current too strong to hold the track is reported unsolvable, not NaN', async ({ page }) => {
  const result = await page.evaluate(() =>
    TC.courseToSteer({ trackDeg: 0, distanceNm: 10, boatSpeedKts: 4, setDeg: 90, driftKts: 6 })
  );
  expect(result.solvable).toBe(false);
  expect(Number.isNaN(result.headingDeg)).toBe(false); // headingDeg is simply absent, never NaN
});

/* ================================================================
   Tide Window — cosine interpolation
================================================================ */

test('tide height model reproduces the exact low and high boundary values', async ({ page }) => {
  const result = await page.evaluate(() => ({
    atLow: TC.tideHeight(2, 2, 0.5, 8, 3.2),
    atHigh: TC.tideHeight(8, 2, 0.5, 8, 3.2),
    atMid: TC.tideHeight(5, 2, 0.5, 8, 3.2),
  }));
  expect(result.atLow).toBeCloseTo(0.5, 6);
  expect(result.atHigh).toBeCloseTo(3.2, 6);
  expect(result.atMid).toBeCloseTo((0.5 + 3.2) / 2, 6);
});

test('tide window: requiredHeight at or below the low tide is always passable', async ({ page }) => {
  const result = await page.evaluate(() =>
    TC.tideWindowStart({ t0: 3, h0: 1.0, t1: 9, h1: 3.0, requiredHeight: 0.8 })
  );
  expect(result.status).toBe('always');
  expect(result.startTime).toBe(3);
});

test('tide window: requiredHeight above the high tide is never reached', async ({ page }) => {
  const result = await page.evaluate(() =>
    TC.tideWindowStart({ t0: 3, h0: 1.0, t1: 9, h1: 3.0, requiredHeight: 3.5 })
  );
  expect(result.status).toBe('never');
  expect(result.startTime).toBeNull();
});

test('tide window: computed crossing time satisfies the height equation exactly', async ({ page }) => {
  const check = await page.evaluate(() => {
    const params = { t0: 4, h0: 0.4, t1: 10.3, h1: 2.9, requiredHeight: 1.7 };
    const result = TC.tideWindowStart(params);
    const heightAtStart = TC.tideHeight(result.startTime, params.t0, params.h0, params.t1, params.h1);
    return { status: result.status, diff: Math.abs(heightAtStart - params.requiredHeight) };
  });
  expect(check.status).toBe('window');
  expect(check.diff).toBeLessThan(1e-9);
});

/* ================================================================
   Right of Way — COLREGS classifier
================================================================ */

test('reciprocal headings meeting dead ahead classify as head-on with both giving way', async ({ page }) => {
  const result = await page.evaluate(() =>
    TC.classifyEncounter({ yourHeadingDeg: 0, otherHeadingDeg: 180, bearingToOtherDeg: 0 })
  );
  expect(result.type).toBe('head-on');
  expect(result.giveWay).toBe('both');
});

test('other vessel on your starboard bow is a crossing situation and you give way', async ({ page }) => {
  const result = await page.evaluate(() =>
    TC.classifyEncounter({ yourHeadingDeg: 0, otherHeadingDeg: 270, bearingToOtherDeg: 45 })
  );
  expect(result.type).toBe('crossing');
  expect(result.giveWay).toBe('you');
});

test('right-of-way classification is symmetric when the two vessels are swapped', async ({ page }) => {
  const check = await page.evaluate(() => {
    const a = TC.classifyEncounter({ yourHeadingDeg: 10, otherHeadingDeg: 260, bearingToOtherDeg: 60 });
    // Swap roles: new "you" heading = old other heading, bearing to new "other" is reversed.
    const b = TC.classifyEncounter({
      yourHeadingDeg: 260,
      otherHeadingDeg: 10,
      bearingToOtherDeg: TC.normalizeDeg(60 + 180),
    });
    return { aGiveWay: a.giveWay, bGiveWay: b.giveWay, aType: a.type, bType: b.type };
  });
  expect(check.aType).toBe(check.bType);
  const swapped = { you: 'other', other: 'you', both: 'both' };
  expect(swapped[check.aGiveWay]).toBe(check.bGiveWay);
});

test('you approaching another vessel from nearly dead astern, same heading, are overtaking her', async ({ page }) => {
  // Other vessel is heading the same way you are, and she sees you at a
  // relative bearing of 170 degrees from her own bow — almost dead astern —
  // so you are the overtaking vessel and must keep clear.
  const result = await page.evaluate(() =>
    TC.classifyEncounter({ yourHeadingDeg: 0, otherHeadingDeg: 0, bearingToOtherDeg: 10 })
  );
  expect(result.type).toBe('overtaking');
  expect(result.giveWay).toBe('you');
});

/* ================================================================
   Buoyage — IALA System B
================================================================ */

test('IALA System B: red-right-returning holds for all color/direction combinations', async ({ page }) => {
  const result = await page.evaluate(() => ({
    redInbound: TC.buoyage.sideForBuoy('red', 'inbound'),
    redOutbound: TC.buoyage.sideForBuoy('red', 'outbound'),
    greenInbound: TC.buoyage.sideForBuoy('green', 'inbound'),
    greenOutbound: TC.buoyage.sideForBuoy('green', 'outbound'),
  }));
  expect(result).toEqual({
    redInbound: 'starboard',
    redOutbound: 'port',
    greenInbound: 'port',
    greenOutbound: 'starboard',
  });
});

test('buoy shape follows color: red is a nun, green is a can', async ({ page }) => {
  const result = await page.evaluate(() => ({
    red: TC.buoyage.shapeForColor('red'),
    green: TC.buoyage.shapeForColor('green'),
  }));
  expect(result).toEqual({ red: 'nun', green: 'can' });
});

test('buoy numbering parity: even numbers are red, odd numbers are green', async ({ page }) => {
  const result = await page.evaluate(() => [2, 3, 14, 17].map((n) => TC.buoyage.colorForNumber(n)));
  expect(result).toEqual(['red', 'green', 'red', 'green']);
});

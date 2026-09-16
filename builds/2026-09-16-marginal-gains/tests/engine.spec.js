// Node-level tests against the exact engine.js the browser loads.
const { test, expect } = require('@playwright/test');
const path = require('path');

const Engine = require(path.join(__dirname, '..', 'src', 'engine.js'));

function bruteForceOptimal(projects, budget) {
  // Enumerate every valid allocation (each project gets 0..min(remaining,maxHours))
  // and return the true maximum total value. Only used on small instances —
  // this is the independent ground truth solveOptimal is checked against.
  let best = 0;

  function recurse(index, remaining, total) {
    if (index === projects.length) {
      if (total > best) best = total;
      return;
    }
    const proj = projects[index];
    const maxX = Math.min(remaining, proj.maxHours);
    for (let x = 0; x <= maxX; x++) {
      recurse(index + 1, remaining - x, total + proj.values[x]);
    }
  }

  recurse(0, budget, 0);
  return best;
}

function randomProject(rng, id) {
  const threshold = Math.floor(rng() * 3);
  const weight = 4 + Math.floor(rng() * 8);
  const maxHours = 2 + Math.floor(rng() * 5); // keep small for brute force feasibility
  return {
    id: id,
    name: id,
    category: 'Research',
    threshold: threshold,
    weight: weight,
    maxHours: maxHours,
    values: Engine.generateValueTable(threshold, weight, maxHours)
  };
}

test.describe('generateValueTable', () => {
  test('is zero below threshold and non-decreasing throughout', () => {
    for (let trial = 0; trial < 50; trial++) {
      const threshold = trial % 4;
      const weight = 5 + (trial % 10);
      const maxHours = 5 + (trial % 12);
      const values = Engine.generateValueTable(threshold, weight, maxHours);
      expect(values.length).toBe(maxHours + 1);
      for (let h = 0; h < threshold && h <= maxHours; h++) {
        expect(values[h]).toBe(0);
      }
      for (let h = 1; h <= maxHours; h++) {
        expect(values[h]).toBeGreaterThanOrEqual(values[h - 1]);
      }
    }
  });

  test('value stays 0 through the threshold hour itself, then climbs', () => {
    const values = Engine.generateValueTable(2, 10, 10);
    expect(values[0]).toBe(0);
    expect(values[1]).toBe(0);
    expect(values[2]).toBe(0); // h - threshold = 0 -> sqrt(0) = 0
    expect(values[3]).toBeGreaterThan(0);
  });
});

test.describe('daily RNG determinism', () => {
  test('same UTC date string always draws the same project set and parameters', () => {
    const a = Engine.drawDailyProjects('2026-09-16');
    const b = Engine.drawDailyProjects('2026-09-16');
    expect(a.budget).toBe(b.budget);
    expect(a.projects.map((p) => p.id)).toEqual(b.projects.map((p) => p.id));
    expect(a.projects.map((p) => p.threshold)).toEqual(b.projects.map((p) => p.threshold));
    expect(a.projects.map((p) => p.weight)).toEqual(b.projects.map((p) => p.weight));
  });

  test('different UTC dates draw different project sets or parameters', () => {
    const a = Engine.drawDailyProjects('2026-09-16');
    const b = Engine.drawDailyProjects('2026-09-17');
    const sameIds = JSON.stringify(a.projects.map((p) => p.id)) === JSON.stringify(b.projects.map((p) => p.id));
    const sameParams = JSON.stringify(a.projects.map((p) => [p.threshold, p.weight, p.maxHours])) ===
      JSON.stringify(b.projects.map((p) => [p.threshold, p.weight, p.maxHours]));
    expect(sameIds && sameParams).toBe(false);
  });

  test('drawDailyProjects always returns 6 distinct projects from the pool', () => {
    const draw = Engine.drawDailyProjects('2026-01-01');
    expect(draw.projects.length).toBe(6);
    const ids = new Set(draw.projects.map((p) => p.id));
    expect(ids.size).toBe(6);
  });
});

test.describe('solveOptimal correctness', () => {
  test('matches brute-force enumeration on many small randomized instances', () => {
    const rng = Engine.mulberry32(12345);
    for (let trial = 0; trial < 40; trial++) {
      const count = 2 + (trial % 2); // 2 or 3 projects
      const projects = [];
      for (let i = 0; i < count; i++) projects.push(randomProject(rng, 'p' + trial + '-' + i));
      const budget = 3 + Math.floor(rng() * 8); // budget <= 10

      const dpResult = Engine.solveOptimal(projects, budget);
      const bruteBest = bruteForceOptimal(projects, budget);

      expect(dpResult.total).toBe(bruteBest);

      // The DP's own reconstructed allocation must actually achieve the value it reports.
      let reconstructedTotal = 0;
      let hoursUsed = 0;
      projects.forEach((p) => {
        const h = dpResult.allocation[p.id] || 0;
        expect(h).toBeGreaterThanOrEqual(0);
        expect(h).toBeLessThanOrEqual(p.maxHours);
        reconstructedTotal += p.values[h];
        hoursUsed += h;
      });
      expect(reconstructedTotal).toBe(dpResult.total);
      expect(hoursUsed).toBeLessThanOrEqual(budget);
    }
  });

  test('no allocation found by random search ever beats the reported optimum', () => {
    const rng = Engine.mulberry32(999);
    for (let trial = 0; trial < 20; trial++) {
      const projects = [randomProject(rng, 'a'), randomProject(rng, 'b'), randomProject(rng, 'c')];
      const budget = 4 + Math.floor(rng() * 6);
      const optimal = Engine.solveOptimal(projects, budget);

      for (let sample = 0; sample < 200; sample++) {
        let remaining = budget;
        let total = 0;
        projects.forEach((p) => {
          const x = Math.min(remaining, Math.floor(rng() * (p.maxHours + 1)));
          total += p.values[x];
          remaining -= x;
        });
        expect(total).toBeLessThanOrEqual(optimal.total);
      }
    }
  });

  test('zero budget yields zero total value and zero hours allocated everywhere', () => {
    const projects = [randomProject(Engine.mulberry32(1), 'a'), randomProject(Engine.mulberry32(2), 'b')];
    const result = Engine.solveOptimal(projects, 0);
    expect(result.total).toBe(0);
    Object.values(result.allocation).forEach((h) => expect(h).toBe(0));
  });

  test('a single project just allocates its full budget or its cap, whichever is smaller', () => {
    const project = randomProject(Engine.mulberry32(7), 'solo');
    const budget = project.maxHours + 5;
    const result = Engine.solveOptimal([project], budget);
    expect(result.allocation.solo).toBe(project.maxHours);
    expect(result.total).toBe(project.values[project.maxHours]);
  });

  test('a budget larger than every maxHours combined never over-allocates any project', () => {
    const rng = Engine.mulberry32(42);
    const projects = [randomProject(rng, 'a'), randomProject(rng, 'b'), randomProject(rng, 'c')];
    const hugeBudget = projects.reduce((s, p) => s + p.maxHours, 0) + 20;
    const result = Engine.solveOptimal(projects, hugeBudget);
    projects.forEach((p) => {
      expect(result.allocation[p.id]).toBe(p.maxHours);
    });
  });
});

test.describe('scoreRound and grading', () => {
  test('allocating exactly the optimal split scores 100%', () => {
    const rng = Engine.mulberry32(555);
    const projects = [randomProject(rng, 'a'), randomProject(rng, 'b'), randomProject(rng, 'c')];
    const budget = 6;
    const optimal = Engine.solveOptimal(projects, budget);
    const score = Engine.scoreRound(projects, optimal.allocation, budget);
    expect(score.percent).toBe(100);
    expect(score.grade).toBe('S');
  });

  test('allocating nothing scores 0% unless the optimal itself is 0', () => {
    const rng = Engine.mulberry32(777);
    const projects = [randomProject(rng, 'a'), randomProject(rng, 'b')];
    const budget = 8;
    const zeroAllocation = {};
    projects.forEach((p) => (zeroAllocation[p.id] = 0));
    const score = Engine.scoreRound(projects, zeroAllocation, budget);
    const optimal = Engine.solveOptimal(projects, budget);
    if (optimal.total === 0) {
      expect(score.percent).toBe(100);
    } else {
      expect(score.percent).toBe(0);
      expect(score.grade).toBe('F');
    }
  });

  test('gradeForPercent maps boundary values to the documented letter grades', () => {
    expect(Engine.gradeForPercent(100)).toBe('S');
    expect(Engine.gradeForPercent(98)).toBe('S');
    expect(Engine.gradeForPercent(97)).toBe('A');
    expect(Engine.gradeForPercent(90)).toBe('A');
    expect(Engine.gradeForPercent(89)).toBe('B');
    expect(Engine.gradeForPercent(80)).toBe('B');
    expect(Engine.gradeForPercent(79)).toBe('C');
    expect(Engine.gradeForPercent(65)).toBe('C');
    expect(Engine.gradeForPercent(64)).toBe('D');
    expect(Engine.gradeForPercent(45)).toBe('D');
    expect(Engine.gradeForPercent(44)).toBe('F');
    expect(Engine.gradeForPercent(0)).toBe('F');
  });
});

test.describe('todayUTCString', () => {
  test('formats a known date as YYYY-MM-DD in UTC', () => {
    const d = new Date(Date.UTC(2026, 8, 16, 23, 59)); // Sept 16 2026, 23:59 UTC
    expect(Engine.todayUTCString(d)).toBe('2026-09-16');
  });

  test('pads single-digit months and days', () => {
    const d = new Date(Date.UTC(2026, 0, 5, 0, 0));
    expect(Engine.todayUTCString(d)).toBe('2026-01-05');
  });
});

test.describe('drawPracticeProjects', () => {
  test('respects the requested difficulty tier project count and budget', () => {
    const light = Engine.drawPracticeProjects(4);
    expect(light.projects.length).toBe(4);
    expect(light.budget).toBe(24);

    const heavy = Engine.drawPracticeProjects(8);
    expect(heavy.projects.length).toBe(8);
    expect(heavy.budget).toBe(56);
  });

  test('every drawn project has a monotonic value table matching its own parameters', () => {
    const draw = Engine.drawPracticeProjects(6);
    draw.projects.forEach((p) => {
      const expected = Engine.generateValueTable(p.threshold, p.weight, p.maxHours);
      expect(p.values).toEqual(expected);
    });
  });
});

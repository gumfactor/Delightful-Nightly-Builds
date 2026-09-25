// Node-level tests against the exact engine.js / graph.js the browser loads.
const { test, expect } = require('@playwright/test');
const path = require('path');

const Engine = require(path.join(__dirname, '..', 'src', 'engine.js'));
const Graph = require(path.join(__dirname, '..', 'src', 'graph.js'));
const AIDebrief = require(path.join(__dirname, '..', 'src', 'ai.js'));
const Levels = require(path.join(__dirname, '..', 'src', 'levels.js'));

function bruteForceOptimal(tasks, numLanes) {
  let best = Infinity;
  function recurse(state) {
    if (Engine.isComplete(state, tasks)) {
      const ms = Engine.currentMakespan(state);
      if (ms < best) best = ms;
      return;
    }
    const ready = Engine.computeReadySet(tasks, state.placed);
    ready.forEach((task) => {
      for (let lane = 0; lane < numLanes; lane++) {
        recurse(Engine.applyPlacement(state, task, lane));
      }
    });
  }
  recurse(Engine.initState(numLanes));
  return best;
}

test.describe('scheduling simulation', () => {
  test('simple chain: each task waits for its single dependency to finish', () => {
    const tasks = [
      { id: 'A', name: 'A', duration: 3, deps: [] },
      { id: 'B', name: 'B', duration: 4, deps: ['A'] },
      { id: 'C', name: 'C', duration: 5, deps: ['B'] },
    ];
    let state = Engine.initState(2);
    state = Engine.applyPlacement(state, tasks[0], 0);
    expect(state.placed.A).toEqual({ lane: 0, start: 0, finish: 3 });
    state = Engine.applyPlacement(state, tasks[1], 0);
    expect(state.placed.B).toEqual({ lane: 0, start: 3, finish: 7 });
    state = Engine.applyPlacement(state, tasks[2], 1);
    // C depends on B (finishes at 7); lane 1 is free at 0, so C must wait for B, not the lane.
    expect(state.placed.C).toEqual({ lane: 1, start: 7, finish: 12 });
    expect(Engine.currentMakespan(state)).toBe(12);
  });

  test('same-lane tasks wait for the lane, not just their dependencies', () => {
    const tasks = [
      { id: 'A', name: 'A', duration: 2, deps: [] },
      { id: 'B', name: 'B', duration: 2, deps: [] },
    ];
    let state = Engine.initState(1);
    state = Engine.applyPlacement(state, tasks[0], 0);
    state = Engine.applyPlacement(state, tasks[1], 0);
    // B has no dependency, but lane 0 isn't free until A finishes at 2.
    expect(state.placed.B.start).toBe(2);
    expect(state.placed.B.finish).toBe(4);
  });

  test('diamond DAG produces the hand-computed makespan', () => {
    // A(2) -> B(4), A -> C(5); D(3) depends on both B and C. 2 lanes.
    const tasks = [
      { id: 'A', name: 'A', duration: 2, deps: [] },
      { id: 'B', name: 'B', duration: 4, deps: ['A'] },
      { id: 'C', name: 'C', duration: 5, deps: ['A'] },
      { id: 'D', name: 'D', duration: 3, deps: ['B', 'C'] },
    ];
    let state = Engine.initState(2);
    state = Engine.applyPlacement(state, tasks[0], 0); // A: 0-2
    state = Engine.applyPlacement(state, tasks[1], 0); // B: 2-6
    state = Engine.applyPlacement(state, tasks[2], 1); // C: 2-7
    state = Engine.applyPlacement(state, tasks[3], 0); // D waits for C (7), not just lane 0 (free at 6)
    expect(state.placed.D).toEqual({ lane: 0, start: 7, finish: 10 });
    expect(Engine.currentMakespan(state)).toBe(10);
  });

  test('applyPlacement throws when a dependency is not yet placed', () => {
    const tasks = [
      { id: 'A', name: 'A', duration: 1, deps: [] },
      { id: 'B', name: 'B', duration: 1, deps: ['A'] },
    ];
    const state = Engine.initState(1);
    expect(() => Engine.applyPlacement(state, tasks[1], 0)).toThrow();
  });

  test('applyPlacement throws on a duplicate placement', () => {
    const tasks = [{ id: 'A', name: 'A', duration: 1, deps: [] }];
    let state = Engine.initState(1);
    state = Engine.applyPlacement(state, tasks[0], 0);
    expect(() => Engine.applyPlacement(state, tasks[0], 0)).toThrow();
  });

  test('computeReadySet reflects newly-unlocked tasks after a placement', () => {
    const tasks = [
      { id: 'A', name: 'A', duration: 1, deps: [] },
      { id: 'B', name: 'B', duration: 1, deps: ['A'] },
      { id: 'C', name: 'C', duration: 1, deps: [] },
    ];
    let state = Engine.initState(2);
    expect(Engine.computeReadySet(tasks, state.placed).map((t) => t.id).sort()).toEqual(['A', 'C']);
    state = Engine.applyPlacement(state, tasks[0], 0);
    expect(Engine.computeReadySet(tasks, state.placed).map((t) => t.id).sort()).toEqual(['B', 'C']);
  });
});

test.describe('solveOptimal — exact solver', () => {
  test('fully serial chain: optimal equals the sum of durations regardless of lane count', () => {
    const tasks = [
      { id: 'A', name: 'A', duration: 3, deps: [] },
      { id: 'B', name: 'B', duration: 4, deps: ['A'] },
      { id: 'C', name: 'C', duration: 5, deps: ['B'] },
    ];
    expect(Engine.solveOptimal(tasks, 1).optimal).toBe(12);
    expect(Engine.solveOptimal(tasks, 3).optimal).toBe(12);
  });

  test('fully parallel tasks: optimal equals the longest single duration when lanes >= task count', () => {
    const tasks = [
      { id: 'A', name: 'A', duration: 3, deps: [] },
      { id: 'B', name: 'B', duration: 4, deps: [] },
      { id: 'C', name: 'C', duration: 5, deps: [] },
    ];
    expect(Engine.solveOptimal(tasks, 3).optimal).toBe(5);
  });

  test('fully parallel tasks: optimal equals the sum when only 1 lane is available', () => {
    const tasks = [
      { id: 'A', name: 'A', duration: 3, deps: [] },
      { id: 'B', name: 'B', duration: 4, deps: [] },
      { id: 'C', name: 'C', duration: 5, deps: [] },
    ];
    expect(Engine.solveOptimal(tasks, 1).optimal).toBe(12);
  });

  test('single task: optimal equals its own duration', () => {
    const tasks = [{ id: 'A', name: 'A', duration: 7, deps: [] }];
    expect(Engine.solveOptimal(tasks, 3).optimal).toBe(7);
  });

  test('diamond DAG: optimal matches the hand-computed value', () => {
    const tasks = [
      { id: 'A', name: 'A', duration: 2, deps: [] },
      { id: 'B', name: 'B', duration: 4, deps: ['A'] },
      { id: 'C', name: 'C', duration: 5, deps: ['A'] },
      { id: 'D', name: 'D', duration: 3, deps: ['B', 'C'] },
    ];
    expect(Engine.solveOptimal(tasks, 2).optimal).toBe(10);
  });

  test('matches independent brute-force enumeration across randomized small DAGs', () => {
    const rng = Engine.mulberry32(2026092501);
    let mismatches = 0;
    for (let trial = 0; trial < 40; trial++) {
      const n = 3 + Math.floor(rng() * 3); // 3..5 — small enough for brute force
      const tasks = [];
      for (let i = 0; i < n; i++) {
        const deps = [];
        for (let j = 0; j < i; j++) {
          if (rng() < 0.4) deps.push('T' + j);
        }
        tasks.push({ id: 'T' + i, name: 'T' + i, duration: 1 + Math.floor(rng() * 6), deps });
      }
      const lanes = 1 + Math.floor(rng() * 3);
      const bf = bruteForceOptimal(tasks, lanes);
      const solved = Engine.solveOptimal(tasks, lanes).optimal;
      if (bf !== solved) mismatches++;
    }
    expect(mismatches).toBe(0);
  });

  test('every shipped level solves without hitting the node-visit safety cap', () => {
    const allLevels = [Levels.TUTORIAL_LEVEL, ...Levels.CAMPAIGN_LEVELS];
    allLevels.forEach((level) => {
      const r = Engine.solveOptimal(level.tasks, level.numLanes);
      expect(r.capped).toBe(false);
      expect(r.optimal).toBeGreaterThan(0);
    });
  });
});

test.describe('grading', () => {
  test('exact match is gold', () => {
    expect(Engine.gradeForMakespan(20, 20)).toBe('gold');
  });

  test('within the margin is silver, at the boundary inclusive', () => {
    // optimal 20 -> margin = round(20*0.15) = 3
    expect(Engine.gradeForMakespan(23, 20)).toBe('silver');
    expect(Engine.gradeForMakespan(24, 20)).toBe('bronze');
  });

  test('small optimal values use the minimum 2-minute margin, not a rounding-to-zero margin', () => {
    // optimal 5 -> 0.15*5=0.75 rounds to 1, but margin floors at 2
    expect(Engine.gradeForMakespan(7, 5)).toBe('silver');
    expect(Engine.gradeForMakespan(8, 5)).toBe('bronze');
  });
});

test.describe('daily challenge generator', () => {
  test('is deterministic for a given UTC date', () => {
    const a = Engine.generateDailyLevel('2026-09-25');
    const b = Engine.generateDailyLevel('2026-09-25');
    expect(a).toEqual(b);
  });

  test('differs across different dates', () => {
    const sampleDates = ['2026-09-25', '2026-09-26', '2026-10-01', '2026-12-31', '2027-01-01'];
    const shapes = sampleDates.map((d) => JSON.stringify(Engine.generateDailyLevel(d).tasks));
    const uniqueShapes = new Set(shapes);
    expect(uniqueShapes.size).toBe(sampleDates.length);
  });

  test('always produces an acyclic DAG (every dependency has a strictly earlier index)', () => {
    const dates = [];
    for (let m = 1; m <= 12; m++) {
      for (let d = 1; d <= 28; d += 7) {
        dates.push('2026-' + String(m).padStart(2, '0') + '-' + String(d).padStart(2, '0'));
      }
    }
    dates.forEach((dateStr) => {
      const level = Engine.generateDailyLevel(dateStr);
      const indexOf = {};
      level.tasks.forEach((t, i) => (indexOf[t.id] = i));
      level.tasks.forEach((t) => {
        t.deps.forEach((d) => {
          expect(indexOf[d]).toBeLessThan(indexOf[t.id]);
        });
      });
      // solveOptimal must not throw on a real generated instance (proves it's a valid schedulable DAG).
      expect(() => Engine.solveOptimal(level.tasks, level.numLanes)).not.toThrow();
    });
  });

  test('never generates a degenerate level (always has parallelism opportunity when n >= 4)', () => {
    const dates = [];
    for (let m = 1; m <= 12; m++) {
      for (let d = 1; d <= 28; d += 5) {
        dates.push('2026-' + String(m).padStart(2, '0') + '-' + String(d).padStart(2, '0'));
      }
    }
    dates.forEach((dateStr) => {
      const level = Engine.generateDailyLevel(dateStr);
      if (level.tasks.length < 4) return;
      const rootCount = level.tasks.filter((t) => t.deps.length === 0).length;
      const edgeCount = level.tasks.reduce((sum, t) => sum + t.deps.length, 0);
      expect(rootCount).toBeGreaterThanOrEqual(2);
      expect(edgeCount).toBeGreaterThanOrEqual(Math.ceil(level.tasks.length / 2));
    });
  });

  test('task count and lane count stay within the documented ranges', () => {
    for (let i = 0; i < 30; i++) {
      const level = Engine.generateDailyLevel('2026-0' + ((i % 9) + 1) + '-1' + (i % 9));
      expect(level.tasks.length).toBeGreaterThanOrEqual(5);
      expect(level.tasks.length).toBeLessThanOrEqual(7);
      expect(level.numLanes).toBeGreaterThanOrEqual(2);
      expect(level.numLanes).toBeLessThanOrEqual(3);
    }
  });
});

test.describe('AI debrief', () => {
  const level = { id: 'L1', title: 'Test Level', numLanes: 2, tasks: [{ id: 'A', name: 'Clone Repository', duration: 3, deps: [] }] };
  const solverResult = { optimal: 10 };
  const playerResult = { makespan: 10, grade: 'gold', placed: { A: { lane: 0, start: 0, finish: 10 } } };

  test('getAICoaching makes zero network calls and returns the fallback when no API key is set', async () => {
    let called = false;
    const fetchImpl = async () => {
      called = true;
      throw new Error('should not be called');
    };
    const note = await AIDebrief.getAICoaching('', level, playerResult, solverResult, fetchImpl);
    expect(called).toBe(false);
    expect(note).toContain('optimal');
  });

  test('getAICoaching calls the Anthropic endpoint with the expected shape when a key is set', async () => {
    let capturedUrl = null;
    let capturedInit = null;
    const fetchImpl = async (url, init) => {
      capturedUrl = url;
      capturedInit = init;
      return {
        ok: true,
        json: async () => ({ content: [{ text: 'Nice run.' }] }),
      };
    };
    const note = await AIDebrief.getAICoaching('sk-test-key', level, playerResult, solverResult, fetchImpl);
    expect(capturedUrl).toBe('https://api.anthropic.com/v1/messages');
    expect(capturedInit.headers['x-api-key']).toBe('sk-test-key');
    expect(note).toBe('Nice run.');
  });

  test('getAICoaching falls back gracefully on a failed or malformed response', async () => {
    const failFetch = async () => ({ ok: false });
    const note1 = await AIDebrief.getAICoaching('sk-test', level, playerResult, solverResult, failFetch);
    expect(note1).toContain('optimal');

    const malformedFetch = async () => ({ ok: true, json: async () => ({}) });
    const note2 = await AIDebrief.getAICoaching('sk-test', level, playerResult, solverResult, malformedFetch);
    expect(note2).toContain('optimal');
  });

  test('the prompt sent to the model contains only computed numbers/names, never personal data', () => {
    const prompt = AIDebrief.buildPrompt(level, playerResult, solverResult);
    expect(prompt).toContain('Clone Repository');
    expect(prompt).toContain('10');
    expect(prompt).not.toMatch(/@/); // no email-shaped strings
  });

  test('buildFallbackNote is deterministic for identical inputs', () => {
    const a = AIDebrief.buildFallbackNote(level, playerResult, solverResult);
    const b = AIDebrief.buildFallbackNote(level, playerResult, solverResult);
    expect(a).toBe(b);
  });
});

test.describe('dependency graph layout', () => {
  test('assigns each task a layer one greater than the deepest dependency', () => {
    const tasks = [
      { id: 'A', name: 'A', duration: 1, deps: [] },
      { id: 'B', name: 'B', duration: 1, deps: ['A'] },
      { id: 'C', name: 'C', duration: 1, deps: ['A'] },
      { id: 'D', name: 'D', duration: 1, deps: ['B', 'C'] },
    ];
    const layout = Graph.computeLayout(tasks);
    expect(layout.layer.A).toBe(0);
    expect(layout.layer.B).toBe(1);
    expect(layout.layer.C).toBe(1);
    expect(layout.layer.D).toBe(2);
    expect(layout.numLayers).toBe(3);
    expect(layout.maxInLayer).toBe(2);
  });

  test('canvasDimensions grows with layer count and widest layer', () => {
    const small = Graph.computeLayout([{ id: 'A', name: 'A', duration: 1, deps: [] }]);
    const wide = Graph.computeLayout([
      { id: 'A', name: 'A', duration: 1, deps: [] },
      { id: 'B', name: 'B', duration: 1, deps: [] },
      { id: 'C', name: 'C', duration: 1, deps: [] },
    ]);
    const dSmall = Graph.canvasDimensions(small);
    const dWide = Graph.canvasDimensions(wide);
    expect(dWide.height).toBeGreaterThan(dSmall.height);
  });
});

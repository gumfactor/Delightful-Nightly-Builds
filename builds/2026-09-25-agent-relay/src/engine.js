// Agent Relay — core engine: scheduling simulation, exact solver, grading, RNG, daily generator.
// Pure logic, no DOM. Dual-exported (CommonJS for Node-level tests, window global for the browser).

var TASK_NAME_POOL = [
  "Clone Repository",
  "Install Dependencies",
  "Read Existing Code",
  "Draft Implementation Plan",
  "Write Feature Code",
  "Write Unit Tests",
  "Run Test Suite",
  "Fix Failing Tests",
  "Fix Lint Errors",
  "Update Documentation",
  "Self Code Review",
  "Security Review",
  "Update Changelog",
  "Open Pull Request",
  "Address Review Comments",
  "Merge & Deploy",
  "Verify Deployment",
  "Sync Task Backlog"
];

// ---------------------------------------------------------------------------
// RNG — mulberry32, seeded from a string hash (FNV-1a). Deterministic given
// the same seed string; used for the UTC-date-seeded Daily Challenge.
// ---------------------------------------------------------------------------

function hashStringToSeed(str) {
  var h = 2166136261;
  for (var i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function mulberry32(seed) {
  var a = seed >>> 0;
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    var t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function pad2(n) {
  return n < 10 ? "0" + n : "" + n;
}

function todayUTCString() {
  var d = new Date();
  return d.getUTCFullYear() + "-" + pad2(d.getUTCMonth() + 1) + "-" + pad2(d.getUTCDate());
}

function shuffleWithRng(arr, rng) {
  var a = arr.slice();
  for (var i = a.length - 1; i > 0; i--) {
    var j = Math.floor(rng() * (i + 1));
    var tmp = a[i];
    a[i] = a[j];
    a[j] = tmp;
  }
  return a;
}

// ---------------------------------------------------------------------------
// Scheduling simulation — placements are built one at a time, always taking a
// task from the "ready" set (all deps already placed) and appending it to the
// end of a chosen lane's queue. This construction guarantees every reachable
// state is valid by construction: a task can never be placed before a
// dependency, so no explicit cycle/order-violation check is ever needed.
// ---------------------------------------------------------------------------

function initState(numLanes) {
  var laneFreeAt = [];
  for (var i = 0; i < numLanes; i++) laneFreeAt.push(0);
  return { placed: {}, laneFreeAt: laneFreeAt };
}

function computeReadySet(tasks, placed) {
  return tasks.filter(function (t) {
    if (placed.hasOwnProperty(t.id)) return false;
    for (var i = 0; i < t.deps.length; i++) {
      if (!placed.hasOwnProperty(t.deps[i])) return false;
    }
    return true;
  });
}

function applyPlacement(state, task, laneIndex) {
  if (state.placed.hasOwnProperty(task.id)) {
    throw new Error('Task "' + task.id + '" is already placed');
  }
  for (var i = 0; i < task.deps.length; i++) {
    if (!state.placed.hasOwnProperty(task.deps[i])) {
      throw new Error('Task "' + task.id + '" is not ready — dependency "' + task.deps[i] + '" is not placed');
    }
  }
  if (laneIndex < 0 || laneIndex >= state.laneFreeAt.length) {
    throw new Error("Invalid lane index " + laneIndex);
  }
  var depFinishMax = 0;
  for (var j = 0; j < task.deps.length; j++) {
    var f = state.placed[task.deps[j]].finish;
    if (f > depFinishMax) depFinishMax = f;
  }
  var start = Math.max(state.laneFreeAt[laneIndex], depFinishMax);
  var finish = start + task.duration;

  var newPlaced = {};
  for (var key in state.placed) {
    if (state.placed.hasOwnProperty(key)) newPlaced[key] = state.placed[key];
  }
  newPlaced[task.id] = { lane: laneIndex, start: start, finish: finish };

  var newLaneFreeAt = state.laneFreeAt.slice();
  newLaneFreeAt[laneIndex] = finish;

  return { placed: newPlaced, laneFreeAt: newLaneFreeAt };
}

function currentMakespan(state) {
  var m = 0;
  for (var i = 0; i < state.laneFreeAt.length; i++) {
    if (state.laneFreeAt[i] > m) m = state.laneFreeAt[i];
  }
  return m;
}

function isComplete(state, tasks) {
  return Object.keys(state.placed).length === tasks.length;
}

// Lower bound on the final makespan from a partial state: the earliest any
// task could possibly finish if lane contention were removed (infinite
// lanes), using the already-fixed finish times of placed tasks. Relaxing a
// resource constraint can only reduce the optimum, so this is admissible —
// safe to use for branch-and-bound pruning.
function earliestFinishBound(tasks, state) {
  var taskById = {};
  tasks.forEach(function (t) {
    taskById[t.id] = t;
  });
  var memo = {};
  function ef(id) {
    if (memo.hasOwnProperty(id)) return memo[id];
    if (state.placed.hasOwnProperty(id)) {
      memo[id] = state.placed[id].finish;
      return memo[id];
    }
    var t = taskById[id];
    var depMax = 0;
    t.deps.forEach(function (d) {
      var v = ef(d);
      if (v > depMax) depMax = v;
    });
    var result = depMax + t.duration;
    memo[id] = result;
    return result;
  }
  var maxEF = 0;
  tasks.forEach(function (t) {
    var v = ef(t.id);
    if (v > maxEF) maxEF = v;
  });
  return maxEF;
}

// Remaining critical path length (this task's duration plus the longest
// chain of dependents downstream of it) — used only to order the greedy
// initial upper bound, not for correctness.
function computeRemainingCriticalPath(tasks) {
  var childrenMap = {};
  tasks.forEach(function (t) {
    childrenMap[t.id] = [];
  });
  tasks.forEach(function (t) {
    t.deps.forEach(function (d) {
      childrenMap[d].push(t.id);
    });
  });
  var taskById = {};
  tasks.forEach(function (t) {
    taskById[t.id] = t;
  });
  var memo = {};
  function cp(id) {
    if (memo.hasOwnProperty(id)) return memo[id];
    var childMax = 0;
    childrenMap[id].forEach(function (cid) {
      var v = cp(cid);
      if (v > childMax) childMax = v;
    });
    var result = taskById[id].duration + childMax;
    memo[id] = result;
    return result;
  }
  var result = {};
  tasks.forEach(function (t) {
    result[t.id] = cp(t.id);
  });
  return result;
}

// Greedy heuristic schedule: at each step, place the ready task with the
// longest remaining critical path onto the earliest-free lane. Used only to
// seed the branch-and-bound search with a good initial upper bound.
function greedySchedule(tasks, numLanes) {
  var rcp = computeRemainingCriticalPath(tasks);
  var state = initState(numLanes);
  var order = [];
  while (!isComplete(state, tasks)) {
    var ready = computeReadySet(tasks, state.placed);
    ready.sort(function (a, b) {
      return rcp[b.id] - rcp[a.id];
    });
    var task = ready[0];
    var bestLane = 0;
    for (var l = 1; l < state.laneFreeAt.length; l++) {
      if (state.laneFreeAt[l] < state.laneFreeAt[bestLane]) bestLane = l;
    }
    state = applyPlacement(state, task, bestLane);
    order.push({ taskId: task.id, lane: bestLane });
  }
  return { makespan: currentMakespan(state), order: order };
}

// Exact solver: branch-and-bound over the ready-queue construction. Explores
// every valid (task, lane) placement sequence, pruned by an admissible lower
// bound and by skipping symmetric lane choices (lanes currently sharing the
// same free time are interchangeable). A node-visit cap is a defensive-only
// safety net for pathological inputs; every shipped level is well within it.
function solveOptimal(tasks, numLanes, options) {
  options = options || {};
  var nodeCap = options.nodeCap || 2000000;
  var nodesVisited = 0;
  var capped = false;

  var greedy = greedySchedule(tasks, numLanes);
  var best = greedy.makespan;
  var bestAssignment = greedy.order;

  function recurse(state, order) {
    nodesVisited++;
    if (nodesVisited > nodeCap) {
      capped = true;
      return;
    }
    if (isComplete(state, tasks)) {
      var ms = currentMakespan(state);
      if (ms < best) {
        best = ms;
        bestAssignment = order.slice();
      }
      return;
    }
    if (earliestFinishBound(tasks, state) >= best) return;

    var ready = computeReadySet(tasks, state.placed);
    for (var ti = 0; ti < ready.length; ti++) {
      var task = ready[ti];
      var seenFreeAt = {};
      for (var lane = 0; lane < numLanes; lane++) {
        var freeAt = state.laneFreeAt[lane];
        if (seenFreeAt.hasOwnProperty(freeAt)) continue;
        seenFreeAt[freeAt] = true;
        var newState = applyPlacement(state, task, lane);
        order.push({ taskId: task.id, lane: lane });
        recurse(newState, order);
        order.pop();
        if (capped) return;
      }
    }
  }

  recurse(initState(numLanes), []);

  return { optimal: best, assignment: bestAssignment, nodesVisited: nodesVisited, capped: capped };
}

// ---------------------------------------------------------------------------
// Grading
// ---------------------------------------------------------------------------

function gradeForMakespan(playerMakespan, optimal) {
  if (playerMakespan === optimal) return "gold";
  var margin = Math.max(2, Math.round(optimal * 0.15));
  if (playerMakespan <= optimal + margin) return "silver";
  return "bronze";
}

// ---------------------------------------------------------------------------
// Daily Challenge generator — deterministic per UTC date string ("YYYY-MM-DD").
// ---------------------------------------------------------------------------

function generateDailyLevel(dateStr) {
  var rng = mulberry32(hashStringToSeed("agent-relay-daily-" + dateStr));
  var attempt;
  var lastTasks = null;
  var lastNumLanes = 2;

  for (attempt = 0; attempt < 25; attempt++) {
    var n = 5 + Math.floor(rng() * 3); // 5..7
    var numLanes = 2 + Math.floor(rng() * 2); // 2..3
    var names = shuffleWithRng(TASK_NAME_POOL, rng).slice(0, n);

    var tasks = [];
    for (var i = 0; i < n; i++) {
      var id = "T" + i;
      var duration = 3 + Math.floor(rng() * 8); // 3..10
      var deps = [];
      if (i > 0) {
        var maxDeps = Math.min(2, i);
        var depCount = Math.floor(rng() * (maxDeps + 1));
        var candidates = shuffleWithRng(
          Array.from({ length: i }, function (_, idx) {
            return "T" + idx;
          }),
          rng
        );
        deps = candidates.slice(0, depCount);
      }
      tasks.push({ id: id, name: names[i], duration: duration, deps: deps });
    }

    var rootCount = tasks.filter(function (t) {
      return t.deps.length === 0;
    }).length;
    var edgeCount = tasks.reduce(function (sum, t) {
      return sum + t.deps.length;
    }, 0);
    var minEdges = Math.ceil(n / 2);
    var valid = n < 4 || (rootCount >= 2 && edgeCount >= minEdges);

    lastTasks = tasks;
    lastNumLanes = numLanes;

    if (valid) {
      return {
        id: "daily-" + dateStr,
        title: "Daily Challenge — " + dateStr,
        flavor: "Today's relay: get every task done as fast as your lanes allow.",
        numLanes: numLanes,
        tasks: tasks
      };
    }
  }

  // Defensive fallback: after 25 deterministic attempts, ship the last
  // generated (still-valid-DAG, just not meeting the density heuristic) shape
  // rather than looping forever. Never reached in practice for n in [5,7].
  return {
    id: "daily-" + dateStr,
    title: "Daily Challenge — " + dateStr,
    flavor: "Today's relay: get every task done as fast as your lanes allow.",
    numLanes: lastNumLanes,
    tasks: lastTasks
  };
}

var Engine = {
  TASK_NAME_POOL: TASK_NAME_POOL,
  hashStringToSeed: hashStringToSeed,
  mulberry32: mulberry32,
  todayUTCString: todayUTCString,
  shuffleWithRng: shuffleWithRng,
  initState: initState,
  computeReadySet: computeReadySet,
  applyPlacement: applyPlacement,
  currentMakespan: currentMakespan,
  isComplete: isComplete,
  earliestFinishBound: earliestFinishBound,
  computeRemainingCriticalPath: computeRemainingCriticalPath,
  greedySchedule: greedySchedule,
  solveOptimal: solveOptimal,
  gradeForMakespan: gradeForMakespan,
  generateDailyLevel: generateDailyLevel
};

if (typeof module !== "undefined" && module.exports) {
  module.exports = Engine;
} else {
  window.Engine = Engine;
}

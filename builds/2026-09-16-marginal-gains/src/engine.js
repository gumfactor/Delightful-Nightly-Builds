// Marginal Gains — core game engine.
// Classic script (no ES modules) so it opens directly via file://.
// The `module.exports` guard at the bottom lets tests `require()` this exact
// file under Node — the same code the browser runs, not a reimplementation.

var CATEGORIES = ["Research", "Teaching", "Admin", "Writing", "Ventures"];

var PROJECT_POOL = [
  { id: "grant-report", name: "Grant Progress Report", category: "Admin", blurb: "Annual progress report due to the funding agency." },
  { id: "manuscript-rr", name: "Manuscript Revise & Resubmit", category: "Writing", blurb: "Reviewer comments are in — time to address them." },
  { id: "irb-renewal", name: "IRB / Ethics Renewal", category: "Admin", blurb: "The protocol's annual ethics approval is expiring." },
  { id: "course-stress", name: "Course Prep — Stress & Coping", category: "Teaching", blurb: "Next week's lecture and readings need updating." },
  { id: "course-ai", name: "Course Prep — AI Applications for Psychologists", category: "Teaching", blurb: "New course; the syllabus is still taking shape." },
  { id: "ra-supervision", name: "RA / Grad Student Supervision", category: "Research", blurb: "Weekly check-ins and feedback on data collection." },
  { id: "canada-list-qa", name: "Canada List Data QA Sprint", category: "Ventures", blurb: "A batch of newly ingested listings needs review." },
  { id: "canada-list-editorial", name: "Canada List Editorial Piece", category: "Ventures", blurb: "A consumer-facing article on Canadian ownership." },
  { id: "kwyeter-spec", name: "Kwyeter Product Spec", category: "Ventures", blurb: "The noise-measurement calibration spec needs detail." },
  { id: "conference-abstract", name: "Conference Abstract Submission", category: "Writing", blurb: "Deadline is close; the abstract is still a draft." },
  { id: "neuroimaging-analysis", name: "Neuroimaging Data Analysis Pass", category: "Research", blurb: "A fresh scanner batch is waiting to be processed." },
  { id: "guest-lecture", name: "Guest Lecture Prep", category: "Teaching", blurb: "Slides for an invited talk to another department." },
  { id: "student-evals", name: "Student Evaluation Write-ups", category: "Admin", blurb: "End-of-term written feedback for every student." },
  { id: "lab-meeting", name: "Lab Meeting & Mentoring Prep", category: "Research", blurb: "This week's lab meeting agenda and discussion prep." },
  { id: "book-chapter", name: "Book Chapter Draft", category: "Writing", blurb: "The Stress and Coping book's next chapter outline." },
  { id: "investment-review", name: "Investment Research Review", category: "Admin", blurb: "A quarterly pass over the personal research watchlist." }
];

var DIFFICULTIES = {
  4: { count: 4, budget: 24 },
  6: { count: 6, budget: 40 },
  8: { count: 8, budget: 56 }
};

function hashStringToSeed(str) {
  var h = 1779033703 ^ str.length;
  for (var i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  h = Math.imul(h ^ (h >>> 16), 2246822507);
  h = Math.imul(h ^ (h >>> 13), 3266489909);
  return (h ^ (h >>> 16)) >>> 0;
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

function dailySeedFor(dateStr) {
  return hashStringToSeed("marginalgains-daily-" + dateStr);
}

function shuffle(arr, rng) {
  var out = arr.slice();
  for (var i = out.length - 1; i > 0; i--) {
    var j = Math.floor(rng() * (i + 1));
    var tmp = out[i];
    out[i] = out[j];
    out[j] = tmp;
  }
  return out;
}

// value(h) = 0 below threshold, then a rounded sqrt-shaped diminishing-returns
// climb up to maxHours; allocating past maxHours never adds more value (the
// project is simply "done"), so callers must never index past maxHours.
function generateValueTable(threshold, weight, maxHours) {
  var values = [];
  for (var h = 0; h <= maxHours; h++) {
    if (h < threshold) {
      values.push(0);
    } else {
      values.push(Math.round(weight * Math.sqrt(h - threshold)));
    }
  }
  return values;
}

function drawProjects(rng, count) {
  var pool = shuffle(PROJECT_POOL, rng);
  var picked = pool.slice(0, count);
  return picked.map(function (base) {
    var threshold = Math.floor(rng() * 4); // 0-3
    var weight = 6 + Math.floor(rng() * 9); // 6-14
    var maxHours = 6 + Math.floor(rng() * 11); // 6-16
    return {
      id: base.id,
      name: base.name,
      category: base.category,
      blurb: base.blurb,
      threshold: threshold,
      weight: weight,
      maxHours: maxHours,
      values: generateValueTable(threshold, weight, maxHours)
    };
  });
}

function drawDailyProjects(dateStr) {
  var rng = mulberry32(dailySeedFor(dateStr));
  var tier = DIFFICULTIES[6];
  return { budget: tier.budget, projects: drawProjects(rng, tier.count) };
}

function drawPracticeProjects(tierKey) {
  var tier = DIFFICULTIES[tierKey] || DIFFICULTIES[6];
  var rng = mulberry32((Math.random() * 4294967296) >>> 0);
  return { budget: tier.budget, projects: drawProjects(rng, tier.count) };
}

function projectValueAt(project, hours) {
  var h = Math.max(0, Math.min(hours, project.maxHours));
  return project.values[h];
}

// Dynamic-programming knapsack over the drawn projects: for each project j
// and hours-used h, dp[j][h] is the best total value achievable using the
// first j projects and at most h hours. This is a real, generically-correct
// solver — not a shortcut — verified against brute-force enumeration in
// tests/engine.spec.js.
function solveOptimal(projects, budget) {
  var n = projects.length;
  var dp = [];
  var choice = [];
  for (var j = 0; j <= n; j++) {
    dp.push(new Array(budget + 1).fill(0));
    choice.push(new Array(budget + 1).fill(0));
  }

  for (var jj = 1; jj <= n; jj++) {
    var proj = projects[jj - 1];
    for (var h = 0; h <= budget; h++) {
      var best = -1;
      var bestX = 0;
      var maxX = Math.min(h, proj.maxHours);
      for (var x = 0; x <= maxX; x++) {
        var val = dp[jj - 1][h - x] + proj.values[x];
        if (val > best) {
          best = val;
          bestX = x;
        }
      }
      dp[jj][h] = best;
      choice[jj][h] = bestX;
    }
  }

  var allocation = {};
  var remaining = budget;
  for (var back = n; back >= 1; back--) {
    var x2 = choice[back][remaining];
    allocation[projects[back - 1].id] = x2;
    remaining -= x2;
  }

  return { total: dp[n][budget], allocation: allocation };
}

function scoreRound(projects, allocation, budget) {
  var playerTotal = 0;
  var used = 0;
  projects.forEach(function (p) {
    var h = allocation[p.id] || 0;
    used += h;
    playerTotal += projectValueAt(p, h);
  });
  var optimal = solveOptimal(projects, budget);
  var pct = optimal.total === 0 ? 100 : Math.round((playerTotal / optimal.total) * 100);
  pct = Math.min(100, Math.max(0, pct));
  return {
    playerTotal: playerTotal,
    optimalTotal: optimal.total,
    optimalAllocation: optimal.allocation,
    hoursUsed: used,
    percent: pct,
    grade: gradeForPercent(pct)
  };
}

function gradeForPercent(pct) {
  if (pct >= 98) return "S";
  if (pct >= 90) return "A";
  if (pct >= 80) return "B";
  if (pct >= 65) return "C";
  if (pct >= 45) return "D";
  return "F";
}

function todayUTCString(d) {
  var date = d || new Date();
  var y = date.getUTCFullYear();
  var m = String(date.getUTCMonth() + 1).padStart(2, "0");
  var day = String(date.getUTCDate()).padStart(2, "0");
  return y + "-" + m + "-" + day;
}

var Engine = {
  CATEGORIES: CATEGORIES,
  PROJECT_POOL: PROJECT_POOL,
  DIFFICULTIES: DIFFICULTIES,
  hashStringToSeed: hashStringToSeed,
  mulberry32: mulberry32,
  dailySeedFor: dailySeedFor,
  shuffle: shuffle,
  generateValueTable: generateValueTable,
  drawProjects: drawProjects,
  drawDailyProjects: drawDailyProjects,
  drawPracticeProjects: drawPracticeProjects,
  projectValueAt: projectValueAt,
  solveOptimal: solveOptimal,
  scoreRound: scoreRound,
  gradeForPercent: gradeForPercent,
  todayUTCString: todayUTCString
};

if (typeof module !== "undefined" && module.exports) {
  module.exports = Engine;
} else {
  window.Engine = Engine;
}

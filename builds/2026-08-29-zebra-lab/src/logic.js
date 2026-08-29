// Zebra Lab — pure game logic: seeded RNG, solution generation, clue enumeration,
// a from-scratch CSP backtracking solver, minimality pruning, and clue-text formatting.
// No DOM access anywhere in this file so it can be loaded directly in Node for tests.

function zlHashStringToInt(str) {
  let h = 1779033703 ^ str.length;
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  return (h ^ (h >>> 16)) >>> 0;
}

function zlMakeRNG(seed) {
  let state = zlHashStringToInt(String(seed)) || 1;
  return function () {
    state |= 0;
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function zlShuffleCopy(arr, rng) {
  const copy = arr.slice();
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    const tmp = copy[i];
    copy[i] = copy[j];
    copy[j] = tmp;
  }
  return copy;
}

function zlInvert(arr) {
  const inv = new Array(arr.length);
  for (let i = 0; i < arr.length; i++) inv[arr[i]] = i;
  return inv;
}

function zlIdentity(n) {
  const arr = new Array(n);
  for (let i = 0; i < n; i++) arr[i] = i;
  return arr;
}

function zlFindCategory(categories, catId) {
  for (let i = 0; i < categories.length; i++) {
    if (categories[i].id === catId) return categories[i];
  }
  throw new Error('Unknown category id: ' + catId);
}

function zlBuildCategories(chapter) {
  return [zlMakePositionCategory(chapter.size)].concat(chapter.categories);
}

function zlGenerateSolution(categories, size, rng) {
  const solution = {};
  categories.forEach(function (cat) {
    if (cat.id === 'position') {
      solution[cat.id] = zlIdentity(size);
    } else {
      solution[cat.id] = zlShuffleCopy(zlIdentity(size), rng);
    }
  });
  return solution;
}

// Enumerate every clue that is TRUE against `solution`, restricted to allowedTypes.
function zlEnumerateTrueClues(categories, solution, allowedTypes) {
  const invMap = {};
  categories.forEach(function (cat) {
    invMap[cat.id] = zlInvert(solution[cat.id]);
  });
  const clues = [];
  for (let i = 0; i < categories.length; i++) {
    for (let j = i + 1; j < categories.length; j++) {
      const catI = categories[i];
      const catJ = categories[j];
      if (catI.id === 'position' && catJ.id === 'position') continue;
      for (let vi = 0; vi < catI.values.length; vi++) {
        for (let vj = 0; vj < catJ.values.length; vj++) {
          const posA = invMap[catI.id][vi];
          const posB = invMap[catJ.id][vj];
          if (posA === posB) {
            if (allowedTypes.indexOf('eq') >= 0) {
              clues.push({ type: 'eq', a: { cat: catI.id, val: vi }, b: { cat: catJ.id, val: vj } });
            }
          } else {
            if (allowedTypes.indexOf('neq') >= 0) {
              clues.push({ type: 'neq', a: { cat: catI.id, val: vi }, b: { cat: catJ.id, val: vj } });
            }
            if (allowedTypes.indexOf('adjacent') >= 0 && Math.abs(posA - posB) === 1) {
              clues.push({ type: 'adjacent', a: { cat: catI.id, val: vi }, b: { cat: catJ.id, val: vj } });
            }
            if (allowedTypes.indexOf('less') >= 0) {
              if (posA < posB) {
                clues.push({ type: 'less', a: { cat: catI.id, val: vi }, b: { cat: catJ.id, val: vj } });
              } else {
                clues.push({ type: 'less', a: { cat: catJ.id, val: vj }, b: { cat: catI.id, val: vi } });
              }
            }
          }
        }
      }
    }
  }
  return clues;
}

function zlCompatible(type, posA, posB) {
  if (type === 'eq') return posA === posB;
  if (type === 'neq') return posA !== posB;
  if (type === 'adjacent') return Math.abs(posA - posB) === 1;
  if (type === 'less') return posA < posB;
  throw new Error('Unknown clue type: ' + type);
}

function zlMakeFullDomains(attrCats, size) {
  const domains = {};
  attrCats.forEach(function (cat) {
    const rows = [];
    for (let p = 0; p < size; p++) rows.push(new Array(size).fill(true));
    domains[cat.id] = rows;
  });
  return domains;
}

function zlCloneDomains(domains, attrCats) {
  const out = {};
  attrCats.forEach(function (cat) {
    out[cat.id] = domains[cat.id].map(function (row) {
      return row.slice();
    });
  });
  return out;
}

// Positions still possible for a given (categoryId, valueIndex) cell.
function zlAllowedPositions(domains, size, catId, val) {
  if (catId === 'position') return [val];
  const out = [];
  for (let p = 0; p < size; p++) {
    if (domains[catId][p][val]) out.push(p);
  }
  return out;
}

// Standard "all-different" propagation within one category (naked/hidden singles).
function zlPropagateAllDiff(domains, size, catId) {
  let changed = false;
  const rows = domains[catId];
  // Hidden single: a value possible at only one position -> that position can't hold any other value.
  for (let v = 0; v < size; v++) {
    let onlyPos = -1;
    let count = 0;
    for (let p = 0; p < size; p++) {
      if (rows[p][v]) {
        count++;
        onlyPos = p;
      }
    }
    if (count === 0) return { changed: changed, contradiction: true };
    if (count === 1) {
      for (let v2 = 0; v2 < size; v2++) {
        if (v2 !== v && rows[onlyPos][v2]) {
          rows[onlyPos][v2] = false;
          changed = true;
        }
      }
    }
  }
  // Naked single: a position with only one possible value -> no other position can hold that value.
  for (let p = 0; p < size; p++) {
    let onlyVal = -1;
    let count = 0;
    for (let v = 0; v < size; v++) {
      if (rows[p][v]) {
        count++;
        onlyVal = v;
      }
    }
    if (count === 0) return { changed: changed, contradiction: true };
    if (count === 1) {
      for (let p2 = 0; p2 < size; p2++) {
        if (p2 !== p && rows[p2][onlyVal]) {
          rows[p2][onlyVal] = false;
          changed = true;
        }
      }
    }
  }
  return { changed: changed, contradiction: false };
}

// Arc-consistency propagation for a single clue relating two (category, value) cells.
function zlPropagateClueArc(domains, size, clue) {
  let changed = false;
  const sides = [
    { side: clue.a, other: clue.b, flip: false },
    { side: clue.b, other: clue.a, flip: true },
  ];
  for (let s = 0; s < sides.length; s++) {
    const side = sides[s].side;
    if (side.cat === 'position') continue; // fixed singleton, nothing to prune
    const otherAllowed = zlAllowedPositions(domains, size, sides[s].other.cat, sides[s].other.val);
    const myAllowed = zlAllowedPositions(domains, size, side.cat, side.val);
    for (let i = 0; i < myAllowed.length; i++) {
      const p = myAllowed[i];
      let supported = false;
      for (let j = 0; j < otherAllowed.length; j++) {
        const q = otherAllowed[j];
        const posA = sides[s].flip ? q : p;
        const posB = sides[s].flip ? p : q;
        if (zlCompatible(clue.type, posA, posB)) {
          supported = true;
          break;
        }
      }
      if (!supported) {
        domains[side.cat][p][side.val] = false;
        changed = true;
      }
    }
  }
  return changed;
}

// Propagate all constraints (all-different per category + every clue) to a fixpoint.
// Returns true if consistent, false if a contradiction was found.
function zlPropagateToFixpoint(domains, size, attrCats, clues) {
  let changed = true;
  while (changed) {
    changed = false;
    for (let i = 0; i < attrCats.length; i++) {
      const res = zlPropagateAllDiff(domains, size, attrCats[i].id);
      if (res.contradiction) return false;
      if (res.changed) changed = true;
    }
    for (let i = 0; i < clues.length; i++) {
      if (zlPropagateClueArc(domains, size, clues[i])) changed = true;
    }
    for (let i = 0; i < attrCats.length; i++) {
      const rows = domains[attrCats[i].id];
      for (let p = 0; p < size; p++) {
        if (!rows[p].some(Boolean)) return false;
      }
    }
  }
  return true;
}

function zlIsFullyDetermined(domains, size, attrCats) {
  for (let i = 0; i < attrCats.length; i++) {
    const rows = domains[attrCats[i].id];
    for (let p = 0; p < size; p++) {
      if (rows[p].filter(Boolean).length !== 1) return false;
    }
  }
  return true;
}

function zlExtractSolution(domains, size, attrCats) {
  const out = {};
  attrCats.forEach(function (cat) {
    const arr = new Array(size).fill(-1);
    for (let p = 0; p < size; p++) {
      arr[p] = domains[cat.id][p].indexOf(true);
    }
    out[cat.id] = arr;
  });
  return out;
}

// Pick the (category, position) cell with the fewest remaining candidates (>1) — MRV heuristic.
function zlPickBranchCell(domains, size, attrCats) {
  let best = null;
  let bestCount = Infinity;
  for (let i = 0; i < attrCats.length; i++) {
    const catId = attrCats[i].id;
    for (let p = 0; p < size; p++) {
      const count = domains[catId][p].filter(Boolean).length;
      if (count > 1 && count < bestCount) {
        bestCount = count;
        best = { catId: catId, p: p };
      }
    }
  }
  return best;
}

// Constraint-propagation + backtracking CSP solver (domain filtering, like a Sudoku solver,
// not naive brute force — needed because 5x5x4 zebra puzzles are far too large to brute force).
// Counts solutions up to `cap` (stops early once reached).
// Returns { count, solution (first found, or null), aborted (safety-cap hit) }.
function zlCountSolutions(categories, size, clues, cap) {
  const attrCats = categories.filter(function (c) {
    return c.id !== 'position';
  });
  const state = { count: 0, first: null, cap: cap, stop: false, nodes: 0, maxNodes: 200000 };

  function search(domains) {
    if (state.stop) return;
    state.nodes++;
    if (state.nodes > state.maxNodes) {
      state.stop = true;
      return;
    }
    if (!zlPropagateToFixpoint(domains, size, attrCats, clues)) return; // contradiction
    if (zlIsFullyDetermined(domains, size, attrCats)) {
      state.count++;
      if (!state.first) state.first = zlExtractSolution(domains, size, attrCats);
      if (state.count >= state.cap) state.stop = true;
      return;
    }
    const cell = zlPickBranchCell(domains, size, attrCats);
    const candidates = [];
    for (let v = 0; v < size; v++) {
      if (domains[cell.catId][cell.p][v]) candidates.push(v);
    }
    for (let i = 0; i < candidates.length; i++) {
      if (state.stop) return;
      const branch = zlCloneDomains(domains, attrCats);
      for (let v = 0; v < size; v++) branch[cell.catId][cell.p][v] = v === candidates[i];
      search(branch);
    }
  }

  search(zlMakeFullDomains(attrCats, size));
  return { count: state.count, solution: state.first, aborted: state.nodes > state.maxNodes };
}

function zlIsUnique(categories, size, clues) {
  return zlCountSolutions(categories, size, clues, 2).count === 1;
}

function zlPruneOnce(categories, size, clueSet, rng) {
  let current = clueSet.slice();
  let changed = true;
  while (changed) {
    changed = false;
    const order = zlShuffleCopy(current, rng);
    for (let i = 0; i < order.length; i++) {
      const trial = current.filter(function (c) {
        return c !== order[i];
      });
      if (zlIsUnique(categories, size, trial)) {
        current = trial;
        changed = true;
      }
    }
  }
  return current;
}

function zlGenerateClueSet(chapter, categories, solution, rng) {
  const allClues = zlEnumerateTrueClues(categories, solution, chapter.clueTypes);
  const pool = zlShuffleCopy(allClues, rng);
  let selected = [];
  for (let i = 0; i < pool.length; i++) {
    selected.push(pool[i]);
    if (zlIsUnique(categories, chapter.size, selected)) break;
  }
  const attempts = 1 + (chapter.extraPruningPasses || 0);
  let best = selected;
  for (let a = 0; a < attempts; a++) {
    const candidate = zlPruneOnce(categories, chapter.size, selected, rng);
    if (candidate.length < best.length) best = candidate;
  }
  return best;
}

function zlGeneratePuzzle(chapterId, seed) {
  const chapter = zlGetChapter(chapterId);
  const rng = zlMakeRNG(seed);
  const categories = zlBuildCategories(chapter);
  const solution = zlGenerateSolution(categories, chapter.size, rng);
  const clues = zlGenerateClueSet(chapter, categories, solution, rng);
  return {
    chapterId: chapterId,
    chapterName: chapter.name,
    size: chapter.size,
    categories: categories,
    solution: solution,
    clues: clues,
    seed: seed,
  };
}

function zlDailySeed(dateStr) {
  return 'daily-' + dateStr;
}

function zlTodayUtcString(date) {
  const d = date || new Date();
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, '0');
  const day = String(d.getUTCDate()).padStart(2, '0');
  return y + '-' + m + '-' + day;
}

function zlGenerateDailyPuzzle(dateStr) {
  return zlGeneratePuzzle(2, zlDailySeed(dateStr));
}

function zlFormatClue(clue, categories) {
  const posCat = zlFindCategory(categories, 'position');
  if (clue.a.cat === 'position' || clue.b.cat === 'position') {
    const posSide = clue.a.cat === 'position' ? clue.a : clue.b;
    const otherSide = clue.a.cat === 'position' ? clue.b : clue.a;
    const otherCat = zlFindCategory(categories, otherSide.cat);
    const otherLabel = otherCat.values[otherSide.val].label;
    const posLabel = posCat.values[posSide.val].label;
    if (clue.type === 'eq') return otherLabel + ' was ' + posLabel + '.';
    if (clue.type === 'neq') return otherLabel + ' was NOT ' + posLabel + '.';
    if (clue.type === 'adjacent') return otherLabel + '’s study is numbered immediately next to ' + posLabel + '.';
    if (clue.type === 'less') {
      if (clue.a.cat === 'position') return posLabel + ' comes before the study using ' + otherLabel + '.';
      return 'The study using ' + otherLabel + ' comes before ' + posLabel + '.';
    }
  }
  const catA = zlFindCategory(categories, clue.a.cat);
  const catB = zlFindCategory(categories, clue.b.cat);
  const labelA = catA.values[clue.a.val].label;
  const labelB = catB.values[clue.b.val].label;
  if (clue.type === 'eq') return 'The same study uses both ' + labelA + ' and ' + labelB + '.';
  if (clue.type === 'neq') return 'The study using ' + labelA + ' does NOT use ' + labelB + '.';
  if (clue.type === 'adjacent') {
    return 'The study using ' + labelA + ' is numbered immediately next to the study using ' + labelB + '.';
  }
  if (clue.type === 'less') {
    return 'The study using ' + labelA + ' has a lower study number than the study using ' + labelB + '.';
  }
  throw new Error('Unknown clue type: ' + clue.type);
}

function zlCountCorrectPositions(puzzle, playerAssign) {
  const attrCats = puzzle.categories.filter(function (c) {
    return c.id !== 'position';
  });
  let count = 0;
  for (let p = 0; p < puzzle.size; p++) {
    let ok = true;
    for (let i = 0; i < attrCats.length; i++) {
      const cat = attrCats[i];
      if (!playerAssign[cat.id] || playerAssign[cat.id][p] !== puzzle.solution[cat.id][p]) {
        ok = false;
        break;
      }
    }
    if (ok) count++;
  }
  return count;
}

function zlIsFullySolved(puzzle, playerAssign) {
  return zlCountCorrectPositions(puzzle, playerAssign) === puzzle.size;
}

function zlPickHintPosition(puzzle, playerAssign, rng) {
  const attrCats = puzzle.categories.filter(function (c) {
    return c.id !== 'position';
  });
  const incorrect = [];
  for (let p = 0; p < puzzle.size; p++) {
    let ok = true;
    for (let i = 0; i < attrCats.length; i++) {
      const cat = attrCats[i];
      if (!playerAssign[cat.id] || playerAssign[cat.id][p] !== puzzle.solution[cat.id][p]) {
        ok = false;
        break;
      }
    }
    if (!ok) incorrect.push(p);
  }
  const pool = incorrect.length > 0 ? incorrect : zlIdentity(puzzle.size);
  return pool[Math.floor(rng() * pool.length)];
}

function zlBuildShareString(dateStr, checksUsed, hintsUsed, solved) {
  let symbol = '⬛'; // black square: not solved
  if (solved) {
    symbol = checksUsed <= 1 && hintsUsed === 0 ? '🟩' : '🟨'; // green : yellow
  }
  return 'Zebra Lab ' + dateStr + '\n' + symbol + ' (' + checksUsed + ' checks, ' + hintsUsed + ' hints)';
}

function zlComposeExplanation(confoundId, threatId) {
  const methodText = ZL_METHOD_SNIPPETS[confoundId];
  const threatText = ZL_THREAT_SNIPPETS[threatId];
  const addresses = ZL_METHOD_ADDRESSES[confoundId] || [];
  const relevance =
    addresses.indexOf(threatId) >= 0
      ? 'This method directly helps guard against ' + threatText + '.'
      : 'This method does not, by itself, address ' + threatText + ' — a different safeguard would be needed for that.';
  return methodText + ' ' + relevance;
}

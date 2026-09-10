// Pure aggregation math over parsed SPARQL rows. No DOM, no network, no storage.

// rows: [{industry, province, count}]
function sumByKey(rows, key) {
  const totals = new Map();
  for (const row of rows) {
    const name = row[key];
    totals.set(name, (totals.get(name) || 0) + row.count);
  }
  return totals;
}

// Returns [{name, count, pct}] sorted by count desc, then name asc for stable ties.
function totalsToSortedList(totalsMap) {
  const grandTotal = Array.from(totalsMap.values()).reduce((a, b) => a + b, 0);
  const list = Array.from(totalsMap.entries()).map(([name, count]) => ({
    name,
    count,
    pct: grandTotal === 0 ? 0 : (count / grandTotal) * 100,
  }));
  list.sort((a, b) => (b.count - a.count) || a.name.localeCompare(b.name));
  return list;
}

function aggregateIndustryTotals(rows) {
  return totalsToSortedList(sumByKey(rows, 'industry'));
}

function aggregateProvinceTotals(rows) {
  return totalsToSortedList(sumByKey(rows, 'province'));
}

// Keeps the top n entries by count and folds the remainder into a single
// "Other" bucket (omitted entirely when there is no remainder).
function topNWithOther(sortedList, n) {
  if (sortedList.length <= n) return sortedList.slice();
  const top = sortedList.slice(0, n);
  const rest = sortedList.slice(n);
  const otherCount = rest.reduce((sum, item) => sum + item.count, 0);
  const otherPct = rest.reduce((sum, item) => sum + item.pct, 0);
  return [...top, { name: 'Other', count: otherCount, pct: otherPct }];
}

// previous/current: [{name, count}] (pct is ignored). Returns a Map name -> {
//   previousCount, currentCount, status: 'new' | 'removed' | 'increased' | 'decreased' | 'unchanged',
//   delta
// } covering every name seen in either list.
function computeDelta(previousList, currentList) {
  const previousMap = new Map((previousList || []).map((item) => [item.name, item.count]));
  const currentMap = new Map((currentList || []).map((item) => [item.name, item.count]));
  const allNames = new Set([...previousMap.keys(), ...currentMap.keys()]);
  const result = new Map();

  for (const name of allNames) {
    const hasPrevious = previousMap.has(name);
    const hasCurrent = currentMap.has(name);
    const previousCount = previousMap.get(name) || 0;
    const currentCount = currentMap.get(name) || 0;
    const delta = currentCount - previousCount;

    let status;
    if (!hasPrevious && hasCurrent) status = 'new';
    else if (hasPrevious && !hasCurrent) status = 'removed';
    else if (delta > 0) status = 'increased';
    else if (delta < 0) status = 'decreased';
    else status = 'unchanged';

    result.set(name, { previousCount, currentCount, status, delta });
  }
  return result;
}

const aggregateApi = {
  aggregateIndustryTotals,
  aggregateProvinceTotals,
  topNWithOther,
  computeDelta,
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = aggregateApi;
}
if (typeof window !== 'undefined') {
  window.DominionAggregate = aggregateApi;
}

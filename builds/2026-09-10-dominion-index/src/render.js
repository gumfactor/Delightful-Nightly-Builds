// DOM rendering + CSV helpers. External text (Wikidata labels) is ALWAYS
// inserted via textContent/DOM APIs, never innerHTML or string-built HTML,
// per STANDARDS.md's XSS rule.

function escapeCsvField(value) {
  const str = String(value);
  if (/[",\n]/.test(str)) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

// rows: [{industry, province, count}]
function rowsToCSV(rows) {
  const header = ['industry', 'province', 'count'];
  const lines = [header.join(',')];
  for (const row of rows) {
    lines.push([escapeCsvField(row.industry), escapeCsvField(row.province), row.count].join(','));
  }
  return lines.join('\r\n');
}

// Pure filter: case-insensitive substring match on industry or province.
function filterRows(rows, filterText) {
  if (!filterText) return rows.slice();
  const needle = filterText.toLowerCase();
  return rows.filter(
    (row) => row.industry.toLowerCase().includes(needle) || row.province.toLowerCase().includes(needle)
  );
}

// Pure sort. sortKey is 'industry' | 'province' | 'count'. direction is 1 or -1.
function sortRows(rows, sortKey, direction) {
  const copy = rows.slice();
  copy.sort((a, b) => {
    if (sortKey === 'count') return (a.count - b.count) * direction;
    return a[sortKey].localeCompare(b[sortKey]) * direction;
  });
  return copy;
}

function deltaLabel(deltaEntry) {
  if (!deltaEntry) return '';
  switch (deltaEntry.status) {
    case 'new':
      return 'new';
    case 'removed':
      return 'gone';
    case 'increased':
      return `+${deltaEntry.delta}`;
    case 'decreased':
      return `${deltaEntry.delta}`;
    default:
      return '—';
  }
}

// Clears tbody and rebuilds it from `rows`, attaching a delta badge per row
// when `deltaMap` (from aggregate.computeDelta, keyed by industry name) is given.
function renderTable(tbodyEl, rows, deltaMap) {
  tbodyEl.textContent = '';
  for (const row of rows) {
    const tr = document.createElement('tr');

    const industryTd = document.createElement('td');
    industryTd.textContent = row.industry;
    tr.appendChild(industryTd);

    const provinceTd = document.createElement('td');
    provinceTd.textContent = row.province;
    tr.appendChild(provinceTd);

    const countTd = document.createElement('td');
    countTd.textContent = String(row.count);
    tr.appendChild(countTd);

    const deltaTd = document.createElement('td');
    const entry = deltaMap ? deltaMap.get(row.industry) : null;
    deltaTd.textContent = deltaLabel(entry);
    if (entry) deltaTd.dataset.status = entry.status;
    tr.appendChild(deltaTd);

    tbodyEl.appendChild(tr);
  }
}

// Renders a simple totals list (used for the industry/province summary panels)
// as <li> elements with a name span, a count span, and an optional delta badge.
function renderTotalsList(listEl, totals, deltaMap) {
  listEl.textContent = '';
  for (const item of totals) {
    const li = document.createElement('li');

    const nameSpan = document.createElement('span');
    nameSpan.className = 'totals-name';
    nameSpan.textContent = item.name;
    li.appendChild(nameSpan);

    const countSpan = document.createElement('span');
    countSpan.className = 'totals-count';
    countSpan.textContent = `${item.count} (${item.pct.toFixed(1)}%)`;
    li.appendChild(countSpan);

    const entry = deltaMap ? deltaMap.get(item.name) : null;
    if (entry && entry.status !== 'unchanged') {
      const badge = document.createElement('span');
      badge.className = `delta-badge delta-${entry.status}`;
      badge.textContent = deltaLabel(entry);
      li.appendChild(badge);
    }

    listEl.appendChild(li);
  }
}

function buildChartConfig(totals, label, colors) {
  return {
    type: 'bar',
    data: {
      labels: totals.map((item) => item.name),
      datasets: [
        {
          label,
          data: totals.map((item) => item.count),
          backgroundColor: colors.bar,
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        x: { beginAtZero: true, ticks: { color: colors.text }, grid: { color: colors.grid } },
        y: { ticks: { color: colors.text }, grid: { display: false } },
      },
    },
  };
}

// Mounts (or remounts) a Chart.js chart on a canvas. Destroys any previous
// instance so repeated refreshes don't leak chart instances.
function mountChart(canvasEl, config, previousChart) {
  if (previousChart) previousChart.destroy();
  return new Chart(canvasEl, config);
}

const renderApi = {
  escapeCsvField,
  rowsToCSV,
  filterRows,
  sortRows,
  deltaLabel,
  renderTable,
  renderTotalsList,
  buildChartConfig,
  mountChart,
};

if (typeof module !== 'undefined' && module.exports) {
  module.exports = renderApi;
}
if (typeof window !== 'undefined') {
  window.DominionRender = renderApi;
}

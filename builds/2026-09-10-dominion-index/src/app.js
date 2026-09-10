(function () {
  'use strict';

  const THEME_KEY = 'dominion-index:theme';
  const TOP_N = 12;

  const els = {
    statusMessage: document.getElementById('status-message'),
    dashboard: document.getElementById('dashboard'),
    lastUpdated: document.getElementById('last-updated'),
    totalCount: document.getElementById('total-count'),
    csvExport: document.getElementById('csv-export'),
    refreshBtn: document.getElementById('refresh-btn'),
    themeToggle: document.getElementById('theme-toggle'),
    industryChartCanvas: document.getElementById('industry-chart'),
    provinceChartCanvas: document.getElementById('province-chart'),
    industryTotalsList: document.getElementById('industry-totals'),
    provinceTotalsList: document.getElementById('province-totals'),
    tableFilter: document.getElementById('table-filter'),
    resultsTbody: document.getElementById('results-tbody'),
    resultsTable: document.getElementById('results-table'),
  };

  const state = {
    rows: [],
    industryDelta: new Map(),
    provinceDelta: new Map(),
    sortKey: 'count',
    sortDirection: -1,
    filterText: '',
    industryChart: null,
    provinceChart: null,
  };

  function showStatus(text, kind) {
    els.statusMessage.textContent = text;
    els.statusMessage.className = `status ${kind}`;
    els.statusMessage.hidden = false;
  }

  function hideStatus() {
    els.statusMessage.hidden = true;
    els.statusMessage.textContent = '';
    els.statusMessage.className = 'status';
  }

  function getThemeColors() {
    const styles = getComputedStyle(document.documentElement);
    return {
      text: styles.getPropertyValue('--text-muted').trim(),
      grid: styles.getPropertyValue('--grid').trim(),
      bar: styles.getPropertyValue('--accent-bar').trim(),
    };
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    els.themeToggle.textContent = theme === 'dark' ? '🌙' : '☀️';
    try {
      window.localStorage.setItem(THEME_KEY, theme);
    } catch (err) {
      // Private-browsing storage lockouts are fine — theme just won't persist.
    }
    if (state.rows.length > 0) renderCharts();
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    applyTheme(current === 'dark' ? 'light' : 'dark');
  }

  function renderCharts() {
    const industryTotals = window.DominionAggregate.topNWithOther(
      window.DominionAggregate.aggregateIndustryTotals(state.rows),
      TOP_N
    );
    const provinceTotals = window.DominionAggregate.aggregateProvinceTotals(state.rows);
    const colors = getThemeColors();

    state.industryChart = window.DominionRender.mountChart(
      els.industryChartCanvas,
      window.DominionRender.buildChartConfig(industryTotals, 'Companies', colors),
      state.industryChart
    );
    state.provinceChart = window.DominionRender.mountChart(
      els.provinceChartCanvas,
      window.DominionRender.buildChartConfig(provinceTotals, 'Companies', colors),
      state.provinceChart
    );

    window.DominionRender.renderTotalsList(els.industryTotalsList, industryTotals, state.industryDelta);
    window.DominionRender.renderTotalsList(els.provinceTotalsList, provinceTotals, state.provinceDelta);
  }

  function renderTable() {
    const filtered = window.DominionRender.filterRows(state.rows, state.filterText);
    const sorted = window.DominionRender.sortRows(filtered, state.sortKey, state.sortDirection);
    window.DominionRender.renderTable(els.resultsTbody, sorted, state.industryDelta);
  }

  function setupCsvExport() {
    els.csvExport.addEventListener('click', (event) => {
      const csv = window.DominionRender.rowsToCSV(state.rows);
      const blob = new Blob([csv], { type: 'text/csv' });
      els.csvExport.href = URL.createObjectURL(blob);
    });
  }

  function setupTableInteractions() {
    els.tableFilter.addEventListener('input', (event) => {
      state.filterText = event.target.value;
      renderTable();
    });

    els.resultsTable.querySelectorAll('th[data-sort-key]').forEach((th) => {
      th.addEventListener('click', () => {
        const key = th.dataset.sortKey;
        if (state.sortKey === key) {
          state.sortDirection *= -1;
        } else {
          state.sortKey = key;
          state.sortDirection = key === 'count' ? -1 : 1;
        }
        renderTable();
      });
    });
  }

  function describeFetchError(err) {
    return (
      `Could not reach the Wikidata SPARQL endpoint (${err.message}). ` +
      'This can happen due to network restrictions, or because some browsers block cross-origin ' +
      'fetches from a page opened directly via file://. Try running a local static server ' +
      '(for example: python3 -m http.server, then open http://localhost:8000) and reload.'
    );
  }

  async function fetchAndRender() {
    hideStatus();
    showStatus('Querying Wikidata…', 'loading');
    els.dashboard.hidden = true;

    let response;
    try {
      response = await fetch(window.DominionSparql.buildQueryUrl(), {
        headers: { Accept: 'application/sparql-results+json' },
      });
    } catch (err) {
      showStatus(describeFetchError(err), 'error');
      return;
    }

    const bodyText = await response.text();

    if (!response.ok) {
      showStatus(`Wikidata returned HTTP ${response.status}: ${bodyText.slice(0, 400)}`, 'error');
      return;
    }

    let rows;
    try {
      rows = window.DominionSparql.parseResults(bodyText);
    } catch (err) {
      showStatus(err.message, 'error');
      return;
    }

    if (rows.length === 0) {
      showStatus('Wikidata returned zero matching companies. The query or the underlying data may have changed.', 'info');
      return;
    }

    state.rows = rows;

    const industryTotals = window.DominionAggregate.aggregateIndustryTotals(rows);
    const provinceTotals = window.DominionAggregate.aggregateProvinceTotals(rows);
    const previousSnapshot = window.DominionSnapshot.readSnapshot(window.localStorage);

    state.industryDelta = window.DominionAggregate.computeDelta(
      previousSnapshot ? previousSnapshot.industryTotals : [],
      industryTotals
    );
    state.provinceDelta = window.DominionAggregate.computeDelta(
      previousSnapshot ? previousSnapshot.provinceTotals : [],
      provinceTotals
    );

    const fetchedAt = new Date().toISOString();
    window.DominionSnapshot.writeSnapshot(window.localStorage, {
      fetchedAt,
      industryTotals: industryTotals.map(({ name, count }) => ({ name, count })),
      provinceTotals: provinceTotals.map(({ name, count }) => ({ name, count })),
    });

    els.lastUpdated.textContent = `Last updated: ${new Date(fetchedAt).toLocaleString()}`;
    const totalCompanies = industryTotals.reduce((sum, item) => sum + item.count, 0);
    els.totalCount.textContent = `${totalCompanies.toLocaleString()} companies across ${rows.length} industry/province pairs`;

    renderCharts();
    renderTable();
    hideStatus();
    els.dashboard.hidden = false;
  }

  function init() {
    let savedTheme = 'dark';
    try {
      savedTheme = window.localStorage.getItem(THEME_KEY) || 'dark';
    } catch (err) {
      // ignore — default to dark
    }
    applyTheme(savedTheme);

    els.refreshBtn.addEventListener('click', fetchAndRender);
    els.themeToggle.addEventListener('click', toggleTheme);
    setupCsvExport();
    setupTableInteractions();

    fetchAndRender();
  }

  window.DominionApp = { describeFetchError, state };
  document.addEventListener('DOMContentLoaded', init);
})();

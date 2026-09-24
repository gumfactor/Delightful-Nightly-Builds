/**
 * State + wiring. Ties window.OwnershipApi, window.OwnershipGraph, and
 * window.OwnershipRender together behind DOM event listeners. Exposed as
 * window.OwnershipApp mainly so tests can await its async operations and
 * inspect state directly instead of guessing at timing.
 */
(function (global) {
  'use strict';

  const RECENT_KEY = 'ownership-explorer:recent';
  const RECENT_LIMIT = 10;
  const SEARCH_DEBOUNCE_MS = 300;

  function createApp(doc) {
    const state = {
      focus: null,
      parentChainResult: { chain: [], cycleDetected: false, depthCapped: false },
      subsidiaries: [],
      history: [],
      recent: [],
    };

    const dom = {
      searchInput: doc.getElementById('search-input'),
      searchResults: doc.getElementById('search-results'),
      focusPanel: doc.getElementById('focus-panel'),
      parentChain: doc.getElementById('parent-chain'),
      subsidiaries: doc.getElementById('subsidiaries'),
      breadcrumb: doc.getElementById('breadcrumb'),
      recentList: doc.getElementById('recent-list'),
      errorBanner: doc.getElementById('error-banner'),
      loadingIndicator: doc.getElementById('loading-indicator'),
    };

    function loadRecent() {
      try {
        const raw = global.localStorage.getItem(RECENT_KEY);
        const parsed = raw ? JSON.parse(raw) : [];
        state.recent = Array.isArray(parsed) ? parsed : [];
      } catch (err) {
        state.recent = [];
      }
      global.OwnershipRender.renderRecent(dom.recentList, state.recent, (entry) => selectEntity(entry));
    }

    function saveRecent(entry) {
      state.recent = [entry, ...state.recent.filter((r) => r.id !== entry.id)].slice(0, RECENT_LIMIT);
      try {
        global.localStorage.setItem(RECENT_KEY, JSON.stringify(state.recent));
      } catch (err) {
        // Private browsing / storage disabled: recents just won't persist.
      }
      global.OwnershipRender.renderRecent(dom.recentList, state.recent, (entry2) => selectEntity(entry2));
    }

    function showError(message) {
      global.OwnershipRender.renderError(dom.errorBanner, message);
    }

    function setLoading(isLoading) {
      global.OwnershipRender.setLoading(dom.loadingIndicator, isLoading);
    }

    async function loadOwnershipData(entityId) {
      const [parentChainResult, subsidiaries] = await Promise.all([
        global.OwnershipGraph.buildParentChain(entityId, global.OwnershipApi.getPrimaryParent),
        global.OwnershipApi.fetchSubsidiaries(entityId),
      ]);
      return { parentChainResult, subsidiaries };
    }

    async function selectEntity(entity, options) {
      const opts = options || {};
      showError(null);
      dom.searchResults.hidden = true;
      dom.searchInput.value = '';

      state.focus = { id: entity.id, label: entity.label, description: entity.description || '' };
      global.OwnershipRender.renderFocusPanel(dom.focusPanel, state.focus);

      if (!opts.fromBreadcrumb) {
        state.history.push({ id: state.focus.id, label: state.focus.label });
      }
      global.OwnershipRender.renderBreadcrumb(dom.breadcrumb, state.history, (index) => jumpToHistory(index));
      saveRecent({ id: state.focus.id, label: state.focus.label, ts: Date.now() });

      setLoading(true);
      try {
        const { parentChainResult, subsidiaries } = await loadOwnershipData(entity.id);
        state.parentChainResult = parentChainResult;
        state.subsidiaries = subsidiaries;
        global.OwnershipRender.renderParentChain(dom.parentChain, parentChainResult, (node) => selectEntity(node));
        global.OwnershipRender.renderSubsidiaries(dom.subsidiaries, subsidiaries, (node) => selectEntity(node));
      } catch (err) {
        showError(err.message || 'Something went wrong fetching ownership data from Wikidata.');
        global.OwnershipRender.renderParentChain(dom.parentChain, { chain: [] }, () => {});
        global.OwnershipRender.renderSubsidiaries(dom.subsidiaries, [], () => {});
      } finally {
        setLoading(false);
      }
    }

    function jumpToHistory(index) {
      const entry = state.history[index];
      if (!entry) return;
      state.history = state.history.slice(0, index + 1);
      selectEntity(entry, { fromBreadcrumb: true });
    }

    let debounceTimer = null;
    async function handleSearchInput() {
      const query = dom.searchInput.value;
      if (debounceTimer) global.clearTimeout(debounceTimer);
      if (!query || !query.trim()) {
        global.OwnershipRender.renderSearchResults(dom.searchResults, [], () => {});
        return;
      }
      debounceTimer = global.setTimeout(async () => {
        try {
          const results = await global.OwnershipApi.searchEntities(query);
          global.OwnershipRender.renderSearchResults(dom.searchResults, results, (entity) => selectEntity(entity));
        } catch (err) {
          showError(err.message || 'Search failed.');
        }
      }, SEARCH_DEBOUNCE_MS);
    }

    function init() {
      loadRecent();
      global.OwnershipRender.renderFocusPanel(dom.focusPanel, null);
      global.OwnershipRender.renderParentChain(dom.parentChain, { chain: [] }, () => {});
      global.OwnershipRender.renderSubsidiaries(dom.subsidiaries, [], () => {});
      dom.searchInput.addEventListener('input', handleSearchInput);
      doc.addEventListener('click', (event) => {
        if (!dom.searchResults.contains(event.target) && event.target !== dom.searchInput) {
          dom.searchResults.hidden = true;
        }
      });
    }

    return { state, dom, init, selectEntity, jumpToHistory, handleSearchInput, loadRecent };
  }

  global.OwnershipApp = { createApp, RECENT_KEY, RECENT_LIMIT, SEARCH_DEBOUNCE_MS };

  if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
      const app = createApp(document);
      app.init();
      global.__ownershipApp = app; // for tests to await/inspect state
    });
  }
})(typeof window !== 'undefined' ? window : globalThis);

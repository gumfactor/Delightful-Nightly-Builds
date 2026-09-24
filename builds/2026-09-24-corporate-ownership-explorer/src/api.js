/**
 * Wikidata network access. Every function here does exactly one fetch and
 * hands the raw JSON to a pure parser in window.OwnershipGraph. Isolated in
 * its own file/namespace (window.OwnershipApi) so tests can stub
 * `window.fetch` and exercise these functions without ever touching
 * anything else in the app.
 */
(function (global) {
  'use strict';

  const SEARCH_ENDPOINT = 'https://www.wikidata.org/w/api.php';
  const SPARQL_ENDPOINT = 'https://query.wikidata.org/sparql';

  async function fetchJson(url, options) {
    let response;
    try {
      response = await fetch(url, options);
    } catch (err) {
      throw new Error(`Network request failed: ${err.message}`);
    }
    if (!response.ok) {
      throw new Error(`Wikidata request failed with status ${response.status}`);
    }
    try {
      return await response.json();
    } catch (err) {
      throw new Error('Wikidata returned an unreadable response.');
    }
  }

  function buildSearchUrl(query) {
    const params = new URLSearchParams({
      action: 'wbsearchentities',
      search: query,
      language: 'en',
      type: 'item',
      format: 'json',
      limit: '8',
      origin: '*',
    });
    return `${SEARCH_ENDPOINT}?${params.toString()}`;
  }

  function buildSparqlUrl(query) {
    const params = new URLSearchParams({ query, format: 'json' });
    return `${SPARQL_ENDPOINT}?${params.toString()}`;
  }

  /** Searches Wikidata for candidate companies matching free-text `query`. */
  async function searchEntities(query) {
    if (!query || !query.trim()) return [];
    const json = await fetchJson(buildSearchUrl(query), {
      headers: { Accept: 'application/json' },
    });
    return global.OwnershipGraph.parseSearchResults(json);
  }

  /**
   * Fetches every direct "owned by" (P127) / "parent organization" (P749)
   * statement recorded for `entityId`, with point-in-time/start/end
   * qualifiers when present. May return more than one candidate parent;
   * callers pick a primary one with OwnershipGraph.choosePrimaryParent.
   */
  async function fetchParents(entityId) {
    const query = `
      SELECT ?prop ?parent ?parentLabel ?pointInTime ?startTime ?endTime WHERE {
        {
          wd:${entityId} p:P127 ?stmt .
          ?stmt ps:P127 ?parent .
          BIND("P127" AS ?prop)
        } UNION {
          wd:${entityId} p:P749 ?stmt .
          ?stmt ps:P749 ?parent .
          BIND("P749" AS ?prop)
        }
        OPTIONAL { ?stmt pq:P585 ?pointInTime }
        OPTIONAL { ?stmt pq:P580 ?startTime }
        OPTIONAL { ?stmt pq:P582 ?endTime }
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
      }
    `.trim();
    const json = await fetchJson(buildSparqlUrl(query), {
      headers: { Accept: 'application/sparql-results+json' },
    });
    return global.OwnershipGraph.parseSparqlBindings(json, {
      idVar: 'parent',
      labelVar: 'parentLabel',
      propVar: 'prop',
      pointInTimeVar: 'pointInTime',
      startTimeVar: 'startTime',
      endTimeVar: 'endTime',
    });
  }

  /**
   * Fetches known subsidiaries of `entityId`: direct `subsidiary` (P355)
   * statements plus the reverse of `owned by`/`parent organization` (any
   * entity that names `entityId` as its own parent). Citation URLs differ
   * by direction — a P355 statement lives on `entityId` itself, while a
   * reverse P127/P749 statement lives on the subsidiary entity — so the
   * correct statement owner is attached per row here rather than in the
   * generic SPARQL-binding parser.
   */
  async function fetchSubsidiaries(entityId) {
    const query = `
      SELECT ?prop ?sub ?subLabel WHERE {
        {
          wd:${entityId} wdt:P355 ?sub .
          BIND("P355" AS ?prop)
        } UNION {
          ?sub wdt:P127 wd:${entityId} .
          BIND("P127" AS ?prop)
        } UNION {
          ?sub wdt:P749 wd:${entityId} .
          BIND("P749" AS ?prop)
        }
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
      }
    `.trim();
    const json = await fetchJson(buildSparqlUrl(query), {
      headers: { Accept: 'application/sparql-results+json' },
    });
    const rows = global.OwnershipGraph.parseSparqlBindings(json, {
      idVar: 'sub',
      labelVar: 'subLabel',
      propVar: 'prop',
    });
    const withCorrectCitation = rows.map((row) => {
      const statementOwnerId = row.property === 'P355' ? entityId : row.id;
      return {
        ...row,
        statementUrl: global.OwnershipGraph.formatCitationUrl(statementOwnerId, row.property),
      };
    });
    return global.OwnershipGraph.dedupeEntities(withCorrectCitation);
  }

  /**
   * Resolver used by OwnershipGraph.buildParentChain: fetches candidate
   * parents for `id` and reduces them to the single primary one (or null).
   */
  async function getPrimaryParent(entityId) {
    const parents = await fetchParents(entityId);
    return global.OwnershipGraph.choosePrimaryParent(parents);
  }

  global.OwnershipApi = {
    SEARCH_ENDPOINT,
    SPARQL_ENDPOINT,
    searchEntities,
    fetchParents,
    fetchSubsidiaries,
    getPrimaryParent,
  };
})(typeof window !== 'undefined' ? window : globalThis);

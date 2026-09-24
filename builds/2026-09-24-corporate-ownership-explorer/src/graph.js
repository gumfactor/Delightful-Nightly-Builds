/**
 * Pure ownership-chain logic. No network, no DOM. Exposed as window.OwnershipGraph
 * so tests can exercise every function directly via page.evaluate().
 */
(function (global) {
  'use strict';

  const OWNERSHIP_PROPS = ['P127', 'P749']; // owned by, parent organization
  const SUBSIDIARY_PROP = 'P355'; // subsidiary
  const MAX_CHAIN_DEPTH = 8;

  /**
   * Formats a Wikidata statement citation URL for a given entity + property.
   * This is the "citation back to Wikidata's own claim source" link: it opens
   * the exact statement on the entity's Wikidata page, where the reference
   * metadata (stated in, reference URL, retrieved date) Wikidata itself
   * records is visible.
   */
  function formatCitationUrl(entityId, propertyId) {
    if (!entityId || !propertyId) return null;
    return `https://www.wikidata.org/wiki/${entityId}#${propertyId}`;
  }

  /**
   * Formats ownership-edge qualifiers (point-in-time / start-end dates) into
   * a short human-readable string, or null when no relevant qualifier exists.
   * Accepts raw qualifier values already extracted as ISO-ish date strings
   * (e.g. "2020-00-00T00:00:00Z" per Wikidata's time format) or plain years.
   */
  function formatQualifiers(qualifiers) {
    if (!qualifiers) return null;
    const { pointInTime, startTime, endTime } = qualifiers;

    const toYear = (raw) => {
      if (!raw) return null;
      const match = String(raw).match(/-?\d{1,6}/);
      return match ? match[0].replace(/^0+(?=\d)/, '') : null;
    };

    if (pointInTime) {
      const year = toYear(pointInTime);
      return year ? `as of ${year}` : null;
    }
    if (startTime && endTime) {
      const startYear = toYear(startTime);
      const endYear = toYear(endTime);
      if (startYear && endYear) return `${startYear}–${endYear}`;
    }
    if (startTime) {
      const year = toYear(startTime);
      return year ? `since ${year}` : null;
    }
    if (endTime) {
      const year = toYear(endTime);
      return year ? `until ${year}` : null;
    }
    return null;
  }

  /**
   * Removes duplicate entities from a list, keeping the first occurrence.
   * Two entries are duplicates when they share the same `id`.
   */
  function dedupeEntities(list) {
    const seen = new Set();
    const out = [];
    for (const item of list || []) {
      if (!item || !item.id) continue;
      if (seen.has(item.id)) continue;
      seen.add(item.id);
      out.push(item);
    }
    return out;
  }

  /**
   * Parses a Wikidata `wbsearchentities` JSON response into a normalized
   * list of candidates. Returns [] for empty/malformed input rather than
   * throwing, since a "no results" search is a normal, expected outcome.
   */
  function parseSearchResults(json) {
    if (!json || !Array.isArray(json.search)) return [];
    return json.search
      .filter((entry) => entry && entry.id)
      .map((entry) => ({
        id: entry.id,
        label: entry.label || entry.id,
        description: entry.description || '',
      }));
  }

  /**
   * Parses SPARQL JSON results (the `results.bindings` shape) into a
   * normalized list of { id, label, property, qualifierText } records.
   * `varNames` maps logical roles to the SPARQL variable names used in the
   * query, since the same parser serves both the parent-chain query and the
   * subsidiaries query with different variable names.
   */
  function parseSparqlBindings(json, varNames) {
    const { idVar, labelVar, propVar, pointInTimeVar, startTimeVar, endTimeVar } = varNames || {};
    if (!json || !json.results || !Array.isArray(json.results.bindings)) return [];

    const extractId = (uri) => {
      if (!uri) return null;
      const match = String(uri).match(/Q\d+$/);
      return match ? match[0] : null;
    };
    const extractProp = (uri) => {
      if (!uri) return null;
      const match = String(uri).match(/P\d+$/);
      return match ? match[0] : null;
    };

    return json.results.bindings
      .map((row) => {
        const idBinding = idVar && row[idVar];
        const id = idBinding ? extractId(idBinding.value) : null;
        if (!id) return null;

        const labelBinding = labelVar && row[labelVar];
        const label = labelBinding ? labelBinding.value : id;

        const propBinding = propVar && row[propVar];
        const property = propBinding ? extractProp(propBinding.value) : null;

        const qualifiers = {
          pointInTime: pointInTimeVar && row[pointInTimeVar] ? row[pointInTimeVar].value : null,
          startTime: startTimeVar && row[startTimeVar] ? row[startTimeVar].value : null,
          endTime: endTimeVar && row[endTimeVar] ? row[endTimeVar].value : null,
        };
        const qualifierText = formatQualifiers(qualifiers);

        return {
          id,
          label,
          property,
          qualifierText,
          statementUrl: property ? formatCitationUrl(id, property) : null,
        };
      })
      .filter(Boolean);
  }

  /**
   * Builds the upward parent-ownership chain starting from `startId` by
   * repeatedly calling `getParent(id)`, an async function returning either
   * `null` (no further parent) or `{ id, label, property, qualifierText }`
   * for the immediate parent of `id`.
   *
   * Stops on: no parent found, a cycle (a parent id already seen in this
   * chain, including the start entity itself), or MAX_CHAIN_DEPTH hops.
   * Returns { chain, cycleDetected, depthCapped }.
   */
  async function buildParentChain(startId, getParent, maxDepth) {
    const cap = typeof maxDepth === 'number' ? maxDepth : MAX_CHAIN_DEPTH;
    const chain = [];
    const visited = new Set([startId]);
    let currentId = startId;
    let cycleDetected = false;
    let depthCapped = false;

    for (let hop = 0; hop < cap; hop += 1) {
      const parent = await getParent(currentId);
      if (!parent || !parent.id) break;

      if (visited.has(parent.id)) {
        cycleDetected = true;
        break;
      }

      visited.add(parent.id);
      chain.push(parent);
      currentId = parent.id;

      if (hop === cap - 1) {
        // Reached the cap this iteration; check whether more would exist.
        const next = await getParent(currentId);
        if (next && next.id && !visited.has(next.id)) {
          depthCapped = true;
        }
      }
    }

    return { chain, cycleDetected, depthCapped };
  }

  /**
   * Deterministically picks one "primary" parent from a list of candidate
   * ownership edges when Wikidata records more than one (e.g. joint
   * ventures, or both P127 and P749 recorded). Prefers `owned by` (P127)
   * over `parent organization` (P749), then breaks remaining ties by
   * ascending entity id, so the same input always yields the same choice.
   * Returns null for an empty list.
   */
  function choosePrimaryParent(parents) {
    if (!parents || parents.length === 0) return null;
    const propRank = (p) => (p.property === 'P127' ? 0 : p.property === 'P749' ? 1 : 2);
    const sorted = [...parents].sort((a, b) => {
      const rankDiff = propRank(a) - propRank(b);
      if (rankDiff !== 0) return rankDiff;
      return String(a.id).localeCompare(String(b.id));
    });
    return sorted[0];
  }

  global.OwnershipGraph = {
    OWNERSHIP_PROPS,
    SUBSIDIARY_PROP,
    MAX_CHAIN_DEPTH,
    formatCitationUrl,
    formatQualifiers,
    dedupeEntities,
    parseSearchResults,
    parseSparqlBindings,
    buildParentChain,
    choosePrimaryParent,
  };
})(typeof window !== 'undefined' ? window : globalThis);

// SPARQL query builder and result parser for the Wikidata Query Service.
// Pure functions — no DOM, no network. `app.js` owns the actual fetch call.

const WIKIDATA_ENDPOINT = 'https://query.wikidata.org/sparql';

const PROVINCE_QIDS = [
  'wd:Q1904',  // Ontario
  'wd:Q176',   // Quebec
  'wd:Q1974',  // British Columbia
  'wd:Q1951',  // Alberta
  'wd:Q1948',  // Manitoba
  'wd:Q1989',  // Saskatchewan
  'wd:Q13603', // Nova Scotia
  'wd:Q1952',  // New Brunswick
  'wd:Q1926',  // Newfoundland and Labrador
  'wd:Q1965',  // Prince Edward Island
  'wd:Q13575', // Northwest Territories
  'wd:Q2003',  // Yukon
  'wd:Q2023',  // Nunavut
];

function buildQuery() {
  return `SELECT ?industryLabel ?provinceLabel (COUNT(DISTINCT ?company) AS ?count) WHERE {
  ?company wdt:P31/wdt:P279* wd:Q4830453 .
  ?company wdt:P159 ?hq .
  ?hq wdt:P17 wd:Q16 .
  FILTER NOT EXISTS {
    { ?company wdt:P749 ?parent } UNION { ?company wdt:P127 ?parent }
    ?parent wdt:P17 ?parentCountry .
    FILTER(?parentCountry != wd:Q16)
  }
  OPTIONAL {
    ?company wdt:P452 ?industry .
    ?industry rdfs:label ?industryLabelRaw . FILTER(LANG(?industryLabelRaw) = "en")
  }
  BIND(COALESCE(?industryLabelRaw, "Unclassified") AS ?industryLabel)
  OPTIONAL {
    VALUES ?province { ${PROVINCE_QIDS.join(' ')} }
    ?hq wdt:P131* ?province .
    ?province rdfs:label ?provinceLabelRaw . FILTER(LANG(?provinceLabelRaw) = "en")
  }
  BIND(COALESCE(?provinceLabelRaw, "Unknown") AS ?provinceLabel)
}
GROUP BY ?industryLabel ?provinceLabel
ORDER BY DESC(?count)`;
}

function buildQueryUrl() {
  const params = new URLSearchParams({ query: buildQuery(), format: 'json' });
  return `${WIKIDATA_ENDPOINT}?${params.toString()}`;
}

class SparqlResultError extends Error {
  constructor(message) {
    super(message);
    this.name = 'SparqlResultError';
  }
}

// Parses a Wikidata SPARQL JSON response into [{industry, province, count}, ...].
// Throws SparqlResultError with a specific, user-facing message on any shape
// that isn't a valid SPARQL results document — callers show this text verbatim.
function parseResults(body) {
  let data;
  if (typeof body === 'string') {
    try {
      data = JSON.parse(body);
    } catch (err) {
      throw new SparqlResultError(
        `Wikidata did not return valid JSON (${err.message}). The endpoint may be reporting an error as plain text.`
      );
    }
  } else if (body && typeof body === 'object') {
    data = body;
  } else {
    throw new SparqlResultError('Wikidata response was empty or not an object.');
  }

  if (!data.results || !Array.isArray(data.results.bindings)) {
    throw new SparqlResultError(
      'Wikidata response was missing the expected results.bindings array — the query shape may no longer match Wikidata\'s schema.'
    );
  }

  return data.results.bindings.map((row, index) => {
    const industry = row.industryLabel && row.industryLabel.value;
    const province = row.provinceLabel && row.provinceLabel.value;
    const countRaw = row.count && row.count.value;
    if (!industry || !province || countRaw === undefined) {
      throw new SparqlResultError(
        `Row ${index} of the Wikidata response was missing industryLabel, provinceLabel, or count.`
      );
    }
    const count = Number(countRaw);
    if (!Number.isFinite(count) || count < 0) {
      throw new SparqlResultError(`Row ${index} had a non-numeric count: "${countRaw}".`);
    }
    return { industry, province, count };
  });
}

const sparqlApi = { buildQuery, buildQueryUrl, parseResults, SparqlResultError, PROVINCE_QIDS, WIKIDATA_ENDPOINT };

if (typeof module !== 'undefined' && module.exports) {
  module.exports = sparqlApi;
}
if (typeof window !== 'undefined') {
  window.DominionSparql = sparqlApi;
}

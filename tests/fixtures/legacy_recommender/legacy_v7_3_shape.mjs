// Synthesised v7.3.0-era recommender.js shape — used only as a
// backwards-compatibility test harness. This module embodies the
// pre-v9.0 client contract:
//
//   - Reads only the four legacy endpoints (sourcetype, cim, app, thin).
//   - Has never heard of /recommender/splunkbase-index.json.
//   - Treats every UC row in uc-thin.json as Object<string, unknown> —
//     therefore tolerates unknown keys (the new `sb` field) silently.
//
// We assert that the v9.0 catalogue payloads remain parseable by this
// pre-v9 shape — i.e. that the schema additions are additive only.
// If a future change ever drops a legacy field, this test fails.

export const LEGACY_ENDPOINTS = [
  ['sourcetypes', '/recommender/sourcetype-index.json'],
  ['cim',         '/recommender/cim-index.json'],
  ['apps',        '/recommender/app-index.json'],
  ['thin',        '/recommender/uc-thin.json'],
];

export async function legacyLoadRemoteIndexes(apiBase, fetchImpl) {
  const out = { sourcetypes: {}, cim: {}, apps: {}, thin: {} };
  for (const [name, ep] of LEGACY_ENDPOINTS) {
    const r = await fetchImpl(apiBase + ep);
    if (!r.ok) throw new Error('HTTP ' + r.status + ' for ' + ep);
    const body = await r.json();
    if (name === 'sourcetypes') out.sourcetypes = body.sourcetypes || {};
    else if (name === 'cim') out.cim = body.cimModels || {};
    else if (name === 'apps') out.apps = body.apps || {};
    else if (name === 'thin') {
      out.thin = (body.useCases || []).reduce((acc, r) => {
        // Legacy client deliberately discards unknown keys
        // (e.g. v9.0's new `splunkbaseApps` field). If a future
        // catalogue change renames id/title/criticality/value, the
        // assertions below trip and we know the additive-only
        // contract was broken.
        acc[r.id] = {
          id: r.id,
          title: r.title,
          criticality: r.criticality,
          value: r.value,
        };
        return acc;
      }, {});
    }
  }
  return out;
}

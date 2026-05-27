#!/usr/bin/env node
/**
 * Generate __tests__/catalogue-snapshot.json — for each source in the
 * v2 catalogue, run its compute function with the "typical" profile-resolved
 * driver values and freeze the {eps, bytesPerEvent} tuple it produces
 * (eps already multiplied by the source's typical uncertainty factor).
 *
 * The CI test `catalogue-snapshot.test.js` then asserts every source still
 * produces the same numbers, catching silent drift from compute-function
 * edits, schema-allowed driver-default tweaks, or catalogue renames.
 *
 * Intentional updates (e.g. re-calibrating a source) should re-run this
 * script and commit the regenerated snapshot in the same change.
 *
 * Usage:
 *   node tools/data-sizing/scripts/generate-snapshot.js
 */
const fs   = require('fs');
const path = require('path');

global.window = {};
require(path.join(__dirname, '..', 'compute-functions.js'));
require(path.join(__dirname, '..', 'ot-data-sources.js'));
const SOURCES = global.window.OT_DATA_SOURCES;
const COMPUTE = global.window.COMPUTE_FUNCTIONS;

const PROFILE = 'typical';

function defaultDriverValues(src) {
  const out = {};
  (src.drivers || []).forEach(d => {
    const preset = (d.profilePresets || {})[PROFILE];
    out[d.id] = preset !== undefined ? preset : d.default;
  });
  return out;
}

const snapshot = {};
SOURCES.forEach(src => {
  const fn = COMPUTE[src.compute];
  if (typeof fn !== 'function') {
    snapshot[src.id] = { error: 'missing compute: ' + src.compute };
    return;
  }
  const result = fn(defaultDriverValues(src), PROFILE);
  const u = (src.uncertainty || {})[PROFILE] || 1.0;
  snapshot[src.id] = {
    eps:           +(result.eps * u).toFixed(6),
    bytesPerEvent: +result.bytesPerEvent.toFixed(6)
  };
});

const outPath = path.join(__dirname, '..', '__tests__', 'catalogue-snapshot.json');
fs.writeFileSync(outPath, JSON.stringify(snapshot, null, 2) + '\n');
console.log('Wrote snapshot for ' + Object.keys(snapshot).length + ' sources.');

/**
 * Catalogue snapshot regression guard.
 *
 * For every source in the v2 catalogue, run its compute function with the
 * "typical" profile-resolved driver values, multiply EPS by the source's
 * typical uncertainty factor, and assert the produced {eps, bytesPerEvent}
 * tuple matches the frozen value in `catalogue-snapshot.json`.
 *
 * If this test fails after a deliberate change (re-calibration, formula
 * tweak, new source, retirement), regenerate the snapshot in the same
 * commit:
 *
 *   node tools/data-sizing/scripts/generate-snapshot.js
 *
 * The reverse check (snapshot entry exists but source is gone) catches
 * silent deletions.
 */
const test   = require('node:test');
const assert = require('node:assert/strict');
const fs     = require('node:fs');
const path   = require('node:path');

global.window = {};
require(path.join(__dirname, '..', 'compute-functions.js'));
require(path.join(__dirname, '..', 'ot-data-sources.js'));
const SOURCES = global.window.OT_DATA_SOURCES;
const COMPUTE = global.window.COMPUTE_FUNCTIONS;

const SNAPSHOT = JSON.parse(fs.readFileSync(
  path.join(__dirname, 'catalogue-snapshot.json'), 'utf8'));

const PROFILE = 'typical';

function defaultDriverValues(src) {
  const out = {};
  (src.drivers || []).forEach(d => {
    const preset = (d.profilePresets || {})[PROFILE];
    out[d.id] = preset !== undefined ? preset : d.default;
  });
  return out;
}

test('catalogue snapshot — every source produces frozen {eps, bytesPerEvent}', () => {
  const drift = [];
  SOURCES.forEach(src => {
    const fn = COMPUTE[src.compute];
    if (typeof fn !== 'function') {
      drift.push(`${src.id}: missing compute ${src.compute}`);
      return;
    }
    const u = (src.uncertainty || {})[PROFILE] || 1.0;
    const out = fn(defaultDriverValues(src), PROFILE);
    const actual = {
      eps:           +(out.eps * u).toFixed(6),
      bytesPerEvent: +out.bytesPerEvent.toFixed(6)
    };
    const expected = SNAPSHOT[src.id];
    if (!expected) {
      drift.push(`${src.id}: not in snapshot (run generate-snapshot.js)`);
      return;
    }
    if (actual.eps !== expected.eps || actual.bytesPerEvent !== expected.bytesPerEvent) {
      drift.push(`${src.id}: expected ${JSON.stringify(expected)} got ${JSON.stringify(actual)}`);
    }
  });
  Object.keys(SNAPSHOT).forEach(id => {
    if (!SOURCES.find(s => s.id === id)) {
      drift.push(`${id}: in snapshot but not in catalogue`);
    }
  });
  assert.deepEqual(drift, [],
    'Catalogue drift detected — review changes, then regenerate the snapshot:\n' +
    '  node tools/data-sizing/scripts/generate-snapshot.js');
});

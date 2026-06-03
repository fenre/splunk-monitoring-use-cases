/**
 * Headless smoke harness for the v2 Data Sizing tool.
 *
 * Automates every pure-compute / pure-data item from the release-time
 * browser smoke checklist (`tools/data-sizing/README.md` →
 * "Browser smoke checklist"). The DOM-only items (badge colour, modal
 * open/close, clipboard copy, file download trigger, the visible
 * disclosure body) MUST still be confirmed in a real browser before a
 * release tag — but the numeric and data layers are guarded here so the
 * eyeball pass can focus on rendering.
 *
 * Pure-engine logic is reimplemented in-process: app.js inlines the
 * storage math, the share-URL serialiser, the share-URL parser, and the
 * CSV column synthesis inside DOM handlers, so they are not callable
 * from Node. Each reimplementation below is byte-for-byte ported from
 * app.js; the line references next to each block tell future-you which
 * fragment to keep in sync if app.js changes.
 *
 * Original delivery context: Task 39 of
 * `docs/superpowers/plans/2026-05-27-data-sizing-realism.md`, v8.7.0
 * release-time smoke gate.
 */
'use strict';

const test   = require('node:test');
const assert = require('node:assert/strict');
const fs     = require('node:fs');
const path   = require('node:path');

global.window = {};
require(path.join(__dirname, '..', 'compute-functions.js'));
require(path.join(__dirname, '..', 'ot-data-sources.js'));
const SOURCES = global.window.OT_DATA_SOURCES;
const COMPUTE = global.window.COMPUTE_FUNCTIONS;

const SECONDS_PER_DAY = 86400;
const BYTES_PER_GB    = 1e9;

function findSource(id) {
  const s = SOURCES.find(x => x.id === id);
  if (!s) throw new Error('catalogue is missing source ' + id);
  return s;
}

// ---------------------------------------------------------------------------
// Ports of the engine bits that app.js inlines inside DOM handlers.
// Keep in lock-step with the line numbers in the comment above each fn.
// ---------------------------------------------------------------------------

// app.js — runComputeForInstance() at line 86.
function runComputeForInstance(entry, profile) {
  const src = entry.source;
  const fn = COMPUTE[src.compute];
  if (typeof fn !== 'function') throw new Error('missing compute: ' + src.compute);
  const driverValues = {};
  (src.drivers || []).forEach(d => {
    const presets = d.profilePresets || {};
    const override = entry.driverValues && entry.driverValues[d.id];
    if (override !== undefined)              driverValues[d.id] = override;
    else if (presets[profile] !== undefined) driverValues[d.id] = presets[profile];
    else                                     driverValues[d.id] = d.default;
  });
  const out = fn(driverValues, profile);
  const u = (src.uncertainty || {})[profile] || 1.0;
  return { eps: out.eps * u, bytesPerEvent: out.bytesPerEvent };
}

// app.js — getInstanceGBDay() at line 319.
function instanceGBDay(entry, profile) {
  const r = runComputeForInstance(entry, profile);
  const filt = (entry.source.realism || {}).filterable_fraction_typical || 0;
  const effEps = r.eps * (1 - filt);
  return (effEps * SECONDS_PER_DAY * r.bytesPerEvent) / BYTES_PER_GB;
}

// app.js — computeTotals() at line 457 (cluster math: RF / SF / SmartStore /
// indexer-count branches).
function computeTotals(entries, cluster, profile) {
  let totalDailyRawGB = 0, totalClusterRawGB = 0, totalClusterTsidxGB = 0;
  entries.forEach(entry => {
    const r = runComputeForInstance(entry, profile);
    const s = entry.source;
    const filt = (s.realism || {}).filterable_fraction_typical || 0;
    const effEps = r.eps * (1 - filt);
    const gbDay  = (effEps * SECONDS_PER_DAY * r.bytesPerEvent) / BYTES_PER_GB;
    const rawdataC = (s.realism || {}).rawdata_compression_typical || 0.15;
    const tsidxC   = (s.realism || {}).tsidx_overhead_typical      || 0.35;
    const rfMul = cluster.smartstore ? 1 : cluster.rf;
    totalDailyRawGB     += gbDay;
    totalClusterRawGB   += gbDay * rawdataC * rfMul;
    totalClusterTsidxGB += gbDay * tsidxC   * cluster.sf;
  });
  const totalClusterGB = totalClusterRawGB + totalClusterTsidxGB;
  const perIndexerGB   = totalClusterGB / Math.max(1, cluster.indexerCount);
  return { totalDailyRawGB, totalClusterRawGB, totalClusterTsidxGB, totalClusterGB, perIndexerGB };
}

// app.js — Share-URL serialiser at line 998; parser at line 1082. The
// serialiser only emits driver overrides that differ from the (profile
// preset or default) baseline so the URL stays short.
function buildShareUrl(entries, profile) {
  return entries.map(entry => {
    const pairs = [];
    (entry.source.drivers || []).forEach(d => {
      if (!entry.driverValues || entry.driverValues[d.id] === undefined) return;
      const current = entry.driverValues[d.id];
      const preset = (d.profilePresets && d.profilePresets[profile] !== undefined)
                       ? d.profilePresets[profile] : d.default;
      if (current !== preset) pairs.push(d.id + '=' + current);
    });
    return entry.source.id + (pairs.length ? ':' + pairs.join(',') : '');
  }).join('|');
}

function parseShareUrl(encoded) {
  const out = [];
  encoded.split('|').filter(Boolean).forEach(part => {
    const bits = part.split(':');
    const sid = bits[0].trim();
    const src = findSource(sid);
    const entry = { source: src, driverValues: {} };
    if (bits[1]) {
      bits[1].split(',').forEach(kv => {
        const eq = kv.indexOf('=');
        if (eq <= 0) return;
        const k = kv.slice(0, eq).trim();
        const v = kv.slice(eq + 1).trim();
        const driver = (src.drivers || []).find(d => d.id === k);
        if (!driver) return;
        entry.driverValues[k] = (driver.type === 'number') ? parseFloat(v) : v;
      });
    }
    out.push(entry);
  });
  return out;
}

// ---------------------------------------------------------------------------
// Item 2 — Palo Alto NGFW @ 1.0 Gbps / Traffic + Threat
// Expected: 4,500 EPS raw → 3,600 EPS effective (after 20% filterable
// fraction) → ~560 GB/day. Matches PAN-OS log-storage tables.
// ---------------------------------------------------------------------------
test('item 2 — PAN @ 1.0 Gbps / traffic+threat produces 4,500 EPS and ~560 GB/day', () => {
  const src = findSource('sec_ngfw_paloalto');
  const entry = {
    source: src,
    driverValues: { throughput_gbps: 1.0, log_profile: 'traffic+threat' }
  };
  const r = runComputeForInstance(entry, 'typical');
  const gbDay = instanceGBDay(entry, 'typical');
  assert.equal(r.eps, 4500, 'raw EPS should be exactly 4,500 per PAN calibration');
  assert.equal(r.bytesPerEvent, 1800, 'bytes/event should be exactly 1,800 per PAN calibration');
  // 4500 * (1-0.2) * 86400 * 1800 / 1e9 ≈ 559.872
  assert.ok(Math.abs(gbDay - 559.872) < 1.0,
    'effective GB/day should be ~560; got ' + gbDay.toFixed(3));
});

// ---------------------------------------------------------------------------
// Item 3 — Modbus @ 500 tags / 30s poll / 0.40 deadband
// 500 tags / 30s = 16.67 polls/s; deadband filters 40% → ~10 EPS emitted.
// ---------------------------------------------------------------------------
test('item 3 — Modbus @ 500 tags / 30s poll / 0.4 deadband produces ~10 EPS', () => {
  const src = findSource('proto_modbus');
  const entry = {
    source: src,
    driverValues: { tag_count: 500, poll_interval_sec: 30, deadband_ratio: 0.40 }
  };
  const r = runComputeForInstance(entry, 'typical');
  assert.ok(r.eps > 6 && r.eps < 14,
    'raw EPS should land near 10 after deadband filter; got ' + r.eps.toFixed(2));
});

// ---------------------------------------------------------------------------
// Item 4 — A pending source's disclosure renders the "no citations yet"
// warning branch. Verifies the catalogue still carries unflagged pending
// sources for the disclosure to display against.
// ---------------------------------------------------------------------------
test('item 4 — at least one pending source has no citations (drives disclosure branch)', () => {
  const pending = SOURCES.filter(s => s.calibration === 'pending');
  assert.ok(pending.length > 0, 'expected at least one pending source');
  const sample = pending[0];
  assert.equal(sample.calibration, 'pending');
  const cites = sample.citations || [];
  assert.equal(cites.length, 0,
    'pending source ' + sample.id + ' should not carry citations yet');
});

// ---------------------------------------------------------------------------
// Item 5 — SmartStore on drops cluster-raw by the RF multiplier.
// ---------------------------------------------------------------------------
test('item 5 — SmartStore on divides cluster-raw by RF', () => {
  const src = findSource('sec_ngfw_paloalto');
  const entry = { source: src, driverValues: { throughput_gbps: 1.0, log_profile: 'traffic+threat' } };
  const off = computeTotals([entry], { rf: 2, sf: 2, smartstore: false, indexerCount: 3 }, 'typical');
  const on  = computeTotals([entry], { rf: 2, sf: 2, smartstore: true,  indexerCount: 3 }, 'typical');
  assert.ok(Math.abs(on.totalClusterRawGB - off.totalClusterRawGB / 2) < 1e-6,
    'SmartStore-on cluster-raw should equal SmartStore-off / RF; got ' +
    on.totalClusterRawGB + ' vs expected ' + (off.totalClusterRawGB / 2));
});

// ---------------------------------------------------------------------------
// Item 6 — RF=3 scales cluster-raw by 1.5× vs RF=2.
// ---------------------------------------------------------------------------
test('item 6 — RF=3 scales cluster-raw by 1.5× vs RF=2', () => {
  const src = findSource('sec_ngfw_paloalto');
  const entry = { source: src, driverValues: { throughput_gbps: 1.0, log_profile: 'traffic+threat' } };
  const rf2 = computeTotals([entry], { rf: 2, sf: 2, smartstore: false, indexerCount: 3 }, 'typical');
  const rf3 = computeTotals([entry], { rf: 3, sf: 2, smartstore: false, indexerCount: 3 }, 'typical');
  const ratio = rf3.totalClusterRawGB / rf2.totalClusterRawGB;
  assert.ok(Math.abs(ratio - 1.5) < 1e-6, 'expected ratio 1.5; got ' + ratio);
});

// ---------------------------------------------------------------------------
// Item 7 — Indexer count divides through to per-indexer storage.
// ---------------------------------------------------------------------------
test('item 7 — per-indexer GB = totalClusterGB / indexerCount', () => {
  const src = findSource('sec_ngfw_paloalto');
  const entry = { source: src, driverValues: { throughput_gbps: 1.0, log_profile: 'traffic+threat' } };
  const five = computeTotals([entry], { rf: 2, sf: 2, smartstore: false, indexerCount: 5 }, 'typical');
  assert.ok(Math.abs(five.perIndexerGB - five.totalClusterGB / 5) < 1e-6,
    'per-indexer math drift');
});

// ---------------------------------------------------------------------------
// Item 8 — Palo Alto NGFW has 3 well-formed citations.
// ---------------------------------------------------------------------------
test('item 8 — PAN NGFW carries 3 well-formed citations', () => {
  const src = findSource('sec_ngfw_paloalto');
  const c = src.citations || [];
  assert.equal(c.length, 3, 'expected 3 PAN citations');
  c.forEach((x, i) => {
    assert.match(x.url, /^https?:\/\//, 'citation ' + i + ' must have an http(s) URL');
    assert.ok(typeof x.type === 'string' && x.type.length > 0,
      'citation ' + i + ' must declare a type');
    assert.match(x.accessed || '', /^\d{4}-\d{2}-\d{2}$/,
      'citation ' + i + ' must carry an ISO accessed date');
  });
});

// ---------------------------------------------------------------------------
// Item 9 — Catalogue calibration tier counts. 25 calibrated at v8.7.0
// launch (Tasks 11-35), all remaining sources tagged "pending", no other
// values present.
// ---------------------------------------------------------------------------
test('item 9 — 25 calibrated sources at v8.7.0 launch; rest are pending', () => {
  const calibrated = SOURCES.filter(s => s.calibration === 'calibrated');
  const pending    = SOURCES.filter(s => s.calibration === 'pending');
  const other      = SOURCES.filter(s => s.calibration !== 'calibrated' && s.calibration !== 'pending');
  assert.equal(calibrated.length, 25, 'expected 25 calibrated sources at v8.7.0 launch');
  assert.equal(other.length, 0, 'no other calibration tier values are permitted');
  assert.equal(calibrated.length + pending.length, SOURCES.length,
    'tier counts must partition the catalogue');
});

// ---------------------------------------------------------------------------
// Item 10 — "modbus" substring search returns proto_modbus.
// ---------------------------------------------------------------------------
test('item 10 — "modbus" substring search hits proto_modbus', () => {
  const q = 'modbus';
  const matches = SOURCES.filter(s =>
    (s.name || '').toLowerCase().includes(q) ||
    (s.id   || '').toLowerCase().includes(q) ||
    (s.subcategory || '').toLowerCase().includes(q)
  );
  assert.ok(matches.length >= 1, '"modbus" should return at least one source');
  assert.ok(matches.some(s => s.id === 'proto_modbus'),
    'proto_modbus should appear in the "modbus" search results');
});

// ---------------------------------------------------------------------------
// Item 11 — Share-URL round-trip preserves driver values and numerics.
// Drivers that equal the (profile preset or default) baseline are omitted
// from the URL so it stays short; the parser must still recover them.
// ---------------------------------------------------------------------------
test('item 11 — share-link round-trip preserves drivers + numerics', () => {
  const original = [
    {
      source: findSource('sec_ngfw_paloalto'),
      driverValues: { throughput_gbps: 2.0, log_profile: 'traffic+threat+url' }
    },
    {
      // Every driver is on the typical preset → encoder should emit just
      // the bare source ID (URL-shortening invariant).
      source: findSource('proto_modbus'),
      driverValues: { tag_count: 500, poll_interval_sec: 30, deadband_ratio: 0.4 }
    }
  ];
  const encoded = buildShareUrl(original, 'typical');
  const modbusBare = !encoded.split('|').some(p => p.startsWith('proto_modbus:'));
  assert.ok(modbusBare,
    'Modbus instance at typical-preset values should be encoded as the bare source ID; got "' + encoded + '"');

  const round = parseShareUrl(encoded);
  assert.equal(round.length, original.length, 'round-trip should preserve instance count');
  for (let i = 0; i < original.length; i++) {
    const a = runComputeForInstance(original[i], 'typical');
    const b = runComputeForInstance(round[i],    'typical');
    assert.ok(Math.abs(a.eps - b.eps) < 1e-6, 'instance ' + i + ': EPS drift in round-trip');
    assert.ok(Math.abs(a.bytesPerEvent - b.bytesPerEvent) < 1e-6,
      'instance ' + i + ': bytes/event drift in round-trip');
  }
});

// ---------------------------------------------------------------------------
// Item 12 — CSV "Drivers (k=v)" column carries effective values with
// override-falls-back-to-default precedence.
// ---------------------------------------------------------------------------
test('item 12 — CSV Drivers cell carries override + falls back to default', () => {
  const src = findSource('sec_ngfw_paloalto');
  const entry = { source: src, driverValues: { throughput_gbps: 1.5 } };  // log_profile left at default
  const profile = 'typical';

  // Port of app.js exportReport() per-source kv synthesis at line 749.
  const kv = (src.drivers || []).map(d => {
    let v;
    if (entry.driverValues && entry.driverValues[d.id] !== undefined)     v = entry.driverValues[d.id];
    else if (d.profilePresets && d.profilePresets[profile] !== undefined) v = d.profilePresets[profile];
    else                                                                  v = d.default;
    return d.id + '=' + v;
  }).join('; ');

  assert.ok(kv.includes('throughput_gbps=1.5'),
    'override should appear in CSV cell; got "' + kv + '"');
  assert.ok(kv.includes('log_profile=traffic+threat'),
    'default should appear for missing override; got "' + kv + '"');
});

// ---------------------------------------------------------------------------
// Item 13 — Release-notes overlay in index.html shows the current release
// (v8.7.1) at the top and still documents the Data Sizing tool v2 feature
// somewhere in the history (v8.7.0, now the second entry).
// ---------------------------------------------------------------------------
test('item 13 — index.html release-notes overlay shows v8.7.1 at the top', () => {
  const indexPath = path.join(__dirname, '..', '..', '..', 'index.html');
  const html = fs.readFileSync(indexPath, 'utf8');
  const open = html.indexOf('<!-- BEGIN RELEASE_NOTES -->');
  const close = html.indexOf('<!-- END RELEASE_NOTES -->');
  assert.ok(open >= 0 && close > open,
    'index.html must contain a release-notes block bracketed by the BEGIN/END comments');
  const block = html.slice(open, close);
  const firstVersion = (block.match(/rn-version-tag (?:major|minor|patch)">([0-9.]+)</) || [])[1];
  assert.equal(firstVersion, '8.7.1', 'top release-notes entry should be v8.7.1');
  // The Data Sizing tool v2 feature (v8.7.0) must remain documented in the
  // release-notes history even though it is no longer the top entry.
  assert.match(block, /Data Sizing tool v2/,
    'release-notes history should still mention the Data Sizing tool v2');
});

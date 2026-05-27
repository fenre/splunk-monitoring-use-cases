#!/usr/bin/env node
/**
 * One-shot migrator: rewrites tools/data-sizing/ot-data-sources.js from v1
 * shape (eps_per_endpoint / bytes_per_event for endpoints;
 * bytes_per_tag / default_tags / default_poll_sec / poll_presets for
 * protocols) to v2 shape (drivers / compute / uncertainty / realism /
 * citations). All migrated entries carry `calibration: "pending"`.
 *
 * Delete this file after the migration commit (Task 40 cleanup).
 */
const fs   = require('fs');
const path = require('path');
const SRC  = path.join(__dirname, '..', 'ot-data-sources.js');

// Load v1 by stripping `const ` declarations and eval'ing.
const v1Text = fs.readFileSync(SRC, 'utf8')
  .replace(/^const /gm, '');
eval(v1Text);
const v1 = OT_DATA_SOURCES;

// Uniform-driver approach: the v1 lookup tables (eps_per_endpoint,
// bytes_per_event, bytes_per_tag) become regular numeric drivers with
// `profilePresets`. The engine resolves per-profile values from the
// presets before calling the compute function. No `_v1_tables` field
// is emitted — the schema's `additionalProperties: false` rule stays
// strictly enforced and no transient-field carve-out is needed.

// Pure defaults used when a v1 source did not declare a particular table.
const DEFAULT_EPS_PER_ENDPOINT = { low: 1,   typical: 1,   high: 1 };
const DEFAULT_BYTES_PER_EVENT  = { low: 500, typical: 500, high: 500 };
const DEFAULT_BYTES_PER_TAG    = { low: 100, typical: 250, high: 500 };

function pickPreset(table, key, fallback) {
  if (!table || table[key] === undefined) return fallback;
  return table[key];
}

function migrateEndpoint(s) {
  const epsTable = s.eps_per_endpoint || DEFAULT_EPS_PER_ENDPOINT;
  const byTable  = s.bytes_per_event  || DEFAULT_BYTES_PER_EVENT;
  const epsTyp   = pickPreset(epsTable, 'typical', DEFAULT_EPS_PER_ENDPOINT.typical);
  const byTyp    = pickPreset(byTable,  'typical', DEFAULT_BYTES_PER_EVENT.typical);
  const defaultEndpoints = s.default_endpoints || 1;
  const drivers = [
    {
      id: 'endpoints',
      label: 'Number of endpoints',
      unit: 'devices',
      type: 'number',
      default: defaultEndpoints,
      min: 1, max: 100000,
      profilePresets: {
        low: Math.max(1, Math.round(defaultEndpoints * 0.5)),
        typical: defaultEndpoints,
        high: defaultEndpoints * 10
      }
    },
    {
      id: 'eps_per_endpoint',
      label: 'EPS per endpoint',
      unit: 'eps',
      type: 'number',
      default: epsTyp,
      min: 0,
      profilePresets: {
        low:     pickPreset(epsTable, 'low',     epsTyp),
        typical: epsTyp,
        high:    pickPreset(epsTable, 'high',    epsTyp)
      },
      help: 'Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs.'
    },
    {
      id: 'bytes_per_event',
      label: 'Bytes per event',
      unit: 'bytes',
      type: 'number',
      default: byTyp,
      min: 0,
      profilePresets: {
        low:     pickPreset(byTable, 'low',     byTyp),
        typical: byTyp,
        high:    pickPreset(byTable, 'high',    byTyp)
      },
      help: 'Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs.'
    }
  ];
  return {
    id: s.id, name: s.name, category: s.category, subcategory: s.subcategory,
    description: s.description, vendor_examples: s.vendor_examples,
    protocol: s.protocol, ingest_method: s.ingest_method,
    splunk_sourcetype: s.splunk_sourcetype,
    calibration: 'pending',
    drivers: drivers,
    compute: 'endpoint_legacy_v1',
    uncertainty: { low: 0.5, typical: 1.0, high: 2.0 },
    realism: {
      rawdata_compression_typical: 0.15,
      tsidx_overhead_typical:      0.35,
      filterable_fraction_typical: 0.15
    },
    citations: [],
    related_uc_ids: s.related_uc_ids || []
  };
}

function migrateProtocol(s) {
  const tagTable = s.bytes_per_tag || DEFAULT_BYTES_PER_TAG;
  const tagTyp   = pickPreset(tagTable, 'typical', DEFAULT_BYTES_PER_TAG.typical);
  const defaultTags = s.default_tags || 100;
  const drivers = [
    {
      id: 'tag_count',
      label: 'Number of tags / topics / OIDs',
      unit: 'tags',
      type: 'number',
      default: defaultTags,
      min: 1, max: 1000000,
      profilePresets: {
        low: Math.max(1, Math.round(defaultTags * 0.2)),
        typical: defaultTags,
        high: defaultTags * 10
      }
    },
    {
      id: 'poll_interval_sec',
      label: 'Polling / publish interval',
      unit: 'seconds',
      type: 'enum',
      default: s.default_poll_sec || 30,
      options: (s.poll_presets || [1, 5, 10, 30, 60, 300]).map(v => ({
        value: v,
        label: v >= 60 ? (v / 60) + ' min' : v + ' s'
      }))
    },
    {
      id: 'deadband_ratio',
      label: 'Value-change filter (deadband)',
      unit: 'fraction',
      type: 'number',
      default: 0.0,
      min: 0.0, max: 0.95,
      profilePresets: { low: 0.0, typical: 0.0, high: 0.0 },
      help: 'Fraction of polls deduplicated at the gateway when register value didn\u2019t change. Default 0 for pending sources; calibrated sources tune per protocol.'
    },
    {
      id: 'bytes_per_tag',
      label: 'Bytes per tag (per poll cycle)',
      unit: 'bytes',
      type: 'number',
      default: tagTyp,
      min: 0,
      profilePresets: {
        low:     pickPreset(tagTable, 'low',     tagTyp),
        typical: tagTyp,
        high:    pickPreset(tagTable, 'high',    tagTyp)
      },
      help: 'Mechanically ported from v1. Replace when source is calibrated. Tune if vendor data differs.'
    }
  ];
  return {
    id: s.id, name: s.name, category: s.category, subcategory: s.subcategory,
    description: s.description, vendor_examples: s.vendor_examples,
    protocol: s.protocol, ingest_method: s.ingest_method,
    splunk_sourcetype: s.splunk_sourcetype,
    calibration: 'pending',
    drivers: drivers,
    compute: 'protocol_legacy_v1',
    uncertainty: { low: 0.5, typical: 1.0, high: 2.0 },
    realism: {
      rawdata_compression_typical: 0.15,
      tsidx_overhead_typical:      0.35,
      filterable_fraction_typical: 0.15
    },
    citations: [],
    related_uc_ids: s.related_uc_ids || []
  };
}

const v2 = v1.map(s => s.source_type === 'protocol' ? migrateProtocol(s) : migrateEndpoint(s));

const out =
`/**
 * Data-Sizing v2 catalogue. See tools/data-sizing/schemas/data-source.schema.json.
 *
 * Calibration tiers:
 *   - "calibrated": vendor-cited drivers + dedicated compute function in
 *     compute-functions.js. Citations array must be non-empty (CI gate).
 *   - "pending":    mechanically ported from v1; numbers approximate.
 *                   Uses endpoint_legacy_v1 or protocol_legacy_v1 driving
 *                   ordinary numeric drivers with profilePresets, so the
 *                   v1 lookup tables flow through the standard driver
 *                   pipeline (no carve-out fields).
 */
window.OT_DATA_SOURCES = ${JSON.stringify(v2, null, 2)};

if (typeof module !== "undefined" && module.exports) {
  module.exports = global.OT_DATA_SOURCES || window.OT_DATA_SOURCES;
}
`;

fs.writeFileSync(SRC, out);
console.log('Migrated ' + v1.length + ' sources -> v2 (all calibration: pending).');

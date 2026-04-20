#!/usr/bin/env node
/**
 * Phase 3a headless smoke test.
 *
 * Stands up a minimal window/document shim, loads the real data.js
 * plus the Phase-3a-touched src/scripts/01-state.js,
 * src/scripts/02-filters.js and src/scripts/04-panel.js in the same
 * order as index.html concatenates them, then exercises the three
 * behaviours Phase 3a introduced:
 *
 *   1) __recomputeCachedFacets() populates _cachedClausesByReg with
 *      one entry per regulation that has at least one cmp row.
 *   2) currentRegulationFilter + currentClauseFilter together narrow
 *      getFilteredUCs() to the exact (reg, version, clause) subset.
 *   3) panelHTML() emits the <table class="uc-compliance-table"> block
 *      for a UC that carries a cmp array.
 *
 * The script exits 0 on success, 1 on any assertion failure, and
 * never touches the network. We deliberately stub out only the
 * globals these three scripts actually touch — full DOM rendering is
 * out of scope for a smoke test.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..", "..");

function readSrc(relPath) {
  return fs.readFileSync(path.join(ROOT, relPath), "utf8");
}

function assert(ok, msg) {
  if (!ok) {
    console.error("FAIL:", msg);
    process.exit(1);
  }
  console.log("ok   -", msg);
}

// Minimal document shim — just enough for the loaded scripts to
// evaluate without ReferenceError. We capture writes to
// ``document.getElementById('panel-body').innerHTML`` so we can
// assert on the HTML that ``fillPanelBody`` produced.
const stubElements = {
  "panel-body": { innerHTML: "" },
  "panel-id": { textContent: "" },
  "panel-title": { textContent: "" },
};
const stubDocument = {
  getElementById: (id) => stubElements[id] || null,
  querySelector: () => null,
  querySelectorAll: () => [],
  addEventListener: () => {},
  body: { classList: { add: () => {}, remove: () => {}, toggle: () => {} } },
  documentElement: { classList: { add: () => {}, remove: () => {} } },
  createElement: () => ({
    style: {},
    classList: { add: () => {}, remove: () => {}, contains: () => false },
    appendChild: () => {},
    setAttribute: () => {},
  }),
  createEvent: () => ({ initEvent: () => {} }),
};

const sandbox = {
  console,
  Date,
  JSON,
  Math,
  Promise,
  Set,
  Map,
  Error,
  setTimeout,
  clearTimeout,
  setInterval,
  clearInterval,
  URL,
  encodeURIComponent,
  decodeURIComponent,
  // Scripts occasionally probe localStorage — fail-open is fine for
  // this smoke test; the scripts already wrap those reads in try/catch.
  localStorage: {
    getItem: () => null,
    setItem: () => {},
    removeItem: () => {},
    clear: () => {},
  },
  document: stubDocument,
  addEventListener: () => {},
  dispatchEvent: () => {},
  CustomEvent: function () {},
  Event: function () {},
  location: { hash: "", pathname: "/", search: "", href: "http://localhost/" },
  history: { replaceState: () => {}, pushState: () => {} },
  navigator: { userAgent: "phase3a-smoke" },
  // Globals the smoke does NOT need (provenance/custom-text) but that
  // 02-filters.js defensively reads — ship empty defaults so the
  // guarded reads evaluate to falsy without throwing.
  UC_CUSTOM_TEXT: {},
  UC_PROVENANCE: {},
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;

vm.createContext(sandbox);

// Load data.js first (window.DATA, window.EQUIPMENT, …), then the
// five script chunks in bundle order. We skip chunks that pull in
// non-trivial DOM APIs we haven't stubbed — for Phase 3a only the
// state/filters/panel chunks matter.
const scripts = [
  "data.js",
  "src/scripts/01-state.js",
  "src/scripts/02-filters.js",
  "src/scripts/04-panel.js",
];

for (const rel of scripts) {
  const src = readSrc(rel);
  try {
    vm.runInContext(src, sandbox, { filename: rel });
  } catch (err) {
    console.error("Failed to load " + rel + ":", err.message);
    // Some scripts may reference functions defined in chunks we
    // skipped (e.g. esc/stripMd live in 01-state.js, called by
    // 04-panel.js at eval time — they shouldn't, everything is in
    // function bodies — but if any top-level throw slips through,
    // fail loud rather than silently masking a regression.
    process.exit(1);
  }
  // data.js ships ``const DATA = [...]``. Classic-script ``const``
  // bindings create a Script Record entry, NOT a property on the
  // global object — so ``window.DATA`` stays undefined even though
  // the bare identifier ``DATA`` is visible to the next script.
  // 01-state.js's bootstrap reads ``window.DATA``, which works in
  // production because the 00-loader.js lazy path copies the parsed
  // catalog onto ``window.DATA = cats``. In this VM harness we skip
  // the loader, so bridge the bare ``DATA`` binding onto
  // ``window.DATA`` ourselves immediately after data.js loads.
  if (rel === "data.js") {
    try {
      vm.runInContext(
        "if (typeof DATA !== 'undefined' && !Array.isArray(window.DATA)) { window.DATA = DATA; }",
        sandbox,
        { filename: "_phase3a_smoke.bridge" },
      );
    } catch (err) {
      console.error("Failed to bridge DATA → window.DATA:", err.message);
      process.exit(1);
    }
  }
}

// __bootstrapCatalogState runs inside 00-loader in production. We
// didn't load 00-loader (it async-awaits fetch), so call the
// bootstrap directly — window.DATA is already populated by data.js.
assert(
  typeof sandbox.__bootstrapCatalogState === "function",
  "01-state.js exports __bootstrapCatalogState()",
);
sandbox.__bootstrapCatalogState();

// Debug: quickly inspect how many cmp rows the bootstrap actually saw.
let totalUCs = 0;
let withCmp = 0;
(sandbox.DATA || []).forEach((cat) => {
  (cat.s || []).forEach((sc) => {
    (sc.u || []).forEach((uc) => {
      totalUCs++;
      if (Array.isArray(uc.cmp) && uc.cmp.length > 0) withCmp++;
    });
  });
});
console.log("debug: totalUCs=" + totalUCs + " withCmp=" + withCmp);

// ---------------------------------------------------------------
// Assertion 1 — cached clause facets
// ---------------------------------------------------------------
const clausesByReg = sandbox._cachedClausesByReg || {};
const regKeys = Object.keys(clausesByReg);
assert(
  regKeys.length > 0,
  "_cachedClausesByReg has at least one regulation",
);
assert(
  regKeys.length >= 10,
  "expect >=10 regulations with clause-level cmp data (got " + regKeys.length + ")",
);

// Canonical form should be "{version}#{clause}". A single version
// should only appear once per clause.
const pickOne = regKeys[0];
const sample = clausesByReg[pickOne];
assert(
  Array.isArray(sample) && sample.length > 0,
  "clauses[" + pickOne + "] is a non-empty array",
);
assert(
  sample.every((s) => typeof s === "string" && s.includes("#")),
  "every clause option is canonical {version}#{clause} form",
);

// ---------------------------------------------------------------
// Assertion 2 — reg + clause filter narrows results
// ---------------------------------------------------------------
// Pick GDPR Art.5 if available (most authoritative test fixture);
// otherwise fall back to the first reg with >=2 UCs under a single
// clause so we can prove the filter is actually cutting results.
function candidatePairs() {
  const out = [];
  for (const reg of regKeys) {
    for (const canonical of clausesByReg[reg]) {
      out.push([reg, canonical]);
    }
  }
  return out;
}

let testReg = null;
let testClause = null;
const allPairs = candidatePairs();
for (const [reg, clause] of allPairs) {
  if (reg.toUpperCase().includes("GDPR") && clause.toUpperCase().includes("ART.5")) {
    testReg = reg;
    testClause = clause;
    break;
  }
}
if (!testReg) {
  testReg = allPairs[0][0];
  testClause = allPairs[0][1];
}

// Baseline — reg only.
sandbox.currentRegulationFilter = testReg;
sandbox.currentClauseFilter = "all";
const regOnly = sandbox.getFilteredUCs();
assert(regOnly.length > 0, "regulation-only filter returns non-empty set");

// Narrowed — reg + clause.
sandbox.currentClauseFilter = testClause;
const narrowed = sandbox.getFilteredUCs();
assert(
  narrowed.length > 0 && narrowed.length <= regOnly.length,
  "clause filter narrows to <= regulation-only count (reg=" +
    regOnly.length + " narrowed=" + narrowed.length + ")",
);

// Every narrowed UC must carry a cmp row matching (reg, version, clause).
const hashIdx = testClause.indexOf("#");
const wantVer = testClause.slice(0, hashIdx);
const wantCl = testClause.slice(hashIdx + 1);
const mismatch = narrowed.find((e) => {
  const cmp = Array.isArray(e.uc.cmp) ? e.uc.cmp : [];
  return !cmp.some((r) => r && r.r === testReg && r.v === wantVer && r.cl === wantCl);
});
assert(
  !mismatch,
  "every narrowed UC has a matching cmp row for " + testReg + " / " + testClause,
);

// ---------------------------------------------------------------
// Assertion 3 — fillPanelBody renders the clause table
// ---------------------------------------------------------------
// fillPanelBody writes into document.getElementById('panel-body').
// innerHTML. We stub panel-body up front and inspect the string
// after the function returns. Pick a narrowed entry that does NOT
// have ``uc.z`` (visualization) so we don't need to stub
// ntVizMockups from 03-render.js.
assert(
  typeof sandbox.fillPanelBody === "function",
  "04-panel.js exports fillPanelBody()",
);
const renderEntry = narrowed.find((e) => !e.uc.z) || narrowed[0];
sandbox.fillPanelBody(renderEntry);
const renderedHtml = stubElements["panel-body"].innerHTML;
assert(
  typeof renderedHtml === "string" && renderedHtml.length > 0,
  "fillPanelBody() populates panel-body innerHTML",
);
assert(
  renderedHtml.includes("uc-compliance-table"),
  "panel HTML includes the uc-compliance-table block",
);
assert(
  renderedHtml.includes("Compliance clauses"),
  "panel HTML includes the 'Compliance clauses' heading",
);
assert(
  renderedHtml.includes("filterByClauseEnc("),
  "panel HTML wires clause-filter buttons via filterByClauseEnc",
);
// Cross-check: the escape function would turn section markers into
// entities, so search for the regulation name raw or entity-escaped.
const regNameEscaped = testReg.replace(/[&<>"']/g, function (c) {
  return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
});
assert(
  renderedHtml.includes(regNameEscaped) || renderedHtml.includes(testReg),
  "panel HTML includes the selected regulation name (" + testReg + ")",
);

console.log("\nAll Phase 3a smoke assertions passed.");
process.exit(0);

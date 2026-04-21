#!/usr/bin/env node
/**
 * Phase 3c headless smoke test for compliance-story.html.
 *
 * Drives a stubbed browser through both modes of the new buyer page:
 *
 *   1) Landing view (no ?reg=) — ensures the tile catalogue is
 *      rendered from api/v1/compliance/story/index.json.
 *   2) Detail view (?reg=gdpr) — ensures the hero, narrative cards,
 *      coverage ring, top-5 highlights, gaps (or empty-state), and
 *      quick-start playbook render from the per-regulation payload.
 *
 * The fixture server is started and stopped by this script so the
 * smoke runs with ``node tools/audits/_phase3c_smoke.js`` and nothing
 * else — exactly like _phase3a_smoke.js and _phase3b_smoke.js.
 *
 * The IIFE is loaded twice in this script: once per mode. Because the
 * VM contexts are independent, each run can spoof its own ``location``
 * search string without the two interfering.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");
const http = require("http");

const ROOT = path.resolve(__dirname, "..", "..");
const HTML_PATH = path.join(ROOT, "compliance-story.html");

// ------------------------------------------------------------
// Tiny fixture server (ephemeral port). Same shape as phase 3b.
// ------------------------------------------------------------
const server = http.createServer((req, res) => {
  try {
    const url = decodeURIComponent(req.url.split("?")[0]);
    const filePath = path.join(ROOT, url.replace(/^\//, ""));
    if (!filePath.startsWith(ROOT)) {
      res.writeHead(403);
      res.end("Forbidden");
      return;
    }
    const data = fs.readFileSync(filePath);
    const ext = path.extname(filePath).toLowerCase();
    const ctype = ext === ".json" ? "application/json" :
                  ext === ".html" ? "text/html" : "application/octet-stream";
    res.writeHead(200, { "Content-Type": ctype });
    res.end(data);
  } catch (err) {
    res.writeHead(404);
    res.end("Not found: " + err.message);
  }
});

function cleanup() {
  try { server.close(); } catch (_) { /* ignore */ }
}

let tests = 0;
let fails = 0;
function assert(ok, msg) {
  tests++;
  if (!ok) {
    fails++;
    console.error("FAIL:", msg);
    return false;
  }
  console.log("ok   -", msg);
  return true;
}

function readScript() {
  const html = fs.readFileSync(HTML_PATH, "utf8");
  const lastOpen = html.lastIndexOf("<script>");
  const lastClose = html.lastIndexOf("</script>");
  if (lastOpen === -1 || lastClose === -1 || lastClose <= lastOpen) {
    throw new Error("compliance-story.html missing inline <script>");
  }
  return html.slice(lastOpen + "<script>".length, lastClose);
}

// ------------------------------------------------------------
// Build a fresh sandbox per run — we want totally independent
// element stores, listener maps, and ``location.search`` values.
// ------------------------------------------------------------
function buildSandbox(base, search) {
  const elements = Object.create(null);
  const listeners = Object.create(null);

  function makeEl(id, tag) {
    const el = {
      id: id, tagName: (tag || "DIV").toUpperCase(),
      innerHTML: "", textContent: "", value: "",
      disabled: false, hidden: false, style: {},
      attributes: Object.create(null),
      classList: {
        _set: new Set(),
        add(c) { this._set.add(c); },
        remove(c) { this._set.delete(c); },
        contains(c) { return this._set.has(c); },
      },
      setAttribute(name, val) { this.attributes[name] = val; },
      getAttribute(name) { return this.attributes[name] != null ? this.attributes[name] : null; },
      removeAttribute(name) { delete this.attributes[name]; },
      addEventListener(evt, fn) {
        if (!listeners[id]) listeners[id] = {};
        if (!listeners[id][evt]) listeners[id][evt] = [];
        listeners[id][evt].push(fn);
      },
      dispatchEvent() {},
      // ``forEach`` iteration happens on NodeList in the real page —
      // but the IIFE only forEach-es over an already-collected NodeList
      // from querySelectorAll. We hand a plain array to that, so this
      // stub never gets forEach'd itself.
      querySelector() { return null; },
      querySelectorAll() { return []; },
      closest() { return null; },
      scrollIntoView() {},
      click() {},
      remove() {},
    };
    return el;
  }

  // All ids the IIFE touches, across both modes. The theme toggle
  // uses the shared chrome ids (theme-btn / theme-label / theme-ico)
  // wired in src/styles/06-chrome.css; the brand subtitle is updated
  // dynamically via cs-brand-sub when a story loads.
  [
    "theme-btn", "theme-label", "theme-ico", "cs-brand-sub",
    "cs-content",
    // landing filters
    "cs-filter-search", "cs-filter-tier", "cs-cards-root",
  ].forEach((id) => { elements[id] = makeEl(id); });

  // The landing-mode filters use ``document.querySelectorAll("#cs-cards-root .cs-card")``
  // and then ``.forEach(card => { ... })``. The stub returns an empty
  // list — which is fine because these assertions only check that the
  // *initial* render happened; filter reactivity is covered by the
  // separate Phase 3a tests on the main catalogue.
  function querySelectorAll() { return []; }

  const documentStub = {
    getElementById(id) {
      if (!elements[id]) elements[id] = makeEl(id);
      return elements[id];
    },
    querySelector() { return null; },
    querySelectorAll: querySelectorAll,
    addEventListener(evt, fn) {
      if (evt === "DOMContentLoaded") {
        Promise.resolve().then(fn);
      }
    },
    createElement(tag) { return makeEl("_" + Math.random().toString(36).slice(2), tag); },
    body: { appendChild() {} },
    documentElement: {
      classList: {
        _set: new Set(),
        add(c) { this._set.add(c); },
        remove(c) { this._set.delete(c); },
        contains(c) { return this._set.has(c); },
      },
    },
  };

  const localStorageStub = {
    _store: {},
    getItem(k) { return this._store[k] == null ? null : this._store[k]; },
    setItem(k, v) { this._store[k] = String(v); },
    removeItem(k) { delete this._store[k]; },
    clear() { this._store = {}; },
  };

  const locationStub = {
    hash: "",
    href: base + "/compliance-story.html" + (search || ""),
    search: search || "",
  };

  const sandbox = {
    console,
    Date, Math, JSON, Error, Promise,
    Set, Map, Array, RegExp, Number, String, Boolean, Object,
    setTimeout, clearTimeout,
    setInterval, clearInterval,
    encodeURIComponent, decodeURIComponent,
    fetch: (url, init) => {
      const u = /^https?:/.test(url) ? url : base + "/" + url.replace(/^\//, "");
      return fetch(u, init);
    },
    document: documentStub,
    window: null,
    localStorage: localStorageStub,
    matchMedia: () => ({ matches: false }),
    location: locationStub,
  };
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);

  return { sandbox, elements, listeners };
}

function waitForCondition(checkFn, timeoutMs) {
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + timeoutMs;
    (function poll() {
      let value;
      try { value = checkFn(); } catch (_) { value = null; }
      if (value) { resolve(value); return; }
      if (Date.now() > deadline) { reject(new Error("timeout")); return; }
      setTimeout(poll, 60);
    })();
  });
}

function runScript(sandbox, src) {
  vm.runInContext(src, sandbox, { filename: "compliance-story.inline.js" });
}

// ------------------------------------------------------------
// Test runs
// ------------------------------------------------------------
async function runLandingMode(base, src) {
  console.log("\n--- landing mode (no ?reg=) ---");
  const { sandbox, elements } = buildSandbox(base, "");
  runScript(sandbox, src);

  try {
    await waitForCondition(() => {
      const html = elements["cs-content"].innerHTML || "";
      return html.indexOf("cs-cards") !== -1 ? html : null;
    }, 10000);
  } catch (_) {
    assert(false, "landing view rendered within 10s");
    return;
  }

  const html = elements["cs-content"].innerHTML;
  assert(html.indexOf("Every regulation we tell a story about") !== -1,
    "landing view includes the intro heading");
  assert(html.indexOf("cs-filter-search") !== -1,
    "landing view wires up the search filter input");
  assert(html.indexOf("cs-filter-tier") !== -1,
    "landing view wires up the tier filter select");
  // Tile count: parse cards and ensure at least one tier-1 tile exists.
  const cardMatches = html.match(/class="cs-card"/g) || [];
  assert(cardMatches.length > 20, "landing view renders many regulation cards (got " + cardMatches.length + ")");
  assert(html.indexOf("GDPR") !== -1, "landing view mentions GDPR among the cards");
  assert(html.indexOf('class="cs-pill tier-1">Tier 1</span>') !== -1,
    "at least one tier-1 card pill is rendered");
  assert(/compliance-story\.html\?reg=[a-zA-Z0-9_-]+/.test(html),
    "cards link to per-regulation detail pages");
}

async function runDetailMode(base, src, regId) {
  console.log("\n--- detail mode (?reg=" + regId + ") ---");
  const { sandbox, elements } = buildSandbox(base, "?reg=" + regId);
  runScript(sandbox, src);

  try {
    await waitForCondition(() => {
      const html = elements["cs-content"].innerHTML || "";
      return html.indexOf("cs-hero") !== -1 ? html : null;
    }, 10000);
  } catch (_) {
    assert(false, "detail view rendered within 10s for reg=" + regId);
    return;
  }

  const html = elements["cs-content"].innerHTML;

  // ---- back link ------------------------------------------------------
  assert(html.indexOf('href="compliance-story.html"') !== -1,
    "detail view has a back link to the landing view");

  // ---- hero -----------------------------------------------------------
  assert(html.indexOf("cs-hero-headline") !== -1 || html.indexOf("cs-hero-sub") !== -1,
    "detail view renders the hero block");
  assert(html.indexOf("Tier") !== -1, "detail view surfaces the tier badge");

  // ---- narrative (what/who/splunk-value) -----------------------------
  assert(html.indexOf("cs-narrative-card") !== -1,
    "detail view renders the narrative (what / who / so-what) cards");
  // At least one of the canonical headings should appear for a
  // tier-1 regulation with a full primer entry.
  const narrativeHeadings = ["What the law is", "Who it affects", "How Splunk helps"];
  const seen = narrativeHeadings.filter((h) => html.indexOf(h) !== -1);
  assert(seen.length >= 2, "detail view has at least two narrative cards (got " + seen.length + "): " + seen.join(", "));

  // ---- coverage ring + legend ----------------------------------------
  assert(html.indexOf("cs-coverage-panel") !== -1,
    "detail view renders the coverage panel");
  assert(html.indexOf("cs-ring") !== -1,
    "coverage panel includes the ring visual");
  assert(html.indexOf("cs-legend-item") !== -1,
    "coverage panel includes a legend");
  assert(/--pct-full:\s*[\d.]+%/.test(html),
    "coverage ring receives a computed --pct-full CSS variable");

  // ---- highlights -----------------------------------------------------
  // GDPR's payload has five full-coverage highlights — assert at least one.
  const highlightCount = (html.match(/class="cs-highlight-card"/g) || []).length;
  assert(highlightCount >= 1,
    "detail view renders at least one highlight card (got " + highlightCount + ")");
  assert(html.indexOf("cs-killer-uc") !== -1,
    "highlight cards link to their killer UC");

  // ---- gaps (may be empty for covered-in-full regs like GDPR) --------
  const hasGaps = html.indexOf('class="cs-gap-card"') !== -1;
  const hasEmpty = html.indexOf("cs-empty-gaps") !== -1;
  assert(hasGaps || hasEmpty,
    "detail view either renders gap cards or an 'no gaps' empty state");

  // ---- playbook -------------------------------------------------------
  assert(html.indexOf("cs-playbook") !== -1,
    "detail view renders the implementer playbook section");
  assert(html.indexOf("<details>") !== -1 || html.indexOf("<details ") !== -1,
    "playbook entries use <details> for collapsible rows");
  assert(html.indexOf("cs-playbook-uc-link") !== -1,
    "playbook entries link through to specific UCs");

  // ---- related resources ---------------------------------------------
  assert(html.indexOf("cs-related") !== -1,
    "detail view renders the related-resources section");
  assert(html.indexOf("Clause navigator") !== -1,
    "related resources link to the clause navigator");
  assert(html.indexOf("Filter the catalogue") !== -1,
    "related resources link back into the filtered catalogue");
}

async function runBadRegIdMode(base, src) {
  console.log("\n--- detail mode (malformed ?reg=) ---");
  // Use a disallowed char (space) to exercise the validation branch.
  const { sandbox, elements } = buildSandbox(base, "?reg=not%20valid");
  runScript(sandbox, src);

  try {
    await waitForCondition(() => {
      const html = elements["cs-content"].innerHTML || "";
      return html.indexOf("cs-error") !== -1 ? html : null;
    }, 4000);
  } catch (_) {
    assert(false, "malformed ?reg= produces an error panel within 4s");
    return;
  }
  const html = elements["cs-content"].innerHTML;
  assert(html.indexOf("Invalid regulation id") !== -1,
    "malformed ?reg= displays 'Invalid regulation id' error");
}

async function runMissingRegMode(base, src) {
  console.log("\n--- detail mode (unknown but valid-shape ?reg=) ---");
  const { sandbox, elements } = buildSandbox(base, "?reg=does-not-exist");
  runScript(sandbox, src);

  try {
    await waitForCondition(() => {
      const html = elements["cs-content"].innerHTML || "";
      return html.indexOf("cs-error") !== -1 ? html : null;
    }, 6000);
  } catch (_) {
    assert(false, "unknown ?reg= produces an error panel within 6s");
    return;
  }
  const html = elements["cs-content"].innerHTML;
  assert(html.indexOf("Could not load compliance story") !== -1,
    "unknown ?reg= displays 'Could not load' error");
}

// ------------------------------------------------------------
// Orchestrator
// ------------------------------------------------------------
server.listen(0, "127.0.0.1", async () => {
  const port = server.address().port;
  const base = "http://127.0.0.1:" + port;
  const src = readScript();

  try {
    await runLandingMode(base, src);
    await runDetailMode(base, src, "gdpr");
    await runBadRegIdMode(base, src);
    await runMissingRegMode(base, src);

    console.log("\n" + tests + " tests, " + fails + " failed.");
    if (fails > 0) {
      cleanup();
      process.exit(1);
    }
    console.log("All Phase 3c smoke assertions passed.");
    cleanup();
    process.exit(0);
  } catch (err) {
    console.error("Harness crashed:", err && err.stack ? err.stack : err);
    cleanup();
    process.exit(1);
  }
});

setTimeout(() => {
  console.error("FAIL: global timeout");
  cleanup();
  process.exit(1);
}, 30000).unref();

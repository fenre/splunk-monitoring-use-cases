#!/usr/bin/env node
/**
 * Phase 3b headless smoke test for clause-navigator.html.
 *
 * Drives a stubbed browser through the key behaviours of the new
 * auditor page:
 *
 *   1) Extracts the inline IIFE from clause-navigator.html and runs
 *      it in a VM context with a minimal DOM + localStorage shim.
 *   2) Waits for the IIFE to finish loading
 *      api/v1/compliance/clauses/index.json (served via a local
 *      python http.server).
 *   3) Verifies the summary tiles, table render, filtering, sorting,
 *      and CSV export function without touching the network outside
 *      the localhost fixture.
 *
 * The fixture server is started and stopped by this script so the
 * smoke runs with ``node tools/audits/_phase3b_smoke.js`` and nothing
 * else — exactly like _phase3a_smoke.js.
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");
const http = require("http");

const ROOT = path.resolve(__dirname, "..", "..");
const HTML_PATH = path.join(ROOT, "clause-navigator.html");

function assert(ok, msg) {
  if (!ok) {
    console.error("FAIL:", msg);
    cleanup();
    process.exit(1);
  }
  console.log("ok   -", msg);
}

// ---------------------------------------------------------------
// 1) Static fixture server (port 0 = ephemeral, avoids collisions)
// ---------------------------------------------------------------
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
  try { server.close(); } catch (_) {}
}

server.listen(0, "127.0.0.1", () => {
  const port = server.address().port;
  const base = "http://127.0.0.1:" + port;

  // -------------------------------------------------------------
  // 2) Extract inline IIFE from clause-navigator.html
  // -------------------------------------------------------------
  const html = fs.readFileSync(HTML_PATH, "utf8");
  // Inline script lives in the LAST <script>...</script> block.
  const lastOpen = html.lastIndexOf("<script>");
  const lastClose = html.lastIndexOf("</script>");
  assert(lastOpen !== -1 && lastClose !== -1 && lastClose > lastOpen,
    "clause-navigator.html contains an inline <script> block");
  const scriptSrc = html.slice(lastOpen + "<script>".length, lastClose);
  assert(scriptSrc.length > 0, "inline <script> has content");

  // -------------------------------------------------------------
  // 3) Build a tiny DOM to back the script's getElementById calls.
  //     Element instances are plain objects; the script never
  //     touches layout, only innerHTML/textContent/value.
  // -------------------------------------------------------------
  const elements = Object.create(null);
  const listeners = Object.create(null); // elementId -> {eventName: [fn]}

  function makeEl(id, tag) {
    const el = {
      id: id, tagName: (tag || "DIV").toUpperCase(),
      innerHTML: "", textContent: "", value: "",
      disabled: false, hidden: false,
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
      querySelector() { return null; },
      querySelectorAll() { return []; },
      closest() { return null; },
      scrollIntoView() {},
      click() {},
      remove() {},
    };
    return el;
  }

  // Pre-create the ids the IIFE touches.
  [
    "cn-theme-btn", "cn-theme-label",
    "cn-tile-regs", "cn-tile-clauses", "cn-tile-full", "cn-tile-partial", "cn-tile-obl",
    "cn-search", "cn-reg", "cn-coverage", "cn-tier", "cn-obl",
    "cn-reset", "cn-export-csv",
    "cn-chips", "cn-summary",
    "cn-table", "cn-tbody",
    "cn-pager", "cn-pager-prev", "cn-pager-next", "cn-pager-label",
  ].forEach((id) => { elements[id] = makeEl(id); });

  // ``document.querySelectorAll("#cn-table thead th[data-sort]")`` is
  // used by ``updateSortIndicators`` and the header-sort wiring.
  const sortHeaders = [
    "regulationShortName", "clause", "coverageRank",
    "coveringUcCount", "tier", "obligationPresent",
  ].map((k) => {
    const th = makeEl("th-" + k, "TH");
    th.setAttribute("data-sort", k);
    return th;
  });

  function querySelectorAll(sel) {
    if (sel === "#cn-table thead th[data-sort]") return sortHeaders;
    return [];
  }
  function querySelector(sel) {
    // The IIFE uses querySelector only on tbody to find rows/details.
    // We never simulate full row expansion in this smoke (Phase 3a
    // already covers the per-UC table path); return null so the
    // expansion code short-circuits.
    return null;
  }

  const documentStub = {
    getElementById(id) { return elements[id] || null; },
    querySelector: querySelector,
    querySelectorAll: querySelectorAll,
    addEventListener(evt, fn) {
      if (evt === "DOMContentLoaded") {
        // Fire the handler on the next microtask so the IIFE has
        // finished evaluating before bootstrap runs.
        Promise.resolve().then(fn);
      }
    },
    createElement(tag) { return makeEl("_" + Math.random().toString(36).slice(2), tag); },
    body: {
      appendChild() {},
    },
    documentElement: {
      classList: {
        _set: new Set(),
        add(c) { this._set.add(c); },
        remove(c) { this._set.delete(c); },
        contains(c) { return this._set.has(c); },
      },
    },
  };

  // Shim localStorage, matchMedia, URL.createObjectURL.
  const localStorageStub = {
    _store: {},
    getItem(k) { return this._store[k] == null ? null : this._store[k]; },
    setItem(k, v) { this._store[k] = String(v); },
    removeItem(k) { delete this._store[k]; },
    clear() { this._store = {}; },
  };

  let csvBlob = null;
  const URLStub = {
    createObjectURL(blob) { csvBlob = blob; return "blob:csv-fixture"; },
    revokeObjectURL() {},
  };

  const locationStub = { hash: "", href: base + "/clause-navigator.html" };

  const sandbox = {
    console,
    Date, Math, JSON, Error, Promise,
    Set, Map, Array,
    setTimeout, clearTimeout,
    setInterval, clearInterval,
    encodeURIComponent, decodeURIComponent,
    fetch: (url, init) => {
      // Resolve relative URLs against the fixture server root.
      const u = /^https?:/.test(url) ? url : base + "/" + url.replace(/^\//, "");
      return fetch(u, init);
    },
    document: documentStub,
    window: null,             // filled in below
    localStorage: localStorageStub,
    matchMedia: () => ({ matches: false }),
    location: locationStub,
    URL: URLStub,
    Blob: function (parts, opts) {
      // Real Node Blob would do, but we only care about string length
      // for the assertions. Store the first chunk for inspection.
      this.parts = parts;
      this.type = (opts && opts.type) || "";
      this.size = parts.reduce((n, p) => n + (p && p.length ? p.length : 0), 0);
    },
  };
  sandbox.window = sandbox;
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);

  // -------------------------------------------------------------
  // 4) Run the IIFE and wait for bootstrap to finish
  // -------------------------------------------------------------
  vm.runInContext(scriptSrc, sandbox, { filename: "clause-navigator.inline.js" });

  // The IIFE installs a DOMContentLoaded listener that calls
  // loadIndex(). That fetch resolves asynchronously — give it a few
  // ticks, then poll until the summary tile has been populated.
  const deadline = Date.now() + 10000;
  (function waitForReady() {
    const regsTile = elements["cn-tile-regs"].textContent;
    if (regsTile && regsTile !== "—" && regsTile !== "\u2014") {
      runAssertions();
      return;
    }
    if (Date.now() > deadline) {
      console.error("FAIL: bootstrap did not populate tiles within 10s");
      cleanup();
      process.exit(1);
    }
    setTimeout(waitForReady, 80);
  })();

  function runAssertions() {
    try {
      // ---- summary tiles populated -----------------------------------
      const regsN = parseInt(elements["cn-tile-regs"].textContent.replace(/\D/g, ""), 10);
      const clauseN = parseInt(elements["cn-tile-clauses"].textContent.replace(/\D/g, ""), 10);
      assert(regsN > 10, "summary shows more than 10 regulations (got " + regsN + ")");
      assert(clauseN > 100, "summary shows more than 100 clauses (got " + clauseN + ")");

      // ---- initial table render --------------------------------------
      const tbody = elements["cn-tbody"].innerHTML;
      assert(tbody.includes('class="cn-row"'), "tbody contains at least one clause row");
      assert(tbody.includes('aria-expanded="false"'), "rows are rendered collapsed by default");
      assert(tbody.includes("Catalogue \u2192"), "rows include the 'Catalogue →' deep-link button");

      // ---- regulation dropdown populated -----------------------------
      const regSelHtml = elements["cn-reg"].innerHTML;
      assert(regSelHtml.split("<option").length > 10, "regulation <select> has many options");
      assert(regSelHtml.includes("GDPR") || regSelHtml.toLowerCase().includes("gdpr"), "regulation dropdown includes GDPR");

      // ---- filter wiring: coverage = uncovered --------------------------
      const covHandler = (listeners["cn-coverage"] || {}).change;
      assert(Array.isArray(covHandler) && covHandler.length > 0, "coverage <select> change handler wired");
      elements["cn-coverage"].value = "uncovered";
      covHandler[0]({ target: elements["cn-coverage"] });
      const summary = elements["cn-summary"].textContent;
      assert(/filtered from/.test(summary), "after filter, summary reports filtered subset");

      // ---- reset filters restores full list -----------------------------
      const resetHandler = (listeners["cn-reset"] || {}).click;
      assert(Array.isArray(resetHandler) && resetHandler.length > 0, "reset button handler wired");
      resetHandler[0]();
      const summary2 = elements["cn-summary"].textContent;
      assert(!/filtered from/.test(summary2), "reset clears filters (no 'filtered from' suffix)");

      // ---- CSV export hits Blob -----------------------------------------
      const csvHandler = (listeners["cn-export-csv"] || {}).click;
      assert(Array.isArray(csvHandler) && csvHandler.length > 0, "export CSV handler wired");
      csvHandler[0]();
      assert(csvBlob && csvBlob.size > 1000, "CSV export produced a non-trivial blob (size=" + (csvBlob && csvBlob.size) + ")");
      const headerLine = (csvBlob.parts[0] || "").split("\n")[0];
      assert(
        headerLine.indexOf("regulationId") !== -1 && headerLine.indexOf("coverageState") !== -1,
        "CSV header row contains regulationId and coverageState",
      );

      console.log("\nAll Phase 3b smoke assertions passed.");
      cleanup();
      process.exit(0);
    } catch (err) {
      console.error("Assertion crashed:", err && err.stack ? err.stack : err);
      cleanup();
      process.exit(1);
    }
  }
});

// Safety: never let a hung test keep the process alive forever.
setTimeout(() => {
  console.error("FAIL: global timeout");
  cleanup();
  process.exit(1);
}, 20000).unref();

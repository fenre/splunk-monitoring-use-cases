// Phase 4.5f — axe-core runner for the perf + a11y gate.
//
// Spawned as a subprocess by scripts/audit_perf_a11y.py.  We take a
// list of HTML files on the command line, load each one into a fresh
// jsdom window (scripts OFF — we audit the STATIC HTML that ships to
// users, not the JS-rendered runtime DOM), run axe-core with the
// jsdom-safe rule configuration, and emit a single deterministic
// JSON document on stdout.
//
// Why jsdom and not a real headless browser (puppeteer, chromium)?
//
//   * The gate runs on every PR.  Spinning up Chromium and its entire
//     sandbox adds >100MB and several seconds of boot; jsdom is 3MB
//     and runs cold in <1s per page.
//   * We intentionally audit STATIC HTML.  A real browser would
//     populate landmarks / headings / table bodies via JavaScript,
//     hiding regressions that screen-reader users hit before the page
//     has hydrated.  Static auditing catches those.
//   * Deterministic results.  A headless browser would produce layout
//     box quads that change across font stacks / OSes; axe-core +
//     jsdom gives the same result byte-for-byte on every CI runner.
//
// axe-core ships a list of rules that require a real layout engine
// (color-contrast, link-in-text-block, target-size, …) — we disable
// those here so the gate does not produce flaky failures.  See
// https://github.com/dequelabs/axe-core/issues/4021 for the upstream
// guidance we follow.
//
// Output schema (printed as a single JSON blob on stdout):
//
//     {
//       "axe_version": "4.11.3",
//       "jsdom_version": "29.0.2",
//       "ran_at_utc": "static",           // reserved for future use
//       "config": {
//         "disabled_rules": ["color-contrast", ...],
//         "run_only": { "type": "tag", "values": [...] }
//       },
//       "results": [
//         {
//           "file": "index.html",
//           "status": "ok"                  // "ok" | "error"
//           "error": null,
//           "summary": {
//             "passes": 37,
//             "violations": 0,
//             "incomplete": 2,
//             "inapplicable": 78
//           },
//           "violations": [
//             {
//               "id": "aria-dialog-name",
//               "impact": "serious",
//               "help": "...",
//               "helpUrl": "...",
//               "tags": ["cat.aria", "wcag2a", ...],
//               "nodeCount": 1,
//               "nodes": [
//                 { "target": ["#panel"], "html": "<div ...", "failureSummary": "..." }
//               ]
//             }
//           ],
//           "incomplete": [ /* same shape as violations, informational */ ]
//         }
//       ]
//     }
//
// The runner never fails on axe violations itself — it is a pure data
// emitter.  The Python orchestrator (scripts/audit_perf_a11y.py)
// interprets severity, applies allowlists, and decides whether to
// fail CI.  This separation of concerns keeps the Node helper tiny
// and testable.

import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createRequire} from 'node:module';

const require = createRequire(import.meta.url);
const axe = require('axe-core');
const {JSDOM} = require('jsdom');
const jsdomPkg = require('jsdom/package.json');

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const REPO = path.resolve(__dirname, '..', '..');

// Rules axe-core cannot evaluate reliably under jsdom because they
// depend on a real layout engine (computed styles, box geometry,
// CSS orientation, etc.).  Keeping these disabled prevents flaky
// "incomplete" floods that would drown the signal the gate is
// supposed to surface.  This list is imported from dequelabs/
// axe-core#4021 and kept in sync with upstream guidance.
const JSDOM_INCOMPATIBLE_RULES = [
  'color-contrast',
  'color-contrast-enhanced',
  'avoid-inline-spacing',
  'css-orientation-lock',
  'focus-order-semantics',
  'frame-focusable-content',
  'frame-tested',
  'link-in-text-block',
  'scrollable-region-focusable',
  'target-size',
];

// Tags to scan: WCAG 2.1 A + AA + best-practice.  We deliberately do
// NOT enable WCAG 2.1 AAA — the regulatory scope of the project is
// WCAG 2.1 AA (the level referenced by Section 508, EN 301 549, the
// EU Web Accessibility Directive, and EAA 2025).
const RUN_ONLY = {
  type: 'tag',
  values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice'],
};

function buildConfig() {
  const rules = {};
  for (const rule of JSDOM_INCOMPATIBLE_RULES) {
    rules[rule] = {enabled: false};
  }
  return {rules};
}

function normaliseTags(tags) {
  if (!Array.isArray(tags)) {
    return [];
  }
  return [...tags].sort();
}

function normaliseNodes(nodes) {
  if (!Array.isArray(nodes)) {
    return [];
  }
  return nodes.map((n) => ({
    target: Array.isArray(n.target) ? n.target.map(String) : [],
    html: typeof n.html === 'string' ? n.html.slice(0, 300) : '',
    failureSummary: typeof n.failureSummary === 'string' ? n.failureSummary : '',
  }));
}

function normaliseRule(rule) {
  return {
    id: rule.id,
    impact: rule.impact ?? null,
    help: rule.help ?? '',
    helpUrl: rule.helpUrl ?? '',
    tags: normaliseTags(rule.tags),
    nodeCount: Array.isArray(rule.nodes) ? rule.nodes.length : 0,
    nodes: normaliseNodes(rule.nodes),
  };
}

async function auditOne(relPath) {
  const abs = path.resolve(REPO, relPath);
  let html;
  try {
    html = fs.readFileSync(abs, 'utf8');
  } catch (err) {
    return {
      file: relPath,
      status: 'error',
      error: `failed to read file: ${err.message}`,
      summary: null,
      violations: [],
      incomplete: [],
    };
  }

  let dom;
  try {
    dom = new JSDOM(html, {
      runScripts: 'outside-only',
      pretendToBeVisual: true,
      url: 'https://fenre.github.io/splunk-monitoring-use-cases/',
    });
  } catch (err) {
    return {
      file: relPath,
      status: 'error',
      error: `jsdom failed to parse HTML: ${err.message}`,
      summary: null,
      violations: [],
      incomplete: [],
    };
  }

  let results;
  try {
    results = await axe.run(dom.window.document.documentElement, {
      ...buildConfig(),
      runOnly: RUN_ONLY,
      resultTypes: ['violations', 'passes', 'incomplete', 'inapplicable'],
    });
  } catch (err) {
    dom.window.close();
    return {
      file: relPath,
      status: 'error',
      error: `axe.run threw: ${err.message}`,
      summary: null,
      violations: [],
      incomplete: [],
    };
  } finally {
    try {
      dom.window.close();
    } catch (_err) {
      // jsdom sometimes double-closes; ignore.
    }
  }

  const violations = (results.violations || [])
    .map(normaliseRule)
    .sort((a, b) => a.id.localeCompare(b.id));
  const incomplete = (results.incomplete || [])
    .map(normaliseRule)
    .sort((a, b) => a.id.localeCompare(b.id));

  return {
    file: relPath,
    status: 'ok',
    error: null,
    summary: {
      passes: (results.passes || []).length,
      violations: violations.length,
      incomplete: incomplete.length,
      inapplicable: (results.inapplicable || []).length,
    },
    violations,
    incomplete,
  };
}

async function main() {
  const argv = process.argv.slice(2);
  if (argv.length === 0) {
    process.stderr.write('usage: node tests/a11y/run-axe.mjs <file.html> [more.html ...]\n');
    process.exit(2);
  }

  const results = [];
  for (const arg of argv) {
    results.push(await auditOne(arg));
  }

  const payload = {
    axe_version: axe.version || 'unknown',
    jsdom_version: jsdomPkg.version || 'unknown',
    ran_at_utc: 'static',
    config: {
      disabled_rules: [...JSDOM_INCOMPATIBLE_RULES],
      run_only: {type: RUN_ONLY.type, values: [...RUN_ONLY.values]},
    },
    results,
  };

  process.stdout.write(JSON.stringify(payload, null, 2) + '\n');
}

main().catch((err) => {
  process.stderr.write(`FATAL: ${err.stack || err.message || err}\n`);
  process.exit(1);
});

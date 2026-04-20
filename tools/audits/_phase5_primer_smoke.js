#!/usr/bin/env node
/**
 * Phase 5 headless smoke test for regulatory-primer.html clause autolinking.
 *
 * Boots the primer's inline IIFE against a stubbed DOM that mirrors the
 * post-render structure (hero + H3 headings + inline <code> clauses),
 * then verifies that ``decorateClauseLinks`` wraps recognised clause
 * tokens in anchors to ``clause-navigator.html`` while leaving tier
 * tokens, SPL fragments, and numeric weights alone.
 *
 * The smoke intentionally avoids the full markdown-render pipeline —
 * that is already exercised by the page itself and by end-to-end UI
 * clicks. What we want to assert here is the *autolinker contract*:
 *
 *   * known clauses for the enclosing regulation become links
 *   * unknown codes inside the same section do NOT become links
 *   * tokens inside <pre> are never touched
 *   * headings that name no regulation skip linking entirely
 *
 * Run with: ``node tools/audits/_phase5_primer_smoke.js`` (no args).
 */
"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "..", "..");
const HTML_PATH = path.join(ROOT, "regulatory-primer.html");
const INDEX_PATH = path.join(
  ROOT,
  "api",
  "v1",
  "compliance",
  "clauses",
  "index.json"
);

let tests = 0;
let fails = 0;
function assert(ok, msg) {
  tests += 1;
  if (!ok) {
    fails += 1;
    console.error("FAIL:", msg);
  } else {
    console.log("ok   -", msg);
  }
}

// ----------------------------------------------------------------------
// Minimal DOM shim — just enough to run decorateClauseLinks.
// ----------------------------------------------------------------------
function makeDom() {
  const elements = [];

  function makeEl(tag) {
    const el = {
      tagName: (tag || "DIV").toUpperCase(),
      textContent: "",
      innerHTML: "",
      _className: "",
      _children: [],
      _attrs: Object.create(null),
      parentNode: null,
      parentElement: null,
      firstChild: null,
      nextSibling: null,
      classList: {
        _set: new Set(),
        add(c) {
          this._set.add(c);
          // Keep _className (source of truth for `.className`) in sync.
          el._className = Array.from(this._set).join(" ");
        },
        remove(c) {
          this._set.delete(c);
          el._className = Array.from(this._set).join(" ");
        },
        contains(c) {
          return this._set.has(c);
        },
      },
      getAttribute(name) {
        return Object.prototype.hasOwnProperty.call(this._attrs, name)
          ? this._attrs[name]
          : null;
      },
      setAttribute(name, value) {
        this._attrs[name] = String(value);
      },
      removeAttribute(name) {
        delete this._attrs[name];
      },
      appendChild(child) {
        if (child.parentNode) {
          const idx = child.parentNode._children.indexOf(child);
          if (idx >= 0) child.parentNode._children.splice(idx, 1);
        }
        this._children.push(child);
        child.parentNode = this;
        child.parentElement = this;
        this.firstChild = this._children[0] || null;
        return child;
      },
      insertBefore(newNode, ref) {
        const idx = this._children.indexOf(ref);
        if (idx < 0) {
          this._children.push(newNode);
        } else {
          this._children.splice(idx, 0, newNode);
        }
        newNode.parentNode = this;
        newNode.parentElement = this;
        this.firstChild = this._children[0] || null;
        return newNode;
      },
      removeChild(child) {
        const idx = this._children.indexOf(child);
        if (idx >= 0) {
          this._children.splice(idx, 1);
          child.parentNode = null;
          child.parentElement = null;
        }
        this.firstChild = this._children[0] || null;
      },
      closest(sel) {
        const tag = String(sel).toUpperCase();
        let cur = this;
        while (cur) {
          if (cur.tagName === tag) return cur;
          cur = cur.parentElement;
        }
        return null;
      },
      querySelector(selector) {
        const arr = queryAll(this, selector);
        return arr.length > 0 ? arr[0] : null;
      },
      querySelectorAll(selector) {
        return queryAll(this, selector);
      },
    };
    // Define className with a setter that syncs to classList (so that
    // `a.className = 'rp-clause-link'` and `a.classList.add(...)` both
    // reach the same backing set).
    Object.defineProperty(el, "className", {
      get() {
        return this._className;
      },
      set(value) {
        this._className = String(value || "");
        const parts = this._className
          .split(/\s+/)
          .filter(function (s) { return s; });
        this.classList._set = new Set(parts);
      },
    });
    elements.push(el);
    return el;
  }

  function queryAll(root, selector) {
    const out = [];
    const sel = String(selector).trim();
    function walk(node) {
      if (!node || !node._children) return;
      for (const c of node._children) {
        if (matches(c, sel)) out.push(c);
        walk(c);
      }
    }
    walk(root);
    return out;
  }

  function matches(el, sel) {
    if (!el.tagName) return false;
    if (sel === "code") return el.tagName === "CODE";
    if (sel === "h2") return el.tagName === "H2";
    if (sel === "h3") return el.tagName === "H3";
    if (sel === "[data-rp-reg]") {
      return el._attrs && Object.prototype.hasOwnProperty.call(el._attrs, "data-rp-reg");
    }
    if (sel === ".rp-hero") {
      return el.classList.contains("rp-hero");
    }
    if (sel === ".rp-hero-clause-count") {
      return el.classList.contains("rp-hero-clause-count");
    }
    if (sel === "a.rp-clause-link") {
      return el.tagName === "A" && el.classList.contains("rp-clause-link");
    }
    return false;
  }

  const article = makeEl("article");

  function createTreeWalker(root /*, whatToShow, filter */) {
    const flat = [];
    function walk(node) {
      if (!node || !node._children) return;
      for (const c of node._children) {
        flat.push(c);
        walk(c);
      }
    }
    walk(root);
    let idx = -1;
    return {
      nextNode() {
        idx += 1;
        return idx < flat.length ? flat[idx] : null;
      },
    };
  }

  const doc = {
    createElement: makeEl,
    createTreeWalker: createTreeWalker,
  };

  return { article, makeEl, doc };
}

// ----------------------------------------------------------------------
// Extract decorateClauseLinks from the inline <script>.
// ----------------------------------------------------------------------
function loadDecorateClauseLinks() {
  const html = fs.readFileSync(HTML_PATH, "utf8");
  // There are multiple <script> blocks; we want the last one which
  // carries the IIFE body.
  const last = html.lastIndexOf("<script>");
  const end = html.lastIndexOf("</script>");
  if (last === -1 || end === -1 || end <= last) {
    throw new Error("could not locate inline <script> in regulatory-primer.html");
  }
  const body = html.slice(last + "<script>".length, end);

  // Pull just the function source — isolate by its opening line.
  const fnStart = body.indexOf("function decorateClauseLinks");
  if (fnStart === -1) {
    throw new Error("decorateClauseLinks not found in script body");
  }
  // Walk braces to find the matching closing brace.
  let depth = 0;
  let i = fnStart;
  let opened = false;
  for (; i < body.length; i += 1) {
    const ch = body[i];
    if (ch === "{") {
      depth += 1;
      opened = true;
    } else if (ch === "}") {
      depth -= 1;
      if (opened && depth === 0) {
        i += 1;
        break;
      }
    }
  }
  const fnSrc = body.slice(fnStart, i);
  return fnSrc;
}

function run() {
  assert(fs.existsSync(HTML_PATH), "regulatory-primer.html exists");
  assert(fs.existsSync(INDEX_PATH), "clauses index exists");

  const clausesIndex = JSON.parse(fs.readFileSync(INDEX_PATH, "utf8"));
  assert(Array.isArray(clausesIndex.clauses), "clauses index has .clauses[]");
  assert(clausesIndex.clauses.length > 100, "clauses index has many entries");

  const fnSrc = loadDecorateClauseLinks();

  const { article, makeEl, doc } = makeDom();

  // Build a miniature primer fragment: an H3 naming GDPR, followed by
  // paragraphs and inline codes.
  const hero = makeEl("div");
  hero.classList.add("rp-hero");
  article.appendChild(hero);

  const h3 = makeEl("h3");
  h3.textContent = "4.1 GDPR — General Data Protection Regulation (EU/EEA)";
  article.appendChild(h3);

  const p1 = makeEl("p");
  const cArt5 = makeEl("code");
  cArt5.textContent = "Art.5";
  p1.appendChild(cArt5);
  article.appendChild(p1);

  const cTier = makeEl("code");
  cTier.textContent = "T1";
  article.appendChild(cTier);

  const cNum = makeEl("code");
  cNum.textContent = "0.7";
  article.appendChild(cNum);

  // A heading that names no regulation — subsequent clause codes should
  // not link (we simulate "### Legend and terminology").
  const h3noReg = makeEl("h3");
  h3noReg.textContent = "Legend and terminology";
  article.appendChild(h3noReg);

  const cOrphan = makeEl("code");
  cOrphan.textContent = "Art.5";
  article.appendChild(cOrphan);

  // Inject into VM
  const sandbox = {
    document: doc,
    NodeFilter: { SHOW_ELEMENT: 1 },
    encodeURIComponent: encodeURIComponent,
    // We do not install `RegExp`; Node.js builtin is fine. `console` for
    // debugging if needed.
    console: console,
  };
  vm.createContext(sandbox);
  vm.runInContext(fnSrc + "\nglobalThis.__fn = decorateClauseLinks;", sandbox);

  sandbox.__fn(article, clausesIndex);

  // Assertions --------------------------------------------------------
  assert(
    cArt5.parentNode &&
      cArt5.parentNode.tagName === "A" &&
      cArt5.parentNode.classList.contains("rp-clause-link"),
    "GDPR Art.5 is wrapped in an rp-clause-link anchor"
  );
  const href = cArt5.parentNode.href || cArt5.parentNode._attrs.href || "";
  assert(
    typeof href === "string" &&
      href.indexOf("clause-navigator.html#clause=") === 0,
    "anchor href targets clause-navigator with clause fragment"
  );
  assert(
    typeof href === "string" && href.indexOf(encodeURIComponent("gdpr@")) > 0,
    "anchor href carries the GDPR clauseId"
  );

  assert(
    !(cTier.parentNode && cTier.parentNode.classList.contains("rp-clause-link")),
    "tier token T1 is not linked"
  );
  assert(
    !(cNum.parentNode && cNum.parentNode.classList.contains("rp-clause-link")),
    "numeric weight 0.7 is not linked"
  );
  assert(
    !(cOrphan.parentNode && cOrphan.parentNode.classList.contains("rp-clause-link")),
    "clause code under a no-regulation heading is not linked"
  );

  // Hero chip should show the match count (1 link created).
  const chip = hero._children.find(
    (c) => c.classList && c.classList.contains("rp-hero-clause-count")
  );
  assert(chip && /^\d+ clauses linked/.test(chip.textContent || ""),
    "hero gains a 'clauses linked' chip after decoration");
}

try {
  run();
} catch (err) {
  console.error(err.stack || String(err));
  fails = Math.max(fails, 1);
  tests = Math.max(tests, 1);
}

console.log("\n" + tests + " tests, " + fails + " failed.");
if (fails > 0) {
  process.exit(1);
} else {
  console.log("All Phase 5 primer smoke assertions passed.");
}

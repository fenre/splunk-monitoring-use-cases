# `src/scripts/` — Source-of-truth JavaScript modules

These five files are the authoritative JavaScript sources for the v7
site's interactive layer. The build pipeline
(`tools/build/render_assets.py`) concatenates them in lexicographic
order, computes a SHA-256 content hash, and emits
`dist/assets/app.<hash>.js`. The HTML rewrite stage swaps the source
`index.html`'s inline `<script>` block for a single
`<script defer src="assets/app.<hash>.js">`.

## File layout

| File             | Lines  | Owns                                                                     |
| ---------------- | -----: | ------------------------------------------------------------------------ |
| `01-state.js`    |   ~165 | SVG icon dictionary, `esc`/`stripMd`/`linkify` helpers, `allUCs`/`ucIndex` build, all top-level state vars |
| `02-filters.js`  |   ~575 | `getFilteredUCs`, `sortUCs`, every `setX` filter handler, advanced filter panel, MITRE dropdown, breadcrumb, filter strip, active-filter chips |
| `03-render.js`   |   ~635 | UC card rendering, sidebar, overview, search results, subcategory view, category view, non-technical viz mockups |
| `04-panel.js`    |   ~285 | Detail panel: `fillPanelBody`, `openPanel`, `closePanel`, `navPanel`, `copyCode`, MITRE map modal |
| `05-app.js`     |  ~1040 | Source catalog, inventory modal, exports, hash routing, non-technical view, theme/a11y, UC selection + DSA, `initApp()` (bootstraps the whole app on load), mobile sidebar |

The numeric prefix (`01-`, `02-`, …) is significant: it defines both
the lexical bundle order and the **execution order**. State must
exist before filters consume it, filters must exist before render
calls them, render must exist before the panel opens, and the panel
must exist before `initApp()` (in `05-app.js`) wires up event
listeners. **Do not reorder.**

## Loading model

* Non-module IIFE-style code (no `import`/`export`, no `type="module"`)
  — every top-level `function` and `var` is a global, just like the
  legacy inline script.
* Loaded via `<script defer src="…">`: the bundle downloads in
  parallel with HTML parsing but executes after the DOM is parsed
  and after the legacy data-layer scripts (`data.js`,
  `non-technical-view.js`, …) have finished. Order with respect to
  those legacy scripts is preserved by source position in
  `dist/index.html`.
* `initApp()` is called at the bottom of `05-app.js`; with `defer`
  this fires before `DOMContentLoaded` but after the document has
  been fully parsed, so every DOM element it queries already exists.

## Editing rules

1. **`src/scripts/` is the source-of-truth** — never edit the inline
   `<script>` block in `index.html` directly. The CI audit
   `tools/audits/asset_drift.py` blocks PRs that desynchronise them.
2. **No `import`/`export`** — until the build pipeline ships an ES
   module bundler, every symbol is a top-level `var` or `function`.
3. **No external runtime dependencies** — zero npm packages, zero
   CDN scripts. The legacy data layer (`data.js`, `provenance.js`,
   `tools/data-sizing/mapping.js`) is loaded via separate
   parser-blocking `<script src="…">` tags in the HTML.
4. **Add new module sections via numeric prefix** — e.g.
   `06-search-shards.js` for the lazy MiniSearch loader landing in
   the next todo. The prefix preserves execution order.

## Adding a new feature

1. Append the new function to the appropriate file (e.g. a new
   render function goes in `03-render.js`; a new modal goes in
   `04-panel.js`).
2. If the feature spans many functions, create `06-<feature>.js`
   with the next free numeric prefix.
3. Run `python3 tools/audits/asset_drift.py --fix` to mirror the
   change into the legacy inline `<script>` block.
4. Run `python3 tools/build/build.py --out dist` and verify
   `dist/index.html` references the new bundle hash and the page
   loads without console errors.

## Lifecycle

* **Now (v7.0):** non-module IIFE, single bundle, single
  `<script defer>` tag.
* **Soon (`catalog-index-lazy` todo):** `01-state.js` stops parsing
  the global `DATA` array and instead lazy-fetches
  `dist/api/catalog-index.json` via the Fetch API. Per-category
  hydration on demand.
* **Soon (`search-shards` todo):** A new `src/scripts/06-search.js`
  replaces the in-memory linear-scan search with a sharded
  MiniSearch index loaded on first keystroke.
* **Future (post-v7):** Migrate to `type="module"` with explicit
  `import`/`export`. The bundle becomes per-route code-split chunks
  emitted by `render_assets.py` instead of one monolithic file.

See `docs/architecture.md` § "Loading model" for the rationale.

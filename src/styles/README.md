# `src/styles/` — Source-of-truth stylesheets

These five CSS files are the authoritative stylesheet sources for the
v7 site. The build pipeline (`tools/build/render_assets.py`)
concatenates them in lexicographic order, computes a SHA-256 content
hash, and emits `dist/assets/styles.<hash>.css`. The HTML rewrite
stage swaps the source `index.html`'s inline `<style>` block for a
`<link rel="preload">` to that fingerprinted bundle.

## File layout

| File                   | Bytes  | Owns                                                        |
| ---------------------- | -----: | ----------------------------------------------------------- |
| `01-tokens.css`        |  ~3 KB | CSS custom properties (`--cisco-blue`, …), dark + colour-blind themes |
| `02-base.css`          |  ~0.5 KB | Reset, body defaults, `:focus-visible`, `<a>`, `<button>`  |
| `03-components.css`    | ~55 KB | All component styles: header, sidebar, cards, panels, modals, tables |
| `04-print.css`         |  ~0.7 KB | `@media print` overrides + non-technical-view modifiers     |
| `05-helpers.css`       |  ~6.5 KB | Release-notes modal, help button/banner, help-tab content   |

The numeric prefix (`01-`, `02-`, …) defines both the source-order in
the bundle and the **critical-CSS partition**: files matching the
prefixes in `tools/build/render_assets.CRITICAL_CSS_PREFIXES`
(currently `("01-", "02-")`) are inlined directly into the HTML
`<head>` so above-the-fold rendering does not block on a network
fetch. The remaining files load via `<link rel="preload">` with an
`onload` handoff to `rel="stylesheet"`, plus a `<noscript>` fallback.

## Editing rules

1. **`src/styles/` is the source-of-truth** — never edit the inline
   `<style>` block in `index.html` directly. The CI audit
   `tools/audits/asset_drift.py` blocks PRs that desynchronise them.
2. **Keep tokens centralised in `01-tokens.css`** — every colour,
   spacing, font, and shadow value lives as a CSS custom property
   here. Components reference them via `var(--…)`.
3. **Hard-fail on circular imports** — these files do not `@import`
   each other. Concatenation order in the bundle is purely lexical.
4. **No build-time CSS preprocessing** — pure CSS only (the v7 build
   ships with zero npm dependencies for content generation).
   Browser-targeting compatibility is covered by the conservative
   feature set we use (CSS Grid, custom properties, modern selectors
   that ship in every browser ≥2 versions back).

## Adding a new component

1. Append the rules to `03-components.css` if they belong to an
   existing component family, or create `06-<feature>.css` with the
   next free numeric prefix.
2. Run `python3 tools/audits/asset_drift.py --fix` to mirror the
   change into the legacy inline `<style>` block (so direct
   `python -m http.server` from repo root keeps working during the
   v7 transition).
3. Run `python3 tools/build/build.py --out dist` and inspect
   `dist/assets/styles.<hash>.css` — the hash will change to reflect
   the new content.

## Lifecycle

The legacy inline `<style>` block in source `index.html` is removed
in the `cleanup-and-docs` todo (post-`render_pages.py` SSG); at that
point `tools/audits/asset_drift.py` is also retired. Until then this
audit is the only thing keeping the two surfaces in sync.

See `docs/architecture.md` § "Asset pipeline" for the rationale.

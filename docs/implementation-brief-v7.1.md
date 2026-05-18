# Implementation Brief: Site Redesign v7.1

> This document captures every design decision from the planning conversation.
> A new agent should read this document first, then the plan file at
> `.cursor/plans/panel_gold-standard_uplift_3c6cbfe5.plan.md`, then begin work.

## Background

This project is a Splunk monitoring use case catalog — a web-based reference
library of **7,364** use cases for Splunk deployments *(this brief originally referred to ~1,400 UCs at the v7.1 planning stage; the catalog has since grown)*. It's hosted on GitHub Pages.
The content lives in JSON files under `content/cat-*/UC-*.json`. A Python build
system (`tools/build/build.py`) generates a static site in `dist/`.

The site recently underwent a quality uplift: 57 NIS2<sup class="ref">[<a href="#ref-1">1</a>]</sup> regulatory use cases were
brought to "gold standard" — detailed implementations, structured known false
positives, multiple references, grandma explanations, and compliance mappings.
The content is now excellent. But the UI doesn't surface it properly.

## The problem we're solving

Users browse the catalog via `index.html`. When they click a UC card, a
**slide-out panel** appears on the right (max 800px wide). This panel:

- Hides the detailed implementation behind a collapsed `<details>` element
- Strips all Markdown formatting from content fields (`esc(stripMd(...))`)
- Never shows the grandma explanation (`uc.ge`) at all
- Doesn't link to the dedicated `/uc/UC-X.Y.Z/` page where content renders properly
- Uses 6 different text-rendering functions inconsistently

Meanwhile, the site has grown to 11 separate HTML files, each with its own
inline CSS, creating inconsistent user experiences.

## What we decided

### 1. Replace the slide-out panel with a master-detail layout

When a UC is selected, the catalog transitions from the card grid to a two-pane
view: condensed UC list on the left (replacing the sidebar), full gold-standard
detail on the right. This is the Stripe/Apple/MDN pattern for reference sites.

**Key decisions:**
- The sidebar collapses when detail view opens; the condensed list takes its place
- `history.pushState` (not `replaceState`) so back/forward works between UCs
- Changing a filter while in detail view updates the list; if the selected UC is filtered out, close the detail
- On mobile (<768px), clicking a card navigates directly to `/uc/UC-X.Y.Z/`
- Bronze/stub UCs get a "help improve this on GitHub" callout instead of empty whitespace

### 2. Consolidate to one rendering function

There are currently 6 text-to-HTML functions: `esc()`, `stripMd()`, `linkify()`,
`linkifyRefs()`, `renderDetailBody()`, plus badge helpers. We add `renderMd()`
as THE standard for all rich content fields and remove `renderDetailBody()` and
`linkifyRefs()`.

`renderMd()` is tightly scoped to Markdown patterns that actually appear in our
content: bold, code, links, lists, headings, code fences, paragraphs. No tables,
images, blockquotes, or nested lists.

### 3. Delete .md companion files

**Status: ✅ DONE 2026-05-18 (F21 close)**

The `content/cat-*/UC-*.md` files were generated from JSON by
`python3 -m splunk_uc generate-md-from-json`. They were NOT read by the build — the build
reads JSON directly. They caused a staleness bug where the panel showed garbage
because the `.md` was stale while the JSON was gold-standard. All 7,929 companion
`.md` files were deleted from `content/` and the generator was retired (`src/splunk_uc/generators/md_from_json.py`
remains as a deprecation stub). The LLM-friendly markdown twin is now rendered
at build time only by `tools/build/templates/uc.py::render_markdown_twin` into
`dist/uc/UC-X.Y.Z/uc.md`. See [`docs/health-check-2026-progress.md`](health-check-2026-progress.md)
F21 row.

### 4. Add a list/grid toggle

A toggle button near the filter bar lets users switch between the existing card
grid and a compact one-line-per-UC list view. Both click through to the same
master-detail detail pane. The toggle state persists to localStorage.

### 5. Simplify the header to two destinations

Replace the 6-link audience navigation (`Catalogue / Clause navigator /
Compliance story / Primer / Scorecard / Docs`) with a clean two-link header:
`Catalog / Documentation`.

### 6. Consolidate documentation pages

All supplementary pages (clause-navigator, compliance-story, scorecard,
regulatory-primer, guides) gather under a unified documentation section with
shared design, accessible from `docs.html`. The standalone HTML files redirect
or are replaced.

### 7. Delete dead code

- `index2.html` — unlinked "journey view" experiment
- Old panel overlay HTML, CSS, and JS

### 8. Version bump

Minor version bump (→ 7.1) after implementation. Major bump reserved for when
all **~7,364** UCs reach gold standard *(planning doc originally said ~1,400)*.

## Architecture

### Data flow (unchanged)

```
UC JSON files (source of truth)
    ↓ tools/build/build.py
    ├── api/catalog-index.json (lightweight stubs, ~750KB gzipped)
    ├── api/cat-N.json (heavy fields per category, lazy-loaded)
    ├── dist/uc/UC-X.Y.Z/index.html (static detail pages)
    └── dist/index.html (SPA catalog)
```

The SPA loads `catalog-index.json` on init, then lazy-fetches `cat-N.json`
when a user opens a UC detail (`__ensureFullUC()`). This architecture is
unchanged.

### Layout states

**Browse mode** (default):
```
┌─────────────────────────────────────────────┐
│ Header: [Catalog] [Documentation]           │
├──────────┬──────────────────────────────────┤
│ Sidebar  │ [Grid/List toggle]              │
│ (cats)   │ Card grid  OR  Compact list     │
│          │ ┌───┐ ┌───┐    UC-1.1.1  Title  │
│          │ │   │ │   │    UC-1.1.2  Title  │
│          │ └───┘ └───┘    UC-1.1.3  Title  │
└──────────┴──────────────────────────────────┘
```

**Detail mode** (UC selected, `body.detail-open`):
```
┌─────────────────────────────────────────────┐
│ Header: [Catalog] [Documentation]           │
├──────────────┬──────────────────────────────┤
│ Condensed    │ Full Detail Pane             │
│ UC List      │                              │
│ (replaces    │ UC-22.2.48 · Title           │
│  sidebar)    │ Value: ...                   │
│              │ In plain language: ...        │
│ • UC-22.2.1  │ Quick facts: ...             │
│ ■ UC-22.2.48 │ SPL: ...                     │
│ • UC-22.2.49 │ Detailed walkthrough: ...    │
│              │ Known false positives: ...   │
│ [Back to     │ References: ...              │
│  catalog]    │ [Open full page →]           │
└──────────────┴──────────────────────────────┘
```

**Mobile (<768px)**: No split. Card click → `/uc/UC-X.Y.Z/`.

## File-by-file change map

### Files to delete
- `index2.html`
- ~~`content/cat-*/UC-*.md`~~ ✅ Deleted 2026-05-18 (F21 close; 7,929 files removed).
- ~~`python3 -m splunk_uc generate-md-from-json`~~ ✅ Retired 2026-05-18.
  Verb removed from `splunk_uc/_registry.py`; the
  `src/splunk_uc/generators/md_from_json.py` module remains as a
  deprecation stub (prints retirement notice and exits non-zero).

### Files to modify

| File | Changes |
|------|---------|
| `src/scripts/01-state.js` | Remove `linkifyRefs()` |
| `src/scripts/02-filters.js` | Add `renderMd()`, remove `renderDetailBody()` |
| `src/scripts/03-render.js` | Add `renderCondensedList()`, add list/grid toggle rendering |
| `src/scripts/04-panel.js` | Replace `fillPanelBody/openPanel/closePanel/navPanel` with `fillDetailPane/openDetail/closeDetail` + pushState navigation |
| `src/styles/03-components.css` | Remove `.c-panel-*` overlay CSS, add master-detail grid, condensed list, detail pane, callout styles |
| `index.html` | Replace `#panel-backdrop` with `#detail-list` + `#detail-pane`, simplify header nav to 2 links, add list/grid toggle button |
| `docs.html` | Expand into documentation hub with sub-navigation |
| `clause-navigator.html` | Redirect to docs hub or integrate |
| `compliance-story.html` | Redirect to docs hub or integrate |
| `scorecard.html` | Redirect to docs hub or integrate |
| `regulatory-primer.html` | Redirect to docs hub or integrate |
| `tools/validate/validate_md.py` | Remove `.md` sibling requirement |

### Files unchanged
- `src/scripts/00-loader.js` — lazy-loading architecture stays
- `src/scripts/05-app.js` — app init, non-technical view (deferred)
- `tools/build/build.py` — build pipeline stays
- `tools/build/templates/uc.py` — static `/uc/` pages stay
- All `content/cat-*/UC-*.json` — no data changes
- `api-docs.html` — Swagger, separate purpose
- `tools/data-sizing/index.html` — separate tool

## Implementation order

1. **Delete dead code first** — `index2.html`, `.md` companions, validator update
2. **Add `renderMd()`** — the foundation everything else depends on
3. **Master-detail layout** — CSS grid, HTML containers, `openDetail/closeDetail`
4. **Detail pane renderer** — `fillDetailPane()` with all sections
5. **Condensed list** — `renderCondensedList()` for the left pane
6. **List/grid toggle** — browse mode enhancement
7. **Navigation** — pushState, filter interaction, scroll restoration
8. **Header simplification** — 2-link nav
9. **Docs consolidation** — gather pages under docs hub
10. **HTML cleanup** — remove old panel DOM
11. **Version bump**
12. **Rebuild and deploy**

## Design decisions log

| Decision | Rationale |
|----------|-----------|
| Master-detail over enhanced panel | Panel is too narrow for gold-standard content. Master-detail is the reference-site standard. |
| Sidebar collapses in detail mode | The condensed list replaces the sidebar's function (navigation). Two left columns would be confusing. |
| pushState not replaceState | Users expect back/forward to navigate between UCs. |
| Filter change closes detail if UC gone | Simplest correct behavior. Avoids showing a UC that's not in the current filter. |
| renderMd() tightly scoped | Our content uses a limited Markdown subset. Supporting everything adds complexity and bugs. |
| Delete .md companions | They caused staleness bugs. JSON is the source of truth. /uc/ pages are the readable version. |
| Two-destination header | 6 links fragments the audience. The site has two purposes: browse UCs (Catalog) and read about regulations/guides (Documentation). |
| List/grid toggle | Power users want compact scanning. Cards are fine for visual browsing. Both click to the same detail. |
| Mobile redirects to /uc/ | The static pages are responsive and gold-standard. No need for a compromised mobile detail pane. |
| Thin-content callout | Bronze/stub UCs will look empty in the detail pane. A callout is honest and invites contribution. |
| Minor version bump | Major version reserved for when all UCs reach gold standard. |

## Glossary

- **UC**: Use case (e.g., UC-22.2.48)
- **Gold standard**: UC-1.1.1 quality — detailed implementation (5-step structure), named KFPs, real SPL, named TAs with Splunkbase<sup class="ref">[<a href="#ref-3">3</a>]</sup> IDs, ≥4 references
- **Grandma explanation** (`ge`): Plain-language "what does this do?" text for non-technical audiences
- **Companion .md**: Generated Markdown mirror of a UC JSON file (being deleted)
- **Catalog-index stub**: Lightweight UC record in `catalog-index.json` (no heavy fields)
- **Heavy fields**: `q`, `m`, `md`, `kfp`, `refs`, `script`, `qs`, `z`, `sver`, `reqf` — lazy-loaded from `cat-N.json`
- **Detail mode**: Master-detail layout when a UC is selected
- **Browse mode**: Card grid (or list) when no UC is selected

---

<!-- BEGIN-AUTOGENERATED-SOURCES -->

## References

*Auto-generated by `scripts/generate_doc_references.py` from `data/source-references.json` and `data/source-mappings.json`. Edit those files (or the document body) to change citations; this footer is rewritten on every run.*

### Supporting sources

<a id="ref-1"></a>**[1]** European Parliament and Council of the European Union. (2022, December). *Directive (EU) 2022/2555 — NIS2 Directive on cybersecurity*. Official Journal of the European Union, L 333. ELI: dir/2022/2555. https://eur-lex.europa.eu/eli/dir/2022/2555/oj

<a id="ref-2"></a>**[2]** Splunk Inc. (2026). *Search Reference: SPL Commands and Functions*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://docs.splunk.com/Documentation/Splunk/latest/SearchReference/WhatsInThisManual

<a id="ref-3"></a>**[3]** Splunk Inc. (2026). *Splunkbase — the Splunk app marketplace*. Splunk LLC, a Cisco company. Retrieved May 11, 2026, from https://splunkbase.splunk.com/

<!-- END-AUTOGENERATED-SOURCES -->

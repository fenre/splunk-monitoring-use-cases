# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [2.1.0] - 2026-03-21

UI polish, non-technical view redesign, and navigation improvements.

### Added

- **Tab-based content navigation** — Categories, Subcategories, Use Cases, and Quick Wins as tabs with integrated sort control.
- **Interactive hero domain chips** — front-page domain buttons now filter the category grid and expand the relevant sidebar group.
- **Hero domain icons** — replaced colored dots with monochrome SVG icons (server, shield, cloud, gear, clipboard).
- **Non-technical view redesign** — animated hero with gradient accent and badge, staggered card fade-ins, numbered area indicators in category detail, styled modal sections with green headings.
- **Release notes popup** — full project history accessible from the page footer.
- **Unified sidebar** — both technical and non-technical modes share the same grouped sidebar with collapsible sections, counts, and subcategory drill-down.

### Changed

- **Filter strip** — removed inline "Pillar" and "Criticality" labels; chips are self-explanatory with criticality color dots inline.
- **Category icons in sidebar** — replaced colored dots with per-category SVG icons to avoid confusion with criticality colors.
- **Smart sidebar folding** — non-active groups auto-fold on navigation; manual expand/collapse preserved until category changes.
- **Sort control** moved from filter strip to the tab bar line.
- **Non-technical category detail** — added back-to-overview button, gradient header accent, focus-area/check counts, and outcomes in header.

### Fixed

- Missing `filterByRegulation` function causing runtime errors.
- Previous/Next modal navigation not updating URL hash.
- `clearAllFilters` not resetting overview group filter.
- `restoreFromHash` not clearing hero domain filter state.
- Double history entries from `filterOvGroup`.
- Clipboard copy with no error handling.
- `scrollToSubcat` not updating URL hash.
- Removed dead functions (`getStarters`, `getStartersFromFiltered`, `toggleOvSPL`) and ~120 lines of unused CSS.
- Accessibility gaps — added ARIA roles, keyboard handlers, and focus management to interactive elements.
- Stale counts in README, CHANGELOG, and source-catalog.md.

---

## [2.0.0] - 2026-03-20

Major UI redesign and content expansion.

### Added

- **Category 21 — Industry Verticals**: 119 use cases for energy/utilities, manufacturing, healthcare, telecom, retail, financial services, transportation, government, education, and insurance.
- **Category 22 — Regulatory & Compliance Frameworks**: 30 use cases across GDPR, NIS2, DORA, CCPA, MiFID II, ISO 27001, NIST CSF, and SOC 2 — promoted to a standalone category for discoverability and customer importance.
- **Unified filter strip** replacing scattered filter blocks — pillar, criticality, difficulty, regulation, industry, monitoring type, and sort in one horizontal bar.
- **Active filter tags** row showing applied filters with inline clear buttons.
- **Grouped sidebar** with 5 collapsible sections (Infrastructure, Security, Cloud, Applications, Regulatory & Compliance) using color-coded headers.
- **Deep linking** via hash-based URL routing — shareable links to `#cat-N`, `#uc-N.N.N`, and `#search=term` with full pushState/popstate support.
- **Virtual scrolling** using IntersectionObserver for performant rendering of all 4,625+ use cases.
- **Sort controls** (criticality, difficulty, name, category) with localStorage persistence.
- **Keyboard shortcuts**: Cmd/Ctrl+K and `/` to focus search, Escape to close modals/sidebar.
- **Print stylesheet** (`@media print`) hiding navigation and decorative elements for clean output.
- **Mobile off-canvas sidebar** with backdrop, 44px touch targets, safe-area insets, and dynamic viewport height.
- **AI-friendly metadata**: Open Graph, Twitter Card, updated JSON-LD, `sitemap.xml`, and enhanced `robots.txt`.
- **Semantic HTML** landmarks (`<nav>`, `<section>`, `<article>`) for improved accessibility.
- `llms.txt` and `llms-full.txt` for LLM-readable site content.

### Changed

- Total use case count increased from 3,473 to **4,625** across **22** categories (up from 20).
- **Light-mode visual overhaul**: subtle gradient backgrounds, ambient orbs, card shadows, stronger tag contrast (WCAG AA), and category-group accent colors.
- **Front page redesign**: display-only stats, streamlined view chips (8 → 4), roadmap moved below content, category cards now navigate directly.
- `renderOverview()`, `renderCategory()`, and `renderSearchResults()` rewritten to use `filterStrip()` and `activeFilterTags()`.
- All 7 filter types consolidated into `getFilteredUCs()` for consistent application across views.
- Regulatory use cases (21.11) rewritten with concrete Splunk TAs, sourcetypes, and deployable SPL.

### Removed

- Deprecated functions: `filterBtns()`, `getMtypeFilterBtns()`, `toggleOvCat()`, `filterByDifficulty()`, `filterByPillar()`, `filterByRegulation()`.
- Inline difficulty legend and separate pillar/regulation filter blocks on the overview page.

---

## [1.0.0] - 2026-03-16

First public release of the Splunk Infrastructure Monitoring Use Case Repository.

### Added

- **3,000+ use cases** across 20 IT infrastructure categories, each with criticality, difficulty, SPL queries, CIM mappings, implementation guidance, and visualization recommendations.
- **Interactive single-page dashboard** (`index.html`) with search, filtering by category/equipment/criticality, non-technical view, and expandable details.
- **Build pipeline** (`build.py`) that compiles use case markdown into `data.js` and `catalog.json`.
- **Validation script** (`validate_md.py`) for structure and UC-ID consistency checks.
- **Machine-readable catalog** (`catalog.json`) for scripting and external integrations.
- **Equipment filter** with 30+ technology vendors/platforms and model-level drill-down.
- **Non-technical view** (`non-technical-view.js`) with plain-language outcomes per category.
- **Customizable site text** (`custom-text.js`) for hero, roadmap, and UI labels.
- **GitHub Pages deployment** via included GitHub Actions workflow.
- **Documentation** covering use case fields, implementation guide, CIM/DMA/OCSF reference, equipment table, catalog schema, and hosting setup.
- **SSE-aligned fields** (MITRE ATT&CK, detection type, known false positives, security domain) for security use cases.
- **CIM SPL** (tstats/datamodel queries) for use cases with CIM data model support.

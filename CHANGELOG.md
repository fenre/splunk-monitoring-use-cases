# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [2.0.0] - 2026-03-20

Major UI redesign and content expansion.

### Added

- **Category 21 — Industry Verticals**: 310+ use cases for energy/utilities, manufacturing, healthcare, telecom, retail, financial services, transportation, government, education, media, and regulatory compliance (GDPR, NIS2, DORA, CCPA, MiFID II, ISO 27001, NIST CSF, SOC 2).
- **Unified filter strip** replacing scattered filter blocks — pillar, criticality, difficulty, regulation, industry, monitoring type, and sort in one horizontal bar.
- **Active filter tags** row showing applied filters with inline clear buttons.
- **Grouped sidebar** with 4 collapsible sections (Infrastructure, Security, Cloud, Applications) using color-coded headers.
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

- Total use case count increased from 3,473 to **4,625** across **21** categories (up from 20).
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

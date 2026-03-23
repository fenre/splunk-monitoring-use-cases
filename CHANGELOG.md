# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [3.1] - 2026-03-23

### Added

- **Archived Splunkbase app visibility** — Use cases referencing archived apps now display an amber "Archived App" badge on cards and a warning box in the modal with successor app recommendation. Palo Alto Networks App (491) newly flagged as archived with successor Splunk App for Palo Alto Networks (7505). Unix and Windows app entries now include successor links to IT Essentials Work (5403).
- **Advanced Filters panel** — Collapsible "Advanced Filters" below the existing filter strip with 8 new filters: ES Detection (toggle), Detection type (dropdown), Premium Apps (dropdown), CIM Data Model (dropdown), App/TA (dropdown), Industry (dropdown), MITRE ATT&CK (searchable text), Data source (searchable text). All filters show as removable chips and update sidebar counts.
- **FILTER_FACETS in data.js** — Pre-extracted unique sorted values for each advanced filter dimension, generated at build time to avoid client-side scanning of 4,600+ use cases.
- **Non-technical view rewrite** — All 22 categories rewritten with 120 monitoring areas and 360 representative UC references. Build-time validation via `validate_non_technical()` ensures UC IDs stay in sync.
- **Sources reference popup** — Footer button opens a catalog of all documentation, apps, frameworks, and community resources used to research and build the use cases — Splunk Lantern, ESCU, MITRE ATT&CK, vendor docs, and regulatory frameworks.
- **SD-WAN use case expansion** — Subcategory 5.5 expanded from 10 to 20 dedicated SD-WAN use cases. New coverage includes OMP route monitoring, BFD session tracking, edge device resource utilization, firmware compliance, DPI application visibility, Cloud OnRamp performance, UTD security policy violations, vManage cluster health, transport circuit SLA tracking, and overlay topology validation. Two misplaced wireless use cases relocated to 5.4.

---

## [3.0] - 2026-03-22

### Added

- **Enterprise Security detection badges** — 2,070 ESCU detection rules now display a teal “ES Detection” badge on UC cards and modals. Risk-Based Alerting detections show “ES Detection — Risk-Based Alerting”. Badges are searchable via “escu”, “es detection”, “rba”.
- **ESCU-specific implementation guidance** — build.py classifies ESCU detections by methodology (TTP, Hunting, Anomaly, Baseline, Correlation) and RBA status, then generates tailored implementation text covering ES Content Management deployment, risk score tuning, analyst response workflows per security domain, and SPL context for Risk Investigation drilldown searches. Replaces the previous generic “Deploy the detection from ESCU” boilerplate on 1,500+ use cases.

### Changed

- **Catalog Dashboard Studio (`catalog-quick-start-top2.json`)** — **44** separate chart objects only (one `splunk.*` visualization per use case). Each panel uses Dashboard Studio **title** and **description** for UC id + name + category — no stacked markdown “label rows” or category bands that read like a table. **3** page markdown blocks (title/subtitle/DEMO) + time picker. Regenerate with **`scripts/generate_catalog_dashboard.py`**.
- **SPL quality: join max=1** — Added explicit max=1 to 88 join statements across all category files to prevent silent data truncation.
- **Text quality improvements** — Revised Value, Implementation, and Visualization fields for 30 use cases across 17 category files, replacing generic descriptions with specific, actionable guidance tailored to each use case context.
- **Markdown fixes** — Corrected duplicate sourcetypes and broken backticks in cat-05-network-infrastructure.md.

---

## [2.1.12] - 2026-03-21

### Added

- **REST deploy for Dashboard Studio** — New **`scripts/deploy_dashboard_studio_rest.py`**: wraps the Studio JSON in the XML envelope required by Splunk’s **`data/ui/views`** API and **POST**s it (create, then update if the dashboard already exists). Documented in **`dashboards/README.md`** with `SPLUNK_TOKEN` or basic auth, app/owner/host options, and links to Splunk Docs.

---

## [2.1.11] - 2026-03-21

### Added

- **Dashboard Studio — Catalog Quick-Start Portfolio** — New **`dashboards/catalog-quick-start-top2.json`**: professional dark-theme Dashboard Studio layout with KPIs, category event bar chart, 24h trend, and a detail table for the **44** use cases (**top two** per category from **`use-cases/INDEX.md`** Quick Start). All data is **synthetic** (`makeresults` / `eval`). **`dashboards/README.md`** documents import into Splunk Enterprise/Cloud; **`scripts/generate_catalog_dashboard.py`** regenerates the JSON when Quick Start picks change.

---

## [2.1.10] - 2026-03-21

### Changed

- **Industry Verticals (category 21)** — **Implementation** sections for aviation, telecommunications, water/wastewater, and insurance use cases now include **Domain context** (standards, regulatory, and operational notes) and **Splunk** guidance (field normalization, thresholds, time scope, and index/sourcetype caveats). Rebuild with `python3 build.py`.

---

## [2.1.9] - 2026-03-21

### Changed

- **Detailed implementation — SPL walkthrough** — Auto-generated “Understanding this SPL” text is now **use-case–aware**: it pulls **title**, **value**, **Data sources**, and **App/TA**, cross-checks the **first search stage** against documented sourcetypes, and adds a **Pipeline walkthrough** with richer command lines (e.g. `by`/`span` for `stats`/`timechart`, first `eval` target field, `where` condition text). CIM variants use a dedicated heading and CIM-specific intro. Implemented in `build.py` (`explain_spl_pipeline`, `_spl_explain_intro`); rebuild with `python3 build.py`.

---

## [2.1.8] - 2026-03-21

### Changed

- **Industry Verticals as its own domain group** — Category 21 is no longer grouped under Applications in `CAT_GROUPS`. The overview hero chips, sidebar, and catalog now use a dedicated **`industry`** group (with **`factory`** icon on the hero) so vertical use cases are visible next to Infrastructure, Security, Cloud, Applications, and Regulatory & Compliance.

---

## [2.1.7] - 2026-03-21

### Changed

- **CIM-style field names** — Normalized `src_ip`/`dest_ip`/`source_ip` to **`src`** / **`dest`** across use-case SPL where appropriate; data model clauses use **`All_Traffic.src`** / **`All_Traffic.dest`** (not `*_ip`). GCP VPC flows use `eval`/`coalesce` from `connection.*`; Azure Firewall threat intel uses `rename` to `src`/`dest`; Carbon Black netconn uses `rename` to `dest`/`dest_port`; SNMP example uses `eval user=coalesce(user, user_name)`. Added `scripts/normalize_cim_fields.py` and a short **Preferred CIM-style field names** table in `docs/cim-and-data-models.md`.

---

## [2.1.6] - 2026-03-21

### Fixed

- **SPL review follow-up** — Applied remaining actionable items from `spl-review-findings.md`: `mvexpand … limit=N` on high-cardinality expands (cloud, Entra, GitHub, Docker); `join type=left max=0` on Webex workspace join; top-N `sort <N> -count` instead of `sort -count` + `head` in several NGFW/IDS/Web examples; AWS IoT provisioning data sources documented to prefer `aws:cloudtrail` + `eventSource` filters; RD Gateway note for XmlWinEventLog vs WinEventLog. See remediation note at top of `spl-review-findings.md`.

---

## [2.1.5] - 2026-03-21

### Added

- **Report issue on GitHub** — Technical and non-technical use case modals include a link that opens **New issue** with a pre-filled title/body: UC id, category/subcategory, link to the source markdown on GitHub (`use-cases/<file>`), and the current dashboard URL with `#uc-…` hash. Forks can set `window.SITE_CUSTOM.siteRepoUrl` to point issues at their repo.

---

## [2.1.4] - 2026-03-21

### Added

- **Auto-generated SPL explanations** — Every use case’s generated **Detailed implementation** (`md` in `catalog.json` / **View more detailed instructions** in the UI) now includes an **Understanding this SPL** section: plain-language bullets per pipeline stage (base search, `stats`/`timechart`, `tstats`/datamodel, joins, lookups, etc.). When a **CIM SPL** (`qs`) exists, the guide also embeds that query and a matching walkthrough. Heuristic limits keep very long ESCU-style searches readable.

---

## [2.1.3] - 2026-03-21

### Fixed

- **SPL & CIM catalog pass** — aligned examples with Splunk CIM and TA conventions across multiple categories: `WinEventLog:Security` sourcetype casing (vs. `wineventlog:security`); `Network_Traffic.All_Traffic` aggregates using `bytes_in`/`bytes_out` with `eval` totals (vs. `All_Traffic.bytes` alone); LDAP `tstats` private-range filtering with `cidrmatch()`; explicit `index=windows` (vs. `index=wineventlog`) in compliance samples; FortiGate inventory search scoped to `fortinet:fortigate_system`; SOX ERP vs. AD queries split; `mvexpand` limits; `transaction`/`sort` tuning; ITSI `inputlookup` notes; markdown/Data Source backtick fixes (e.g. Meraki on UC-5.4.9).
- **Additional SPL hygiene** — `cidrmatch()` argument order (IP first, CIDR second); UC-10.13.12 CIM egress example uses `` `drop_dm_object_name("All_Traffic")` `` then `src`/`dest` for RFC1918 tests; **cat-05** closed 100+ broken `` ` `` spans on Meraki Data Sources lines; normalized `| sort -field` (removed erroneous spaces) in Meraki SPL snippets.

---

## [2.1.2] - 2026-03-21

### Fixed

- **ES `notable` macro** — replaced `index=notable` with the Splunk ES `` `notable` `` macro across 15 SPL queries in Category 10 (Security Infrastructure) and Category 22 (Regulatory & Compliance). The macro resolves human-readable status labels, owner fields, and other enrichment that raw index access does not provide.

---

## [2.1.1] - 2026-03-21

AI and LLM discoverability improvements.

### Added

- **Self-describing catalog.json** — `_schema_url` and `_readme` keys at the top level so tools fetching the catalog cold can discover the field schema without a second fetch.
- **Expanded sitemap.xml** — now generated by `build.py` with 33 URLs (was 4), covering all 22 category markdown files, INDEX.md, documentation pages, and AI index files. Stays in sync as categories are added.
- **Cross-referenced llms.txt / llms-full.txt** — each file now points to the other explaining the difference (concise category index vs. full use case listing).

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
